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
import string

import pynipap
from pynipap import VRF, Pool, Prefix, NipapError
from command import Command


# definitions
valid_countries = [
    'AT', 'DE', 'DK', 'EE', 'FI', 'FR',
    'GB', 'HR', 'LT', 'LV', 'KZ', 'NL',
    'RU', 'SE', 'US' ] # test test, fill up! :)
valid_prefix_types = [ 'host', 'reservation', 'assignment' ]
valid_families = [ 'ipv4', 'ipv6' ]
valid_bools = [ 'true', 'false' ]
valid_priorities = [ 'low', 'medium', 'high' ]


# evil global vars
vrf = None
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



def get_vrf(arg = None, opts = None, abort = False):
    """ Returns VRF to work in

        Returns a pynipap.VRF object representing the VRF we are working
        in. If there is a VRF set globally, return this. If not, fetch the
        VRF named 'arg'. If 'arg' is None, fetch the default_vrf
        attribute from the config file and return this VRF.
    """

    # yep, global variables are evil
    global vrf

    # if there is a VRF set, return it
    if vrf is not None:
        return vrf

    if arg is None:
        # fetch default vrf
        try:
            vrf_rt = cfg.get('global', 'default_vrf')
        except ConfigParser.NoOptionError:
            # default to all VRFs
            vrf_rt = 'all'
    else:
        vrf_rt = arg

    if vrf_rt == 'none':
        vrf = VRF()
    elif vrf_rt == 'all':
        vrf = VRF()
        vrf.rt = 'all'
    else:
        try:
            vrf = VRF.list({ 'rt': vrf_rt })[0]
        except IndexError:
            if abort:
                print >> sys.stderr, "VRF %s not found." % str(vrf_rt)
                sys.exit(1)
            else:
                vrf = False

    return vrf



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
                        'val1': 'rt',
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
        val2 = "%s" % val

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

    query = _expand_list_query(opts)
    offset = 0
    limit = 100
    while True:
        res = Pool.search(query, { 'offset': offset, 'max_result': limit })
        if len(res['result']) == 0:
            print "No matching pools found"
            return
        elif offset == 0:
            print "%-19s %-39s %-14s %-8s" % (
                "Name", "Description", "Default type", "4 / 6"
            )
            print "-----------------------------------------------------------------------------------"

        for p in res['result']:
            if len(str(p.description)) > 38:
                desc = p.description[0:34] + "..."
            else:
                desc = p.description
            print "%-19s %-39s %-14s %-2s / %-3s" % (
                p.name, desc, p.default_type,
                str(p.ipv4_default_prefix_length),
                str(p.ipv6_default_prefix_length)
            )
        if len(res['result']) < limit:
            break
        offset += limit



def list_vrf(arg, opts):
    """ List VRFs matching a search criteria
    """

    if 'rt' in opts:
        opts['rt'] = '^' + opts['rt'] + '$'
    query = _expand_list_query(opts)

    offset = 0
    limit = 100
    while True:
        res = VRF.search(query, { 'offset': offset, 'max_result': limit })
        if len(res['result']) == 0:
            print "No matching VRFs found."
            return
        elif offset == 0:
            print "%-16s %-22s %-40s" % ("VRF", "Name", "Description")
            print "--------------------------------------------------------------------------------"

        for v in res['result']:
            if len(unicode(v.description)) > 40:
                desc = v.description[0:37] + "..."
            else:
                desc = v.description
            print "%-16s %-22s %-40s" % (v.rt, v.name, desc)

        if len(res['result']) < limit:
            break
        offset += limit



def list_prefix(arg, opts):
    """ List prefixes matching 'arg'
    """

    search_string = ''
    if type(arg) == list or type(arg) == tuple:
        search_string = ' '.join(arg)

    v = get_vrf(opts.get('vrf_rt'), abort=True)

    if v.rt == 'all':
        vrf_q = None
    else:
        vrf_q = {
            'operator': 'equals',
            'val1': 'vrf_rt',
            'val2': v.rt
        }


    offset = 0
    # small initial limit for "instant" result
    limit = 50
    while True:
        res = Prefix.smart_search(search_string, { 'parents_depth': -1,
            'offset': offset, 'max_result': limit }, vrf_q)

        if len(res['result']) == 0:
            print "No addresses matching '%s' found." % search_string
            return

        for p in res['result']:
            if p.display == False:
                continue

            vrf = None
            if p.vrf is not None:
                vrf = p.vrf.rt
            try:
                print "%-10s %-29s %-2s %-19s %-14s %-40s" % (vrf,
                    "".join("  " for i in range(p.indent)) + p.display_prefix,
                    p.type[0].upper(), p.node, p.order_id, p.description
                )
            except UnicodeEncodeError, e:
                print >> sys.stderr, "\nCrazy encoding for prefix %s\n" % p.prefix

        if len(res['result']) < limit:
            break
        offset += limit

        # let consecutive limit be higher to tax the XML-RPC backend less
        limit = 200




"""
    ADD FUNCTIONS
"""

def add_prefix(arg, opts):
    """ Add prefix to NIPAP
    """

    p = Prefix()
    p.prefix = opts.get('prefix')
    p.type = opts.get('type')
    p.description = opts.get('description')
    p.node = opts.get('node')
    p.country = opts.get('country')
    p.order_id = opts.get('order_id')
    p.alarm_priority = opts.get('alarm_priority')
    p.comment = opts.get('comment')
    p.monitor = _str_to_bool(opts.get('monitor'))

    if 'vrf_rt' in opts:
        if opts['vrf_rt'] != 'none':
            try:
                p.vrf = VRF.list({ 'rt': opts['vrf_rt'] })[0]
            except IndexError:
                print >> sys.stderr, "Could not find VRFi with RT %s" % str(opts['vrf_rt'])
                sys.exit(1)

    args = {}
    if 'from-pool' in opts:
        res = Pool.list({ 'name': opts['from-pool'] })
        if len(res) == 0:
            print >> sys.stderr, "No pool named %s found." % opts['from-pool']
            sys.exit(1)

        args['from-pool'] = res[0]

    if 'from-prefix' in opts:
        args['from-prefix'] = [ opts['from-prefix'], ]

    if 'prefix_length' in opts:
        args['prefix_length'] = int(opts['prefix_length'])

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

    if p.vrf is None:
        vrf_rt = 'none'
        print "Prefix %s added to the global VRF." % (p.display_prefix)
    else:
        print "Prefix %s added to VRF '%s' (%s) " % (p.display_prefix,
                p.vrf.name, p.vrf.rt)




def add_vrf(arg, opts):
    """ Add VRF to NIPAP
    """

    v = VRF()
    v.rt = opts.get('rt')
    v.name = opts.get('name')
    v.description = opts.get('description')

    try:
        v.save()
    except pynipap.NipapError, e:
        print >> sys.stderr, "Could not add VRF to NIPAP: %s" % e.message
        sys.exit(1)

    print "Added VRF %s with id %d" % (v.rt, v.id)



def add_pool(arg, opts):
    """ Add a pool.
    """

    p = Pool()
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

    print "Pool '%s' created with id %s" % (p.name, p.id)



"""
    VIEW FUNCTIONS
"""
def view_vrf(arg, opts):
    """ View a single VRF
    """

    res = VRF.list({ 'rt': arg })
    if len(res) < 1:
        print >> sys.stderr, "VRF %s not found." % arg
        sys.exit(1)

    v = res[0]

    print "-- VRF"
    print "  %-12s : %d" % ("ID", v.id)
    print "  %-12s : %s" % ("RT", v.rt)
    print "  %-12s : %s" % ("Name", v.name)
    print "  %-12s : %s" % ("Description", v.description)



def view_pool(arg, opts):
    """ View a single pool
    """

    res = Pool.list({ 'name': arg })

    if len(res) == 0:
        print "No pool named %s found." % arg
        return

    p = res[0]
    print  "-- Pool "
    print "  %-15s : %d" % ("ID", p.id)
    print "  %-15s : %s" % ("Name", p.name)
    print "  %-15s : %s" % ("Description", p.description)
    print "  %-15s : %s" % ("Default type", p.default_type)
    print "  %-15s : %s / %s" % ("Preflen (v4/v6)", str(p.ipv4_default_prefix_length), str(p.ipv6_default_prefix_length))
    print "\n-- Prefixes in pool"

    res = Prefix.list({ 'pool': p.id})
    for pref in res:
        print "  %s" % pref.display_prefix



def view_prefix(arg, opts):
    """ View a single prefix.
    """

    q = { 'operator': 'equals', 'val1': 'prefix', 'val2': arg }

    v = get_vrf(opts.get('vrf_rt'), abort=True)
    if v.rt != 'all':
        q = {
            'operator': 'and',
            'val1': q,
            'val2': {
                'operator': 'equals',
                'val1': 'vrf_rt',
                'val2': v.rt
            }
        }

    res = Prefix.search(q, {})

    if len(res['result']) == 0:
        print "Address %s not found." % arg
        return

    p = res['result'][0]
    if p.vrf is None:
        vrf = p.vrf
    else:
        vrf = p.vrf.rt

    print  "-- Address "
    print "  %-15s : %s" % ("Prefix", p.prefix)
    print "  %-15s : %s" % ("Display prefix", p.display_prefix)
    print "  %-15s : %s" % ("Type", p.type)
    print "  %-15s : IPv%s" % ("Family", p.family)
    print "  %-15s : %s" % ("VRF", vrf)
    print "  %-15s : %s" % ("Description", p.description)
    print "  %-15s : %s" % ("Node", p.node)
    print "  %-15s : %s" % ("Country", p.country)
    print "  %-15s : %s" % ("Order", p.order_id)
    print "  %-15s : %s" % ("Alarm priority", p.alarm_priority)
    print "  %-15s : %s" % ("Monitor", p.monitor)
    print "-- Comment"
    print p.comment or ''



"""
    REMOVE FUNCTIONS
"""

def remove_vrf(arg, opts):
    """ Remove VRF
    """

    res = VRF.list({ 'rt': arg })
    if len(res) < 1:
        print >> sys.stderr, "VRF %s not found." % arg
        sys.exit(1)

    v = res[0]

    print "RT: %s\nName: %s\nDescription: %s" % (v.rt, v.name, v.description)
    print "\nWARNING: THIS WILL REMOVE THE VRF INCLUDING ALL IT'S ADDRESSES"
    res = raw_input("Do you really want to remove the VRF %s? [y/n]: " % v.rt)

    if res == 'y':
        s.remove()
        print "VRF %s removed." % v.rt
    else:
        print "Operation canceled."



def remove_pool(arg, opts):
    """ Remove pool
    """

    res = Pool.list({ 'name': arg })
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
    recursive = False
    if opts.get('recursive') is True:
        recursive = True

    spec = { 'prefix': arg }
    if opts.get('vrf_rt') is None:
        v = get_vrf('none', abort=True)
    else:
        v = get_vrf(opts.get('vrf_rt'), abort=True)
    spec['vrf_rt'] = v.rt

    res = Prefix.list(spec)

    if len(res) < 1:
        print >> sys.stderr, "No prefix %s found." % arg
        sys.exit(1)

    # figure out VRF
    p = res[0]
    if p.vrf is None:
        vrf = None
    else:
        vrf = p.vrf.rt

    if recursive is True:
        # recursive delete

        # get affected prefixes
        query = {
                'val1': 'prefix',
                'operator': 'contained_within_equals',
                'val2': p.prefix
        }

        # add VRF to query if we have one
        if 'vrf_rt' in spec:
            vrf_q = {
                'val1': 'vrf_rt',
                'operator': 'equals',
                'val2': spec['vrf_rt']
            }
            query = {
                'val1': query,
                'operator': 'and',
                'val2': vrf_q
            }

        pres = Prefix.search(query, { 'parents_depth': 0, 'max_result': 1200 })
        if len(pres['result']) <= 1:
            res = raw_input("Do you really want to remove the prefix %s in VRF %s? [y/n]: " % (p.prefix, vrf))
        else:
            print "Recursively deleting %s will delete the following prefixes:" % p.prefix

            i = 0
            for rp in pres['result']:
                print "%-29s %-2s %-19s %-14s %-40s" % ("".join("  " for i in
                    range(rp.indent)) + rp.display_prefix,
                    rp.type[0].upper(), rp.node, rp.order_id, rp.description)
                i += 1
                if i > 10:
                    print ".. and %s other prefixes" % (len(pres['result']) - 10)
                    break

            res = raw_input("Do you really want to recursively remove %s prefixes in VRF %s? [y/n]: " % (len(pres['result']), vrf))
    else:
        # non recursive delete
        res = raw_input("Do you really want to remove the prefix %s in VRF %s? [y/n]: " % (p.prefix, vrf))

    if res.lower() == 'y' or res.lower() == 'yes':
        p.remove(recursive = recursive)
        if recursive is True:
            print "Prefix %s and %s other prefixes removed." % (p.prefix, (len(pres['result']) - 1))
        else:
            print "Prefix %s removed." % p.prefix
    else:
        print "Operation canceled."


"""
    MODIFY FUNCTIONS
"""

def modify_vrf(arg, opts):
    """ Modify a VRF with the options set in opts
    """

    res = VRF.list({ 'rt': arg })
    if len(res) < 1:
        print >> sys.stderr, "VRF %s not found." % arg
        sys.exit(1)

    v = res[0]

    if 'rt' in opts:
        v.rt = opts['rt']
    if 'name' in opts:
        v.name = opts['name']
    if 'description' in opts:
        v.description = opts['description']

    v.save()

    print "VRF %s saved." % v.rt



def modify_pool(arg, opts):
    """ Modify a pool with the options set in opts
    """

    res = Pool.list({ 'name': arg })
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

    spec = { 'prefix': arg }
    v = get_vrf(abort=True)
    spec['vrf_rt'] = v.rt

    res = Prefix.list(spec)
    if len(res) == 0:
        print >> sys.stderr, "Prefix %s not found in VRF %s." % (arg, v.rt)
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
    if 'alarm_priority' in opts:
        p.alarm_priority = opts['alarm_priority']
    if 'monitor' in opts:
        p.monitor = _str_to_bool(opts['monitor'])

    if 'vrf_rt' in opts:
        try:
            p.vrf = VRF.list({ 'rt': opts['vrf_rt'] })[0]
        except IndexError:
            print >> sys.stderr, "VRF %s not found." % opts['vrf_rt']
            sys.exit(1)

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
        if string.find(straw, key) == 0:
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

    search_string = '^'
    if arg is not None:
        search_string += arg

    res = Pool.search({
        'operator': 'regex_match',
        'val1': 'name',
        'val2': search_string
    })

    ret = []
    for p in res['result']:
        ret.append(p.name)

    return ret



def complete_vrf(arg):
    """ Returns list of matching VRFs
    """

    search_string = ''
    if arg is not None:
        search_string = '^%s' % arg

    res = VRF.search({
        'operator': 'regex_match',
        'val1': 'rt',
        'val2':  search_string
        })

    ret = []

    for v in res['result']:
        ret.append(v.rt)
    if re.match(search_string, 'none'):
        ret.append('none')

    return ret


def complete_vrf_virtual(arg):
    """ Returns list of matching VRFs

        Includes "virtual" VRF 'all' which is used in search
        operations
    """

    ret = complete_vrf(arg)

    search_string = ''
    if arg is not None:
        search_string = '^%s' % arg

    if re.match(search_string, 'all'):
        ret.append('all')

    return ret


""" The NIPAP command tree
"""
cmds = {
    'type': 'command',
    'children': {
        'address': {
            'type': 'command',
            'children': {
                # add
                'add': {
                    'type': 'command',
                    'exec': add_prefix,
                    'children': {
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
                        'vrf_rt': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                                'complete': complete_vrf,
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
                        'prefix_length': {
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
                    'rest_argument': {
                        'type': 'value',
                        'content_type': unicode,
                        'description': 'Prefix',
                    },
                    'children': {
                        'vrf_rt': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                                'description': 'VRF',
                                'complete': complete_vrf_virtual,
                            },
                        }
                    }
                },

                # modify
                'modify': {
                    'type': 'command',
                    'argument': {
                        'type': 'value',
                        'content_type': unicode,
                        'description': 'Prefix to edit',
                    },
                    'children': {
                        'vrf_rt': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                                'description': 'VRF',
                                'complete': complete_vrf,
                            },
                            'exec_immediately': get_vrf
                        },
                        'set': {
                            'type': 'command',
                            'exec': modify_prefix,
                            'children': {
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
                                'vrf_rt': {
                                    'type': 'option',
                                    'argument': {
                                        'type': 'value',
                                        'content_type': unicode,
                                        'complete': complete_vrf,
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
                    },
                    'children': {
	                    'vrf_rt': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                                'complete': complete_vrf,
                            }
                        },
                        'recursive': {
                            'type': 'bool'
                        }
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
                    },
                    'children': {
	                    'vrf_rt': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                                'complete': complete_vrf,
                            }
                        },
                    }
                }
            }
        },

        # VRF commands
        'vrf': {
            'type': 'command',
            'children': {

                # add
                'add': {
                    'type': 'command',
                    'exec': add_vrf,
                    'children': {
                        'rt': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                                'description': 'VRF RT'
                            }
                        },
                        'name': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                                'description': 'VRF name',
                            }

                        },
                        'description': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                                'description': 'Description of the VRF'
                            }
                        }
                    }
                },

                # list
                'list': {
                    'type': 'command',
                    'exec': list_vrf,
                    'children': {
                        'rt': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                                'description': 'VRF RT',
                                'complete': complete_vrf,
                            }
                        },
                        'name': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                                'description': 'VRF name',
                            }

                        },
                        'description': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                                'description': 'Description of the VRF'
                            }
                        }
                    }
                },

                # view
                'view': {
                    'exec': view_vrf,
                    'type': 'command',
                    'argument': {
                        'type': 'value',
                        'content_type': unicode,
                        'description': 'VRF',
                        'complete': complete_vrf,
                    }
                },

                # remove
                'remove': {
                    'exec': remove_vrf,
                    'type': 'command',
                    'argument': {
                        'type': 'value',
                        'content_type': unicode,
                        'description': 'VRF',
                        'complete': complete_vrf,
                    }
                },

                # modify
                'modify': {
                    'type': 'command',
                    'argument': {
                        'type': 'value',
                        'content_type': unicode,
                        'description': 'VRF',
                        'complete': complete_vrf,
                    },
                    'children': {
                        'set': {
                            'type': 'command',
                            'exec': modify_vrf,
                            'children': {
                                'rt': {
                                    'type': 'option',
                                    'argument': {
                                        'type': 'value',
                                        'content_type': unicode,
                                        'description': 'VRF RT'
                                    }
                                },
                                'name': {
                                    'type': 'option',
                                    'argument': {
                                        'type': 'value',
                                        'content_type': unicode,
                                        'description': 'VRF name',
                                    }

                                },
                                'description': {
                                    'type': 'option',
                                    'argument': {
                                        'type': 'value',
                                        'content_type': unicode,
                                        'description': 'Description of the VRF'
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
            'children': {

                # add
                'add': {
                    'type': 'command',
                    'exec': add_pool,
                    'children': {
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
                    'children': {
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
                    'children': {
                        'set': {
                            'type': 'command',
                            'exec': modify_pool,
                            'children': {
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

