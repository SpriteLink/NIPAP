#! /usr/bin/python
"""

    NIPAP Command-line interface

"""

import os
import sys
import re
import ConfigParser
sys.path.append('../pynipap')
import pynipap
from command import Command

def setup_connection(cfg):

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


def get_default_schema(cfg):
    # fetch default schema
    try:
        schema_name = cfg.get('global', 'schema')
    except ConfigParser.NoOptionError:
        print >> sys.stderr, "Please define the default schema in your .nipaprc"
        sys.exit(1)

    return pynipap.Schema.list({ 'name': schema_name })[0]


def list_pool(cfg, arg, opts):
    """ List pools matching a search criteria
    """

    s = get_default_schema(cfg)
    search_string = ''
    if arg is not None:
        search_string = arg
    res = pynipap.Pool.smart_search(s, search_string)
    for p in res['result']:
        print "%s" % p.name



def list_schema(cfg, arg, opts):
    """ List pools matching a search criteria
    """

    search_string = ''
    if arg is not None:
        search_string = arg
    res = pynipap.Schema.smart_search(search_string)
    for s in res['result']:
        print "%s" % s.name

def list_prefix(cfg, arg, opts):
    pass


"""
    ADD FUNCTIONS
"""

def add_prefix(arg, opts):
    pass


def add_schema(cfg, arg, opts):
    """ Add schema to NIPAP
    """

    s = pynipap.Schema()
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
    pass

"""
    VIEW FUNCTIONS
"""
def view_schema(cfg, arg, opts):
    """ View a single schema
    """

    res = pynipap.Schema.list({ 'name': arg })
    if len(res) < 1:
        print >> sys.stderr, "No schema with name %s found." % arg
        sys.exit(1)

    s = res[0]

    print "Name: %s\nDescription: %s\nVRF: %s" % (s.name, s.description, s.vrf)


def view_prefix(arg, opts):
    """ View a single prefix.
    """
    p = pynipap.Prefix.get()
    pass


"""
    COMPLETION METHODS
"""

def complete_family(arg):
    valid = [ 'ipv4', 'ipv6' ]
    if len(arg) == 0:
        return valid

    match = []
    for e in valid:
        if re.match(arg, e):
            match.append(e)
    return match


def complete_pool_name(arg):
    
    s = get_default_schema(cfg)
    search_string = ''
    if arg is not None:
        search_string = arg
    # shuld probably be changed to an anchored regexp search
    res = pynipap.Pool.smart_search(s, search_string)
    ret = []
    for p in res['result']:
        ret.append(p.name)

def complete_schema_name(arg):

    search_string = ''
    if arg is not None:
        search_string = '^%s' % arg

    res = pynipap.Schema.search({
        'operator': 'regex_match', 
        'val1': 'name',
        'val2':  search_string
        })
    ret = []
    for schema in res['result']:
        ret.append(schema.name)

    return ret

"""
    VALIDATION METHODS
"""
def validate_family(arg):
    return arg in [ 'ipv4', 'ipv6' ]


def validate_schema_name(arg):

    s = pynipap.Schema.list({ 'name': arg })
    return len(s) == 1


cmds = {
    'params': {
        'address': {
            'type': 'command',
            'params': {
                'add': {
                    'type': 'command',
                    'params': {
                        'comment': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
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
                                'validator': validate_family
                            }
                        },
                        'from-pool': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                                'complete': complete_pool_name,
#                                'validator': validate_pool
                            }
                        },
                        'node': {
                            'type': 'option',
                            'content_type': unicode,
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
#                                'complete': complete_node,
#                                'validator': validate_node
                            }
                        },
                        'order': {
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
                    },
                    'exec': add_prefix,
                },
                'list': {
                    'type': 'command',
                    'exec': list_prefix
                },
                'modify': {
                    'type': 'command',
                },
                'remove': {
                    'type': 'command',
                    'argument': {
                        'content_type': unicode,
                        'description': 'Address to remove'
                    }
                },
                'view': {
                    'type': 'command',
                    'exec': view_prefix,
                    'argument': {
                        'type': 'argument',
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
                'list': {
                    'type': 'command',
                    'exec': list_schema,
#                    'argument': {
#                        'type': 'value',
#                        'content_type': unicode,
#                        'descripton': 'Schema search string'
#                    },
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
                                'validator': validate_schema_name
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
                'view': {
                    'exec': view_schema,
                    'type': 'command',
                    'argument': {
                        'type': 'value',
                        'content_type': unicode,
                        'description': 'Schema name',
                        'complete': complete_schema_name,
                        'validator': validate_schema_name
                    }
                }
            }
        },

        # pool commands
        'pool': {
            'type': 'command',
            'params': {
                'add': {
                    'type': 'command',
                    'exec': add_pool,
                },
                'list': {
                    'type': 'command',
                    'exec': list_pool,
                    'argument': {
                        'type': 'value',
                        'content_type': unicode,
                        'descripton': 'Pool search string',
                    },
                    'params': {
                        'default_type': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                                'descripton': 'Schema search string'
                                
                            }
                        },
                        'name': {

                        },
                        'description': {

                        }

                    }
                }
            }
        }
    }
}

# read configuration
cfg = ConfigParser.ConfigParser()
cfg.read(os.path.expanduser('~/.nipaprc'))

setup_connection(cfg)

if __name__ == '__main__':

    try:
        cmd = Command(cmds, sys.argv[1::])
    except ValueError, e:
        print >> sys.stderr, "Error: %s" % e.message
        sys.exit(1)

    # execute command
    if cmd.exe is None:
        print "Incomplete command specified"
        print "valid completions: %s" % cmd.get_complete_string()
        sys.exit(1)

    cmd.exe(cfg, cmd.arg, cmd.exe_options)

