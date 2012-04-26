#! /usr/bin/python
""" NIPAP shell command

    A shell command to interact with NIPAP.
"""


import os
import sys
import re
import shlex
import pipes
import subprocess
import ConfigParser

import pynipap
from pynipap import Schema, Pool, Prefix, NipapError
from command import Command


# definitions
valid_countries = [ 'DE', 'EE', 'NL', 'SE', 'US' ] # test test, fill up! :)
valid_prefix_types = [ 'host', 'reservation', 'assignment' ]
valid_families = [ 'ipv4', 'ipv6' ]
valid_bools = [ 'true', 'false' ]
valid_priorities = [ 'low', 'medium', 'high' ]


# evil global vars
schema = None
cfg = None



def setup_connection():
    """ Set up the global pynipap connection object
    """

    # build XML-RPC URI
    try:
        pynipap.xmlrpc_uri = "http://%(username)s:%(password)s@%(hostname)s:%(port)s" % {
                'username': cfg.get('global', 'username'),
                'password': cfg.get('global', 'password'),
                'hostname': cfg.get('global', 'hostname'),
                'port'    : cfg.get('global', 'port')
            }
    except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
        print >> sys.stderr, "Please define the username, password, hostname and port in your .nipaprc under the section 'global'"
        sys.exit(1)

    ao = pynipap.AuthOptions({'authoritative_source': 'nipap'})



def get_schema(arg = None, opts = None):
    """ Returns schema to work in

        Returns a pynipap.Schema object representing the schema we are working
        in. If there is a schema set globally, return this. If not, fetch the
        schema named 'arg'. If 'arg' is None, fetch the default_schema
        attribute from the config file and return this schema.
    """

    # yep, global variables are evil
    global schema

    # if there is a schema set, return it
    if schema is not None:
        return schema

    if arg is None:
        # fetch default schema
        try:
            schema_name = cfg.get('global', 'default_schema')
        except ConfigParser.NoOptionError:
            print >> sys.stderr, "Please define the default schema in your .nipaprc"
            sys.exit(1)
    else:
        schema_name = arg

    try:
        schema = Schema.list({ 'name': schema_name })[0]
    except IndexError:
        schema = False

    return schema



def _str_to_bool(arg):
    """ Return True or False depending on input string

        Parses the string 'arg' and returns True if it has the value "true",
        False if it has the value "false" and throws an exception otherwise.
    """

    if arg is None:
        return False

    if arg == 'true':
        return True
    elif arg == 'false':
        return False
    else:
        raise ValueError('Only values true and false permitted')



"""
    LIST FUNCTIONS
"""

def _expand_list_query(opts):
    """ Parse a dict and return a valid query dict

        Parses a dict containing object attributes and values and return a
        valid NIPAP query dict which regex matches the values and AND:s
        together all individual queries. The regex match is anchored in the
        beginning of the string.

        Example:

            {
                'name': 'cust',
                'vrf': '123:2'
            }

        will be expanded to the query dict

            {
                'operator': 'and',
                'val1': {
                        'operator': 'regex_match',
                        'val1': 'name',
                        'val2': '^cust'
                    },
                'val2': {
                        'operator': 'regex_match',
                        'val1': 'vrf',
                        'val2': '^123:2'
                    }
            }
    """

    # create list of query parts
    query_parts = []
    for key, val in opts.items():

        # standard case
        operator = 'regex_match'
        val1 = key
        val2 = "^%s" % val

        query_parts.append({
            'operator': operator,
            'val1': val1,
            'val2': val2
        })

    # Sum all query parts to one query
    query = {}
    if len(query_parts) > 0:
        query = query_parts[0]

    if len(query_parts) > 1:
        for query_part in query_parts[1:]:
            query = {
                'operator': 'and',
                'val1': query_part,
                'val2': query
            }

    return query


def list_pool(arg, opts):
    """ List pools matching a search criteria
    """

    s = get_schema()

    query = _expand_list_query(opts)
    res = Pool.search(s, query)
    if len(res['result']) > 0:
        print "%-19s %-39s %-14s %-8s" % (
            "Name", "Description", "Default type", "4 / 6"
        )
        print "-----------------------------------------------------------------------------------"
    else:
        print "No matching pools found"

    for p in res['result']:
        if len(p.description) > 38:
            desc = p.description[0:34] + "..."
        else:
            desc = p.description
        print "%-19s %-39s %-14s %-2s / %-3s" % (
            p.name, desc, p.default_type,
            str(p.ipv4_default_prefix_length),
            str(p.ipv6_default_prefix_length)
        )



def list_schema(arg, opts):
    """ List schemas matching a search criteria
    """

    query = _expand_list_query(opts)
    res = Schema.search(query)
    if len(res['result']) > 0:
        print "%-17s %-45s %-16s" % ("Name", "Description", "VRF")
        print "--------------------------------------------------------------------------------"
    else:
        print "No matching schemas found."

    for s in res['result']:
        if len(s.description) > 45:
            desc = s.description[0:42] + "..."
        else:
            desc = s.description
        print "%-17s %-45s %-16s" % (s.name, desc, s.vrf)



def list_prefix(arg, opts):
    """ List prefixes matching 'arg'
    """

    s = get_schema()

    res = Prefix.smart_search(s, arg, { 'parents_depth': -1, 'max_result': 1200 })
    if len(res['result']) == 0:
        print "No addresses matching '%s' found." % arg
        return

    for p in res['result']:
        if p.display == False:
            continue

        try:
            print "%-29s %-2s %-19s %-14s %-40s" % (
                "".join("  " for i in range(p.indent)) + p.display_prefix,
                p.type[0].upper(), p.node, p.order_id, p.description
            )
        except UnicodeEncodeError, e:
            print >> sys.stderr, "\nCrazy encoding for prefix %s\n" % p.prefix



"""
    ADD FUNCTIONS
"""

def add_prefix(arg, opts):
    """ Add prefix to NIPAP
    """

    s = get_schema()

    p = Prefix()
    p.schema = s
    p.prefix = opts.get('prefix')
    p.type = opts.get('type')
    p.description = opts.get('description')
    p.node = opts.get('node')
    p.country = opts.get('country')
    p.order_id = opts.get('order_id')
    p.vrf = opts.get('vrf')
    p.alarm_priority = opts.get('alarm_priority')
    p.comment = opts.get('comment')
    p.monitor = _str_to_bool(opts.get('monitor'))

    args = {}
    if 'from-pool' in opts:
        res = Pool.list(s, { 'name': opts['from-pool'] })
        if len(res) == 0:
            print >> sys.stderr, "No pool named %s found." % opts['from-pool']
            sys.exit(1)

        args['from-pool'] = res[0]

    if 'from-prefix' in opts:
        args['from-prefix'] = [ opts['from-prefix'], ]

    if 'prefix-length' in opts:
        args['prefix_length'] = int(opts['prefix-length'])

    if 'family' in opts:
        family = opts['family']
        if opts['family'] == 'ipv4':
            family = 4
        elif opts['family'] == 'ipv6':
            family = 6

        args['family'] = family


    try:
        p.save(args)
    except NipapError, e:
        print >> sys.stderr, "Could not add prefix to NIPAP: %s" % e.message
        sys.exit(1)

    print "Prefix %s added." % p.display_prefix



def add_schema(arg, opts):
    """ Add schema to NIPAP
    """

    s = Schema()
    s.name = opts.get('name')
    s.description = opts.get('description')
    s.vrf = opts.get('vrf')

    try:
        s.save()
    except pynipap.NipapError, e:
        print >> sys.stderr, "Could not add schema to NIPAP: %s" % e.message
        sys.exit(1)

    print "Added schema %s with id %d" % (s.name, s.id)



def add_pool(arg, opts):
    """ Add a pool.
    """

    p = Pool()
    p.schema = get_schema(opts.get('schema'))
    p.name = opts.get('name')
    p.description = opts.get('description')
    p.default_type = opts.get('default-type')
    p.ipv4_default_prefix_length = opts.get('ipv4_default_prefix_length')
    p.ipv6_default_prefix_length = opts.get('ipv6_default_prefix_length')

    try:
        p.save()
    except pynipap.NipapError, e:
        print >> sys.stderr, "Could not add pool to NIPAP: %s" % e.message
        sys.exit(1)

    print "Pool %s created with id %s" % (p.name, p.id)



"""
    VIEW FUNCTIONS
"""
def view_schema(arg, opts):
    """ View a single schema
    """

    res = Schema.list({ 'name': arg })
    if len(res) < 1:
        print >> sys.stderr, "No schema with name %s found." % arg
        sys.exit(1)

    s = res[0]

    print "-- Schema"
    print "  %-12s : %s" % ("Name", s.name)
    print "  %-12s : %d" % ("ID", s.id)
    print "  %-12s : %s" % ("Description", s.description)
    print "  %-12s : %s" % ("VRF", s.vrf)



def view_pool(arg, opts):
    """ View a single pool
    """

    s = get_schema(opts.get('schema'))

    res = Pool.list(s, { 'name': arg })

    if len(res) == 0:
        print "No pool named %s found." % arg
        return

    p = res[0]
    print  "-- Pool "
    print "  %-15s : %s" % ("Name", p.name)
    print "  %-15s : %s" % ("Description", p.description)
    print "  %-15s : %s" % ("Default type", p.default_type)
    print "  %-15s : %s / %s" % ("Preflen (v4/v6)", str(p.ipv4_default_prefix_length), str(p.ipv6_default_prefix_length))
    print "\n-- Prefixes in pool"

    res = Prefix.list(s, { 'pool': p.id})
    for pref in res:
        print "  %s" % pref.display_prefix



def view_prefix(arg, opts):
    """ View a single prefix.
    """

    s = get_schema()

    res = Prefix.search(s, { 'operator': 'equals', 'val1': 'prefix', 'val2': arg }, {})

    if len(res['result']) == 0:
        print "Address %s not found." % arg
        return

    p = res['result'][0]
    print  "-- Address "
    print "  %-15s : %s" % ("Prefix", p.prefix)
    print "  %-15s : %s" % ("Display prefix", p.display_prefix)
    print "  %-15s : %s" % ("Type", p.type)
    print "  %-15s : IPv%s" % ("Family", p.family)
    print "  %-15s : %s" % ("Description", p.description)
    print "  %-15s : %s" % ("Node", p.node)
    print "  %-15s : %s" % ("Order", p.order_id)
    print "  %-15s : %s" % ("VRF", p.vrf)
    print "  %-15s : %s" % ("Alarm priority", p.alarm_priority)
    print "  %-15s : %s" % ("Monitor", p.monitor)
    print "-- Comment"
    print p.comment




"""
    REMOVE FUNCTIONS
"""

def remove_schema(arg, opts):
    """ Remove schema
    """

    res = Schema.list({ 'name': arg })
    if len(res) < 1:
        print >> sys.stderr, "No schema with name %s found." % arg
        sys.exit(1)

    s = res[0]

    print "Name: %s\nDescription: %s\nVRF: %s" % (s.name, s.description, s.vrf)
    print "\nWARNING: THIS WILL REMOVE THE SCHEMA INCLUDING ALL IT'S ADDRESSES"
    res = raw_input("Do you really want to remove the schema %s? [y/n]: " % s.name)

    if res == 'y':
        s.remove()
        print "Schema %s removed." % s.name
    else:
        print "Operation canceled."



def remove_pool(arg, opts):
    """ Remove pool
    """

    s = get_schema()
    res = Pool.list(s, { 'name': arg })
    if len(res) < 1:
        print >> sys.stderr, "No pool with name %s found." % arg
        sys.exit(1)

    p = res[0]

    res = raw_input("Do you really want to remove the pool %s? [y/n]: " % p.name)

    if res == 'y':
        p.remove()
        print "Pool %s removed." % p.name
    else:
        print "Operation canceled."



def remove_prefix(arg, opts):
    """ Remove prefix
    """

    s = get_schema()
    res = Prefix.list(s, { 'prefix': arg })

    if len(res) < 1:
        print >> sys.stderr, "No prefix %s found." % arg
        sys.exit(1)

    p = res[0]

    res = raw_input("Do you really want to remove the prefix %s in schema %s? [y/n]: " % (p.prefix, s.name))

    if res == 'y':
        p.remove()
        print "Prefix %s removed." % p.prefix
    else:
        print "Operation canceled."


"""
    MODIFY FUNCTIONS
"""

def modify_schema(arg, opts):
    """ Modify a schema with the options set in opts
    """

    res = Schema.list({ 'name': arg })
    if len(res) < 1:
        print >> sys.stderr, "No schema with name %s found." % arg
        sys.exit(1)

    s = res[0]

    if 'name' in opts:
        s.name = opts['name']
    if 'vrf' in opts:
        s.vrf = opts['vrf']
    if 'description' in opts:
        s.description = opts['description']

    s.save()

    print "Schema %s saved." % s.name



def modify_pool(arg, opts):
    """ Modify a pool with the options set in opts
    """

    s = get_schema()
    res = Pool.list(s, { 'name': arg })
    if len(res) < 1:
        print >> sys.stderr, "No pool with name %s found." % arg
        sys.exit(1)

    p = res[0]

    if 'name' in opts:
        p.name = opts['name']
    if 'description' in opts:
        p.description = opts['description']
    if 'default-type' in opts:
        p.default_type = opts['default-type']
    if 'ipv4_default_prefix_length' in opts:
        p.ipv4_default_prefix_length = opts['ipv4_default_prefix_length']
    if 'ipv6_default_prefix_length' in opts:
        p.ipv6_default_prefix_length = opts['ipv6_default_prefix_length']

    p.save()

    print "Pool %s saved." % p.name



def modify_prefix(arg, opts):
    """ Modify the prefix 'arg' with the options 'opts'
    """

    s = get_schema()

    res = Prefix.list(s, { 'prefix': arg })
    if len(res) == 0:
        print >> sys.stderr, "Prefix %s not found in schema %s." % (arg, s.name)
        return

    p = res[0]

    if 'description' in opts:
        p.description = opts['description']
    if 'comment' in opts:
        p.comment = opts['comment']
    if 'node' in opts:
        p.node = opts['node']
    if 'type' in opts:
        p.type = opts['type']
    if 'country' in opts:
        p.country = opts['country']
    if 'order_id' in opts:
        p.order_id = opts['order_id']
    if 'vrf' in opts:
        p.vrf = opts['vrf']
    if 'alarm_priority' in opts:
        p.alarm_priority = opts['alarm_priority']
    if 'monitor' in opts:
        p.monitor = _str_to_bool(opts['monitor'])

    try:
        p.save()
    except NipapError, e:
        print >> sys.stderr, "Could not save prefix changes: %s" % e.message
        sys.exit(1)

    print "Prefix %s saved." % p.display_prefix



"""
    COMPLETION FUNCTIONS
"""

def _complete_string(key, haystack):
    """ Returns valid string completions

        Takes the string 'key' and compares it to each of the strings in
        'haystack'. The ones which beginns with 'key' are returned as result.
    """

    if len(key) == 0:
        return haystack

    match = []
    for straw in haystack:
        if re.match(key, straw):
            match.append(straw)
    return match



def complete_bool(arg):
    """ Complete strings "true" and "false"
    """
    return _complete_string(arg, valid_bools)



def complete_country(arg):
    """ Complete country codes ("SE", "DE", ...)
    """
    return _complete_string(arg, valid_countries)



def complete_family(arg):
    """ Complete inet family ("ipv4", "ipv6")
    """
    return _complete_string(arg, valid_families)



def complete_prefix_type(arg):
    """ Complete NIPAP prefix type
    """
    return _complete_string(arg, valid_prefix_types)



def complete_priority(arg):
    """ Complete NIPAP alarm priority
    """
    return _complete_string(arg, valid_priorities)



def complete_node(arg):
    """ Complete node hostname

        This function is currently a bit special as it looks in the config file
        for a command to use to complete a node hostname from an external
        system.

        It is configured by setting the config attribute "complete_node_cmd" to
        a shell command. The string "%search_string%" in the command will be
        replaced by the current search string.
    """

    # get complete command from config
    try:
        cmd = cfg.get('global', 'complete_node_cmd')
    except ConfigParser.NoOptionError:
        return [ '', ]

    cmd = re.sub('%search_string%', pipes.quote(arg), cmd)

    args = shlex.split(cmd)
    p = subprocess.Popen(args, stdout=subprocess.PIPE)
    res, err = p.communicate()

    nodes = res.split('\n')
    return nodes


def complete_pool_name(arg):
    """ Returns list of matching pool names
    """

    s = get_schema()
    search_string = '^'
    if arg is not None:
        search_string += arg

    res = Pool.search(s, {
        'operator': 'regex_match',
        'val1': 'name',
        'val2': search_string
    })

    ret = []
    for p in res['result']:
        ret.append(p.name)

    return ret



def complete_schema_name(arg):
    """ Returns list of matching schema names
    """

    search_string = ''
    if arg is not None:
        search_string = '^%s' % arg

    res = Schema.search({
        'operator': 'regex_match',
        'val1': 'name',
        'val2':  search_string
        })

    ret = []
    for schema in res['result']:
        ret.append(schema.name)

    return ret


""" The NIPAP command tree
"""
cmds = {
    'params': {
        'address': {
            'type': 'command',
            'params': {

                #set schema
                'schema': {
                    'type': 'option',
                    'argument': {
                        'type': 'value',
                        'content_type': unicode,
                        'description': 'Schema name',
                        'complete': complete_schema_name,
                    },
                    'exec_immediately': get_schema
                },

                # add
                'add': {
                    'type': 'command',
                    'exec': add_prefix,
                    'params': {
                        'comment': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                            }
                        },
                        'country': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                                'complete': complete_country,
                            }
                        },
                        'description': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                            }
                        },
                        'family': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                                'complete': complete_family,
                            }
                        },
                        'type': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'description': 'Prefix type: reservation | assignment | host',
                                'content_type': unicode,
                                'complete': complete_prefix_type,
                            }
                        },
                        'from-pool': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                                'complete': complete_pool_name,
                            }
                        },
                        'from-prefix': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                            }
                        },
                        'node': {
                            'type': 'option',
                            'content_type': unicode,
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                                'complete': complete_node,
                            }
                        },
                        'order': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                            }
                        },
                        'vrf': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                            }
                        },
                        'prefix': {
                            'type': 'option',
                            'content_type': unicode,
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                            }
                        },
                        'prefix-length': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': int
                            }
                        },
                        'monitor': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                                'complete': complete_bool,
                            }
                        },
                        'alarm_priority': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                                'complete': complete_priority,
                            }
                        }
                    },
                },

                # list
                'list': {
                    'type': 'command',
                    'exec': list_prefix,
                    'argument': {
                        'type': 'value',
                        'content_type': unicode,
                        'description': 'Prefix',
                    },
                },

                # modify
                'modify': {
                    'type': 'command',
                    'argument': {
                        'type': 'value',
                        'content_type': unicode,
                        'description': 'Prefix to edit',
                    },
                    'params': {
                        'set': {
                            'type': 'command',
                            'exec': modify_prefix,
                            'params': {
                                'comment': {
                                    'type': 'option',
                                    'argument': {
                                        'type': 'value',
                                        'content_type': unicode,
                                    }
                                },
                                'country': {
                                    'type': 'option',
                                    'argument': {
                                        'type': 'value',
                                        'content_type': unicode,
                                        'complete': complete_country,
                                    }
                                },
                                'description': {
                                    'type': 'option',
                                    'argument': {
                                        'type': 'value',
                                        'content_type': unicode,
                                    }
                                },
                                'family': {
                                    'type': 'option',
                                    'argument': {
                                        'type': 'value',
                                        'content_type': unicode,
                                        'complete': complete_family,
                                    }
                                },
                                'type': {
                                    'type': 'option',
                                    'argument': {
                                        'type': 'value',
                                        'description': 'Prefix type: reservation | assignment | host',
                                        'content_type': unicode,
                                        'complete': complete_prefix_type,
                                    }
                                },
                                'node': {
                                    'type': 'option',
                                    'content_type': unicode,
                                    'argument': {
                                        'type': 'value',
                                        'content_type': unicode,
                                        'complete': complete_node,
                                    }
                                },
                                'order': {
                                    'type': 'option',
                                    'argument': {
                                        'type': 'value',
                                        'content_type': unicode,
                                    }
                                },
                                'vrf': {
                                    'type': 'option',
                                    'argument': {
                                        'type': 'value',
                                        'content_type': unicode,
                                    }
                                },
                                'monitor': {
                                    'type': 'option',
                                    'argument': {
                                        'type': 'value',
                                        'content_type': unicode,
                                        'complete': complete_bool,
                                    }
                                },
                                'alarm_priority': {
                                    'type': 'option',
                                    'argument': {
                                        'type': 'value',
                                        'content_type': unicode,
                                        'complete': complete_priority,
                                    }
                                }
                            }
                        }
                    }
                },

                # remove
                'remove': {
                    'type': 'command',
                    'exec': remove_prefix,
                    'argument': {
                        'type': 'value',
                        'content_type': unicode,
                        'description': 'Remove address'
                    }
                },

                # view
                'view': {
                    'type': 'command',
                    'exec': view_prefix,
                    'argument': {
                        'type': 'value',
                        'content_type': unicode,
                        'description': 'Address to view'
                    }
                }
            }
        },

        # schema commands
        'schema': {
            'type': 'command',
            'params': {

                # add
                'add': {
                    'type': 'command',
                    'exec': add_schema,
                    'params': {
                        'vrf': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                                'description': 'VRF which the schema is mapped to'
                            }
                        },
                        'name': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                                'description': 'Schema name',
                            }

                        },
                        'description': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                                'description': 'VRF which the schema is mapped to'
                            }
                        }
                    }
                },

                # list
                'list': {
                    'type': 'command',
                    'exec': list_schema,
                    'params': {
                        'vrf': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                                'description': 'VRF which the schema is mapped to'
                            }
                        },
                        'name': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                                'description': 'Schema name',
                                'complete': complete_schema_name,
                            }

                        },
                        'description': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                                'description': 'VRF which the schema is mapped to'
                            }
                        }
                    }
                },

                # view
                'view': {
                    'exec': view_schema,
                    'type': 'command',
                    'argument': {
                        'type': 'value',
                        'content_type': unicode,
                        'description': 'Schema name',
                        'complete': complete_schema_name,
                    }
                },

                # remove
                'remove': {
                    'exec': remove_schema,
                    'type': 'command',
                    'argument': {
                        'type': 'value',
                        'content_type': unicode,
                        'description': 'Schema name',
                        'complete': complete_schema_name,
                    }
                },

                # modify
                'modify': {
                    'type': 'command',
                    'argument': {
                        'type': 'value',
                        'content_type': unicode,
                        'description': 'Schema name',
                        'complete': complete_schema_name,
                    },
                    'params': {
                        'set': {
                            'type': 'command',
                            'exec': modify_schema,
                            'params': {
                                'vrf': {
                                    'type': 'option',
                                    'argument': {
                                        'type': 'value',
                                        'content_type': unicode,
                                        'description': 'VRF which the schema is mapped to'
                                    }
                                },
                                'name': {
                                    'type': 'option',
                                    'argument': {
                                        'type': 'value',
                                        'content_type': unicode,
                                        'description': 'Schema name',
                                    }

                                },
                                'description': {
                                    'type': 'option',
                                    'argument': {
                                        'type': 'value',
                                        'content_type': unicode,
                                        'description': 'VRF which the schema is mapped to'
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },

        # pool commands
        'pool': {
            'type': 'command',
            'params': {

                #set schema
                'schema': {
                    'type': 'option',
                    'argument': {
                        'type': 'value',
                        'content_type': unicode,
                        'description': 'Schema name',
                        'complete': complete_schema_name,
                    },
                    'exec_immediately': get_schema
                },

                # add
                'add': {
                    'type': 'command',
                    'exec': add_pool,
                    'params': {
                        'default-type': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                                'descripton': 'Default prefix type: reservation | assignment | host',
                                'complete': complete_prefix_type,
                            }
                        },
                        'name': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                                'descripton': 'Name of the pool'
                            }
                        },
                        'description': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                                'descripton': 'A short description of the pool'
                            }
                        },
                        'ipv4_default_prefix_length': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': int,
                                'descripton': 'Default IPv4 prefix length'
                            }
                        },
                        'ipv6_default_prefix_length': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': int,
                                'descripton': 'Default IPv6 prefix length'
                            }
                        }
                    }
                },

                # list
                'list': {
                    'type': 'command',
                    'exec': list_pool,
                    'params': {
                        'default-type': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                                'descripton': 'Default prefix type: reservation | assignment | host',
                                'complete': complete_prefix_type,
                            }
                        },
                        'name': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                                'descripton': 'Name of the pool'
                            }
                        },
                        'description': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                                'descripton': 'A short description of the pool'
                            }
                        },
                        'ipv4_default_prefix_length': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': int,
                                'descripton': 'Default IPv4 prefix length'
                            }
                        },
                        'ipv6_default_prefix_length': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': int,
                                'descripton': 'Default IPv6 prefix length'
                            }
                        }
                    }
                },

                # remove
                'remove': {
                    'type': 'command',
                    'exec': remove_pool,
                    'argument': {
                        'type': 'value',
                        'content_type': unicode,
                        'description': 'Pool name',
                        'complete': complete_pool_name,
                    }
                },

                # modify
                'modify': {
                    'type': 'command',
                    'argument': {
                        'type': 'value',
                        'content_type': unicode,
                        'description': 'Pool name',
                        'complete': complete_pool_name,
                    },
                    'params': {
                        'set': {
                            'type': 'command',
                            'exec': modify_pool,
                            'params': {
                                'default-type': {
                                    'type': 'option',
                                    'argument': {
                                        'type': 'value',
                                        'content_type': unicode,
                                        'descripton': 'Default prefix type: reservation | assignment | host',
                                        'complete': complete_prefix_type,
                                    }
                                },
                                'name': {
                                    'type': 'option',
                                    'argument': {
                                        'type': 'value',
                                        'content_type': unicode,
                                        'descripton': 'Name of the pool'
                                    }
                                },
                                'description': {
                                    'type': 'option',
                                    'argument': {
                                        'type': 'value',
                                        'content_type': unicode,
                                        'descripton': 'A short description of the pool'
                                    }
                                },
                                'ipv4_default_prefix_length': {
                                    'type': 'option',
                                    'argument': {
                                        'type': 'value',
                                        'content_type': int,
                                        'descripton': 'Default IPv4 prefix length'
                                    }
                                },
                                'ipv6_default_prefix_length': {
                                    'type': 'option',
                                    'argument': {
                                        'type': 'value',
                                        'content_type': int,
                                        'descripton': 'Default IPv6 prefix length'
                                    }
                                }
                            }
                        }
                    }
                },

                # view
                'view': {
                    'exec': view_pool,
                    'type': 'command',
                    'argument': {
                        'type': 'value',
                        'content_type': unicode,
                        'description': 'Pool name',
                        'complete': complete_pool_name,
                    }
                }
            }
        }
    }
}

# read configuration
cfg = ConfigParser.ConfigParser()
cfg.read(os.path.expanduser('~/.nipaprc'))

setup_connection()

if __name__ == '__main__':

    try:
        cmd = Command(cmds, sys.argv[1::])
    except ValueError, e:
        print >> sys.stderr, "Error: %s" % e.message
        sys.exit(1)

    # execute command
    if cmd.exe is None:
        print "Incomplete command specified"
        print "valid completions: %s" % " ".join(cmd.next_values())
        sys.exit(1)

    try:
        cmd.exe(cmd.arg, cmd.exe_options)
    except NipapError, e:
        print >> sys.stderr, "Command failed:\n  %s" % e.message
        sys.exit(1)

