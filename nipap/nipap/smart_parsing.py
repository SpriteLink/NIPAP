#!/usr/bin/python

from itertools import izip_longest
import logging
import re

import IPy

from pyparsing import Combine, Forward, Group, Literal, nestedExpr, OneOrMore, ParseResults, quotedString, Regex, QuotedString, Word, ZeroOrMore, alphanums, nums, oneOf

from errors import *


class SmartParser:
    attributes = {}
    match_operators = ['=', '<', '>', '<=', '>=', '~']
    boolean_operators = ['and', 'or']

    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)


    def _is_ipv4(self, ip):
        """ Return true if given arg is a valid IPv4 address
        """
        try:
            p = IPy.IP(ip)
        except ValueError:
            return False

        if p.version() == 4:
            return True
        return False


    def _is_ipv6(self, ip):
        """ Return true if given arg is a valid IPv6 address
        """
        try:
            p = IPy.IP(ip)
        except ValueError:
            return False

        if p.version() == 6:
            return True
        return False


    def _get_afi(self, ip):
        """ Return address-family (4 or 6) for IP or None if invalid address
        """

        parts = unicode(ip).split("/")
        if len(parts) == 1:
            # just an address
            if self._is_ipv4(ip):
                return 4
            elif self._is_ipv6(ip):
                return 6
            else:
                return None
        elif len(parts) == 2:
            # a prefix!
            try:
                pl = int(parts[1])
            except ValueError:
                # if casting parts[1] to int failes, this is not a prefix..
                return None

            if self._is_ipv4(parts[0]):
                if pl >= 0 and pl <= 32:
                    # prefix mask must be between 0 and 32
                    return 4
                # otherwise error
                return None
            elif self._is_ipv6(parts[0]):
                if pl >= 0 and pl <= 128:
                    # prefix mask must be between 0 and 128
                    return 6
                # otherwise error
                return None
            else:
                return None
        else:
            # more than two parts.. this is neither an address or a prefix
            return None


    def _string_to_ast(self, input_string):
        """ Parse a smart search string and return it in an AST like form
        """

        # simple words
        comp_word = Word(alphanums + "-./_")
        word = Word(alphanums + "-./_").setResultsName('word')
        # numbers
        comp_number = Word(nums)
        number = Word(nums).setResultsName('number')

        # IPv4 address
        ipv4_oct = Regex("((2(5[0-5]|[0-4][0-9])|[01]?[0-9][0-9]?))")
        comp_ipv4_address = Combine(ipv4_oct + ('.' + ipv4_oct*3))
        ipv4_address = Combine(ipv4_oct + ('.' + ipv4_oct*3)).setResultsName('ipv4_address')

        # VRF RTs of the form number:number
        vrf_rt = Combine((comp_ipv4_address | comp_number) + Literal(':') + comp_number).setResultsName('vrf_rt')

        # tags
        tags = Combine( Literal('#') + comp_word).setResultsName('tag')

        # operators for matching
        match_op = oneOf(' '.join(self.match_operators)).setResultsName('operator')
        boolean_op = oneOf(' '.join(self.boolean_operators)).setResultsName('boolean')
        # quoted string
        quoted_string = QuotedString('"', unquoteResults=True, escChar='\\').setResultsName('quoted_string')
        # expression to match a certain value for an attribute
        expression = Group(word + match_op + (quoted_string | vrf_rt | word | number)).setResultsName('expression')
        # we work on atoms, which are single quoted strings, match expressions,
        # tags, VRF RT or simple words.
        # NOTE: Place them in order of most exact match first!
        atom = Group(quoted_string | expression | tags | vrf_rt | boolean_op | word)

        enclosed = Forward()
        parens = nestedExpr('(', ')', content=enclosed)
        enclosed << (
                parens | atom
                ).setResultsName('nested')

        content = Forward()
        content << (
                ZeroOrMore(enclosed)
                )

        res = content.parseString(input_string)
        return res


    def _ast_to_dictsql(self, input_ast):
        """
        """
        # Add implicit AND operator between expressions if there is no explicit
        # operator specified.
        ast = []
        for token, lookahead in izip_longest(input_ast, input_ast[1:]):
            if token.getName() == "boolean":
                # only add boolean operator if it is NOT the last token
                if lookahead is not None:
                    ast.append(token)
                continue
            else:
                # add non-boolean token
                ast.append(token)
                # if next token is boolean, continue so it can be added
                if lookahead is None or lookahead.getName() == "boolean":
                    continue
                # if next token is NOT a boolean, add implicit AND
                ast.append(ParseResults('and', 'boolean'))


        # dictSql stack
        dss = {
                'operator': None,
                'val1': None,
                'val2': None
                }

        dse = None
        for part, lookahead in izip_longest(ast, ast[1:]):
            self._logger.debug("part: %s %s" % (part, part.getName()))

            # handle operators joining together expressions
            if part.getName() == 'boolean':
                op = part[0].lower()
                dss['operator'] = op
                dss['interpretation'] = {
                        'interpretation': op,
                        'operator': op
                        }
                continue

            # string expr that we expand to dictsql expression
            elif part.getName() == 'expression':
                if part.operator in self.match_operators:
                    dse = self._parse_expr(part)
                else:
                    dse = self._ast_to_dictsql(part)
            elif part.getName() == 'nested':
                dse = self._ast_to_dictsql(part)
            elif part.getName() in ('word', 'tag', 'vrf_rt'):
                # dict sql expression
                dse = self._string_to_dictsql(part)
                self._logger.debug('string part: %s  => %s' % (part, dse))
            else:
                raise ParserError("Unhandled part in AST: %s %s" % (part,
                                                                    part.getName()))

            if dss['val1'] is None:
                self._logger.debug('val1 not set, using dse: %s' % str(dse))
                dss['val1'] = dse
            else:
                self._logger.debug("val1 is set, operator is '%s', val2 = dst: %s" % (dss['operator'], str(dse)))
                dss['val2'] = dse

            if lookahead is not None:
                if dss['val1'] is not None and dss['val2'] is not None:
                    dss = {
                            'operator': None,
                            'val1': dss,
                            'val2': None
                        }

        # special handling when AST is only one expression, then we overwrite
        # the dss with dse
        if len(ast) == 1:
            dss = dse
        if len(ast) == 0:
            dss = self._string_to_dictsql(ParseResults('', 'word'))

        # return the final composed stack of dictsql expressions
        return dss


    def _string_to_dictsql(self, string):
        """ Do magic matching of single words or quoted string
        """
        raise NotImplemented()


    def _parse_expr(self, part):
        """ Parse matching expression in form key <op> value

            For example;
                vlan > 1
                node = FOO-BAR
        """
        self._logger.debug("parsing expression: " + str(part))
        key, op, val = part

        if key not in self.attributes:
            raise NotImplementedError()

        dictsql = {
                'operator': op,
                'val1': key,
                'val2': str(val),
                'interpretation': {
                    'string': key + op + val,
                    'interpretation': 'expression',
                    'attribute': key,
                    'operator': op
                }
            }

        return dictsql



    def parse(self, input_string):
        # check for unclosed quotes/parentheses
        paired_exprs = nestedExpr('(', ')') | quotedString
        stripped_line = paired_exprs.suppress().transformString(input_string)
        if '"' in stripped_line:
            raise NipapValueError('Unclosed quote')
        # TODO: add test case for this
        if '(' in stripped_line or ')' in stripped_line:
            raise NipapValueError('Unclosed parentheses')

        ast = self._string_to_ast(input_string)
        return self._ast_to_dictsql(ast)





class PoolSmartParser(SmartParser):
    attributes = {
        'default_type': True,
        'description': True,
        'free_addresses_v4': True,
        'free_addresses_v6': True,
        'free_prefixes_v4': True,
        'free_prefixes_v6': True,
        'ipv4_default_prefix_length': True,
        'ipv6_default_prefix_length': True,
        'member_prefixes_v4': True,
        'member_prefixes_v6': True,
        'name': True,
        'total_addresses_v4': True,
        'total_addresses_v6': True,
        'total_prefixes_v4': True,
        'total_prefixes_v6': True,
        'used_addresses_v4': True,
        'used_addresses_v6': True,
        'used_prefixes_v4': True,
        'used_prefixes_v6': True,
        'vrf': True,
        }


    def _string_to_dictsql(self, part):
        """ Do magic matching of single words or quoted string
        """
        self._logger.debug("parsing string: " + str(part[0]) + " of type: " + part.getName())

        if part.getName() == 'tag':
            self._logger.debug("Query part '" + part[0][0] + "' interpreted as tag")
            dictsql = {
                    'interpretation': {
                        'string': part[0],
                        'interpretation': 'tag',
                        'attribute': 'tag',
                        'operator': 'equals_any',
                        },
                    'operator': 'equals_any',
                    'val1': 'tags',
                    'val2': part[0][1:]
                    }

        elif part.getName() == 'vrf_rt':
            self._logger.debug("Query part '" + part.vrf_rt + "' interpreted as VRF RT")
            # TODO: enable this, our fancy new interpretation
            dictsql = {
                    'interpretation': {
                        'attribute': 'VRF RT',
                        'interpretation': 'vrf_rt',
                        'operator': 'equals',
                        'string': part.vrf_rt
                        },
                    'operator': 'equals',
                    'val1': 'vrf_rt',
                    'val2': part.vrf_rt
                    }
            # using old interpretation for the time being to make sure we align
            # with old smart search interpreter
            dictsql = {
                    'interpretation': {
                        'attribute': 'name or description',
                        'interpretation': 'text',
                        'operator': 'regex',
                        'string': part.vrf_rt
                        },
                    'operator': 'or',
                    'val1': {
                        'operator': 'regex_match',
                        'val1': 'name',
                        'val2': part.vrf_rt
                        },
                    'val2': {
                        'operator': 'regex_match',
                        'val1': 'description',
                        'val2': part.vrf_rt
                        }
                    }

        else:
            self._logger.debug("Query part '" + part[0] + "' interpreted as text")
            dictsql = {
                    'interpretation': {
                        'attribute': 'name or description',
                        'interpretation': 'text',
                        'operator': 'regex',
                        'string': part[0]
                        },
                    'operator': 'or',
                    'val1': {
                        'operator': 'regex_match',
                        'val1': 'name',
                        'val2': part[0]
                        },
                    'val2': {
                        'operator': 'regex_match',
                        'val1': 'description',
                        'val2': part[0]
                        }
                    }

        return dictsql



class PrefixSmartParser(SmartParser):
    attributes = {
        'added': True,
        'alarm_priority': True,
        'authoritative_source': True,
        'children': True,
        'comment': True,
        'country': True,
        'customer_id': True,
        'description': True,
        'display': True,
        'display_prefix': True,
        'expires': True,
        'external_key': True,
        'family': True,
        'free_addreses': True,
        'indent': True,
        'last_modified': True,
        'match': True,
        'monitor': True,
        'node': True,
        'order_id': True,
        'pool': True,
        'prefix': True,
        'status': True,
        'total_addresses': True,
        'type': True,
        'used_addreses': True,
        'vlan': True,
        'vrf': True,
        }

    def _string_to_dictsql(self, part):
        """ Do magic matching of single words or quoted string
        """
        self._logger.debug("parsing string: " + str(part[0]) + " of type: " + part.getName())

        if part.getName() == 'tag':
            self._logger.debug("Query part '" + part[0][0] + "' interpreted as tag")
            dictsql = {
                    'interpretation': {
                        'string': part[0][0],
                        'interpretation': 'tag',
                        'attribute': 'tag',
                        'operator': 'equals_any',
                        },
                    'operator': 'equals_any',
                    'val1': 'tags',
                    'val2': part[0]['word']
                    }

        elif part.getName() == 'ipv4_address':
            dictsql = {}
        elif part.getName() == 'vrf_rt':
            self._logger.debug("Query part '" + part.vrf_rt[0] + "' interpreted as VRF RT")
            # TODO: enable this, our fancy new interpretation
            dictsql = {
                    'interpretation': {
                        'attribute': 'VRF RT',
                        'interpretation': 'vrf_rt',
                        'operator': 'equals',
                        'string': part.vrf_rt[0]
                        },
                    'operator': 'equals',
                    'val1': 'vrf_rt',
                    'val2': part.vrf_rt[0]
                    }
            # using old interpretation for the time being to make sure we align
            # with old smart search interpreter
            dictsql = {
                    'interpretation': {
                        'attribute': 'name or description',
                        'interpretation': 'text',
                        'operator': 'regex',
                        'string': part.vrf_rt[0]
                        },
                    'operator': 'or',
                    'val1': {
                        'operator': 'regex_match',
                        'val1': 'name',
                        'val2': part.vrf_rt[0]
                        },
                    'val2': {
                        'operator': 'regex_match',
                        'val1': 'description',
                        'val2': part.vrf_rt[0]
                        }
                    }

        else:
            # since it's difficult to parse IP addresses using pyparsing we do a
            # bit of good ol parsing here

            if self._get_afi(part[0]) == 4 and len(part[0].split('/')) == 2:
                self._logger.debug("Query part '" + part[0] + "' interpreted as prefix")
                address, prefix_length = part[0].split('/')

                # complete a prefix to it's fully expanded form
                # 10/8 will be expanded into 10.0.0.0/8 which PostgreSQL can
                # parse correctly
                while len(address.split('.')) < 4:
                    address += '.0'

                prefix = address + '/' + prefix_length
                strict_prefix = str(IPy.IP(part[0], make_net = True))

                interp = {
                        'string': part[0],
                        'interpretation': 'IPv4 prefix',
                        'attribute': 'prefix',
                        'operator': 'contained_within_equals',
                    }

                if prefix != part[0]:
                    interp['expanded'] = prefix

                if prefix != strict_prefix:
                    interp['strict_prefix'] = strict_prefix

                dictsql = {
                    'interpretation': interp,
                    'operator': 'contained_within_equals',
                    'val1': 'prefix',
                    'val2': strict_prefix
                }

            # IPv4 address
            # split on dot to make sure we have all four octets before we do a
            # search
            elif self._get_afi(part[0]) == 4 and len(part[0].split('.')) == 4:
                self._logger.debug("Query part '" + part[0] + "' interpreted as prefix")
                dictsql = {
                    'interpretation': {
                        'string': part[0],
                        'interpretation': 'IPv4 address',
                        'attribute': 'prefix',
                        'operator': 'contains_equals',
                    },
                    'operator': 'contains_equals',
                    'val1': 'prefix',
                    'val2': part[0]
                }

            # IPv6 prefix
            elif self._get_afi(part[0]) == 6 and len(part[0].split('/')) == 2:
                self._logger.debug("Query part '" + part[0] + "' interpreted as IPv6 prefix")
                strict_prefix = str(IPy.IP(part[0], make_net = True))
                interp = {
                        'string': part[0],
                        'interpretation': 'IPv6 prefix',
                        'attribute': 'prefix',
                        'operator': 'contained_within_equals'
                    }
                if part[0] != strict_prefix:
                    interp['strict_prefix'] = strict_prefix

                dictsql = {
                    'interpretation': interp,
                    'operator': 'contained_within_equals',
                    'val1': 'prefix',
                    'val2': strict_prefix
                }

            # IPv6 address
            elif self._get_afi(part[0]) == 6:
                self._logger.debug("Query part '" + part[0] + "' interpreted as IPv6 address")
                dictsql = {
                    'interpretation': {
                        'string': part[0],
                        'interpretation': 'IPv6 address',
                        'attribute': 'prefix',
                        'operator': 'contains_equals',
                    },
                    'operator': 'contains_equals',
                    'val1': 'prefix',
                    'val2': part[0]
                }
            else:
                # Description or comment
                self._logger.debug("Query part '" + part[0] + "' interpreted as text")
                dictsql = {
                        'interpretation': {
                            'string': part[0],
                            'interpretation': 'text',
                            'attribute': 'description or comment or node or order_id or customer_id',
                            'operator': 'regex',
                        },
                        'operator': 'or',
                        'val1': {
                            'operator': 'or',
                            'val1': {
                                'operator': 'or',
                                'val1': {
                                    'operator': 'or',
                                    'val1': {
                                        'operator': 'regex_match',
                                        'val1': 'comment',
                                        'val2': part[0]
                                        },
                                    'val2': {
                                        'operator': 'regex_match',
                                        'val1': 'description',
                                        'val2': part[0]
                                        }
                                    },
                                'val2': {
                                    'operator': 'regex_match',
                                    'val1': 'node',
                                    'val2': part[0]
                                    }
                                },
                            'val2': {
                                'operator': 'regex_match',
                                'val1': 'order_id',
                                'val2': part[0]
                                },
                            },
                        'val2': {
                            'operator': 'regex_match',
                            'val1': 'customer_id',
                            'val2': part[0]
                            }
                        }

        return dictsql



class VrfSmartParser(SmartParser):
    attributes = {
        'description': True,
        'free_addresses_v4': True,
        'free_addresses_v6': True,
        'name': True,
        'num_prefixes_v4': True,
        'num_prefixes_v6': True,
        'rt': True,
        'total_addresses_v4': True,
        'total_addresses_v6': True,
        'used_addresses_v4': True,
        'used_addresses_v6': True,
    }

    def _string_to_dictsql(self, part):
        """ Do magic matching of single words or quoted string
        """
        self._logger.debug("parsing string: " + str(part[0]) + " of type: " + part.getName())

        if part.getName() == 'tag':
            self._logger.debug("Query part '" + part[0][0] + "' interpreted as tag")
            dictsql = {
                    'interpretation': {
                        'string': part[0],
                        'interpretation': 'tag',
                        'attribute': 'tag',
                        'operator': 'equals_any',
                        },
                    'operator': 'equals_any',
                    'val1': 'tags',
                    'val2': part[0][1:]
                    }

        elif part.getName() == 'vrf_rt':
            self._logger.debug("Query part '" + part.vrf_rt + "' interpreted as VRF RT")
            # TODO: enable this, our fancy new interpretation
            dictsql = {
                    'interpretation': {
                        'attribute': 'VRF RT',
                        'interpretation': 'vrf_rt',
                        'operator': 'equals',
                        'string': part.vrf_rt
                        },
                    'operator': 'equals',
                    'val1': 'vrf_rt',
                    'val2': part.vrf_rt
                    }
            # using old interpretation for the time being to make sure we align
            # with old smart search interpreter
            dictsql = {
                    'interpretation': {
                        'string': part.vrf_rt,
                        'interpretation': 'text',
                        'attribute': 'vrf or name or description',
                        'operator': 'regex',
                    },
                    'operator': 'or',
                    'val1': {
                        'operator': 'or',
                        'val1': {
                            'operator': 'regex_match',
                            'val1': 'name',
                            'val2': part.vrf_rt
                        },
                        'val2': {
                            'operator': 'regex_match',
                            'val1': 'description',
                            'val2': part.vrf_rt
                        }
                    },
                    'val2': {
                        'operator': 'regex_match',
                        'val1': 'rt',
                        'val2': part.vrf_rt
                    }
                }

        else:
            self._logger.debug("Query part '" + part[0] + "' interpreted as text")
            dictsql = {
                    'interpretation': {
                        'string': part[0],
                        'interpretation': 'text',
                        'attribute': 'vrf or name or description',
                        'operator': 'regex',
                    },
                    'operator': 'or',
                    'val1': {
                        'operator': 'or',
                        'val1': {
                            'operator': 'regex_match',
                            'val1': 'name',
                            'val2': part[0]
                        },
                        'val2': {
                            'operator': 'regex_match',
                            'val1': 'description',
                            'val2': part[0]
                        }
                    },
                    'val2': {
                        'operator': 'regex_match',
                        'val1': 'rt',
                        'val2': part[0]
                    }
                }

        return dictsql



class ParserError(Exception):
    """ General parser error
    """



if __name__ == '__main__':
    # set logging format
    LOG_FORMAT = "%(asctime)s: %(module)-10s %(levelname)-8s %(message)s"
    # setup basic logging
    logging.basicConfig(format=LOG_FORMAT)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    p = VrfSmartParser()
    #dictsql, interpretation = p.parse('core (country=SE or country = NL OR (damp AND "foo bar")')
    #dictsql, interpretation = p.parse('core (country=SE or country = NL OR (damp AND "foo bar"))')
    import sys
    dictsql = p.parse(' '.join(sys.argv[1:]))
    import pprint
    print "----------"
    pp = pprint.PrettyPrinter(indent = 4)
    pp.pprint(dictsql)
    print "----------"
