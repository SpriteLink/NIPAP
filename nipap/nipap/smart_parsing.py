#!/usr/bin/python

from itertools import izip_longest
import logging
from pyparsing import Forward, Group, nestedExpr, ParseResults, QuotedString, Word, ZeroOrMore, alphanums, nums, oneOf

op_text = {
        '=': 'equals',
        '<': 'is less than'
        }

class SmartParser:
    columns = {}
    match_operators = ['=', '<', '>', '<=', '=>', '~']
    boolean_operators = ['and', 'or']

    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)


    def _string_to_ast(self, input_string):
        """ Parse a smart search string and return it in an AST like form
        """

        # simple words
        word = Word(alphanums + "-.")
        # numbers
        number = Word(nums)
        # operators for matching
        match_op = oneOf(' '.join(self.match_operators))
        # quoted string
        quoted_string = QuotedString('"', unquoteResults=True, escChar='\\')
        # expression to match a certain value for an attribute
        expression = Group(word + match_op + (quoted_string | word | number))
        # we work on atoms, which are single words, quoted strings or match expressions
        atom = (quoted_string | expression | word )

        enclosed = Forward()
        parens = nestedExpr('(', ')', content=enclosed)
        enclosed << (
                atom | parens
                )

        content = Forward()
        content << (
                ZeroOrMore(enclosed)
                )

        return content.parseString(input_string)


    def _ast_to_dictsql(self, ast):
        """
        """
        #self._logger.debug("parsing AST: " + str(ast))
        interp = []

        dse = None

        # dictSql stack
        dss = {
                'operator': None,
                'val1': None,
                'val2': None
                }

        for part, lookahead in izip_longest(ast, ast[1:]):
            #self._logger.debug("part: %s %s" % (part, type(part)))
            print "part: %s   lookahead: %s" % (part, lookahead)

            # handle operators joining together expressions
            if isinstance(part, basestring) and part.lower() in self.boolean_operators:
                dss['operator'] = part.lower()
                dss['interpretation'] = {
                        'interpretation': part.lower(),
                        'operator': part.lower()
                        }
                #self._logger.debug("operator part: %s" % part.lower())
                continue

            # string expr that we expand to dictsql expression
            elif isinstance(part, basestring):
                # dict sql expression
                dse = self._string_to_dictsql(part)
                #self._logger.debug('string part: %s  => %s' % (part, dse))
            elif isinstance(part, ParseResults):
                if part[1] in self.match_operators:
                    dse = self._parse_expr(part)
                    print dse
                else:
#                    for word in part:
#                        if str(word).lower() in ('or', 'and'):
#                            self._logger.debug('AND/ORing: ' + str(word) + str(type(word)))
                    dse = self._ast_to_dictsql(part)
            else:
                raise ParserError("Unhandled part in AST: %s" % part)

            print "DSE:", dse

            if lookahead is not None:
                if dss['val1'] is not None and dss['val2'] is not None:
                    print "nesting!"
                    dss = {
                            'operator': None,
                            'val1': dss,
                            'val2': None
                        }

            if dss['val1'] is None:
                #self._logger.debug('val1 not set, using dse: %s' % str(dse))
                dss['val1'] = dse
            else:
                #self._logger.debug("val1 is set, operator is '%s', val2 = dst: %s" % (dss['operator'], str(dse)))
                dss['val2'] = dse


        # special handling when AST is only one expression, then we overwrite
        # the dss with dse
        if len(ast) == 1:
            dss = dse
        if len(ast) == 0:
            dss = self._string_to_dictsql('')


        # return the final composed stack of dictsql expressions
        return dss


    def _string_to_dictsql(self, string):
        """ Do magic matching of single words or quoted string
        """
        #self._logger.debug("parsing string: " + str(string))
        #self._logger.debug("Query part '" + string + "' interpreted as text")

        dictsql = {
                'operator': 'or',
                'val1': {
                    'operator': 'or',
                    'val1': {
                        'operator': 'regex_match',
                        'val1': 'description',
                        'val2': string
                    },
                    'val2': {
                        'operator': 'regex_match',
                        'val1': 'comment',
                        'val2': string
                    }
                },
                'val2': {
                    'operator': 'regex_match',
                    'val1': 'node',
                    'val2': string
                },
                'interpretation': 'text',
                'attribute': 'vrf or name or description'
            }

        return dictsql


    def _parse_expr(self, part):
        """ Parse matching expression in form key <op> value

            For example;
                vlan > 1
                node = FOO-BAR
        """
        self._logger.debug("parsing expression: " + str(part))
        key, op, val = part

        dictsql = {
                'operator': op,
                'val1': key,
                'val2': val,
                'interpretation': 'expression'
            }

        return dictsql


    def _add_implicit_ops(self, input_ast):
        """ Add implicit AND operator between expressions if there is no
            explicit operator specified.
        """
        res_ast = []

        for token, lookahead in izip_longest(input_ast, input_ast[1:]):
            if isinstance(token, str) and token.lower() in self.boolean_operators:
                res_ast.append(token)
                continue
            if isinstance(lookahead, str) and lookahead.lower() in self.boolean_operators: 
                res_ast.append(token)
                continue
            res_ast.append(token)
            if lookahead is not None:
                res_ast.append('and')

        return res_ast



    def parse(self, input_string):
        raw_ast = self._string_to_ast(input_string)
        ast = self._add_implicit_ops(raw_ast)
        return self._ast_to_dictsql(ast)


class VrfSmartParser(SmartParser):
    columns = {
            'rt',
            'name',
            'description',
            'tags'
            }


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

    p = SmartParser()
    #dictsql, interpretation = p.parse('core (country=SE or country = NL OR (damp AND "foo bar")')
    #dictsql, interpretation = p.parse('core (country=SE or country = NL OR (damp AND "foo bar"))')
    import sys
    dictsql = p.parse(' '.join(sys.argv[1:]))
    import pprint
    print "----------"
    pp = pprint.PrettyPrinter(indent = 4)
    pp.pprint(dictsql)
    print "----------"
