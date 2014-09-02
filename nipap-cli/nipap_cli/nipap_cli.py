#! /usr/bin/python
""" NIPAP shell command

    A shell command to interact with NIPAP.
"""


import ConfigParser
import csv
import os
import pipes
import re
import shlex
import string
import subprocess
import sys

import pynipap
from pynipap import Pool, Prefix, Tag, VRF, NipapError
from command import Command


# definitions
valid_countries = [
    'AT', 'DE', 'DK', 'EE', 'FI', 'FR',
    'GB', 'HR', 'LT', 'LV', 'KZ', 'NL',
    'RU', 'SE', 'US' ] # test test, fill up! :)
valid_prefix_types = [ 'host', 'reservation', 'assignment' ]
valid_families = [ 'ipv4', 'ipv6', 'dual-stack' ]
valid_bools = [ 'true', 'false' ]
valid_priorities = [ 'warning', 'low', 'medium', 'high', 'critical' ]


# evil global vars
vrf = None
cfg = None
pool = None



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

    ao = pynipap.AuthOptions({
        'authoritative_source': 'nipap',
        'username': os.getenv('NIPAP_IMPERSONATE_USERNAME') or cfg.get('global', 'username'),
        'full_name': os.getenv('NIPAP_IMPERSONATE_FULL_NAME'),
        })



def vrf_format(vrf):
    return "VRF '%s' [RT: %s]" % (vrf.name, vrf.rt or '-')


def get_pool(arg = None, opts = None, abort = False):
    """ Returns pool to work with

        Returns a pynipap.Pool object representing the pool we are working with.
    """
    # yep, global variables are evil
    global pool

    try:
        pool = Pool.list({ 'name': arg })[0]
    except IndexError:
        if abort:
            print >> sys.stderr, "Pool '%s' not found." % str(arg)
            sys.exit(1)
        else:
            pool = None

    return pool



def get_vrf(arg = None, default_var = 'default_vrf_rt', abort = False):
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
            vrf_rt = cfg.get('global', default_var)
        except ConfigParser.NoOptionError:
            # default to all VRFs
            vrf_rt = 'all'
    else:
        vrf_rt = arg

    if vrf_rt.lower() == 'all':
        vrf = VRF()
        vrf.rt = 'all'
    else:
        if vrf_rt.lower() in ('-', 'none'):
            vrf_rt = None

        try:
            vrf = VRF.search({ 'val1': 'rt',
                'operator': 'equals',
                'val2': vrf_rt
                })['result'][0]
        except (KeyError, IndexError):
            if abort:
                print >> sys.stderr, "VRF with [RT: %s] not found." % str(vrf_rt)
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


def list_pool(arg, opts, shell_opts):
    """ List pools matching a search criteria
    """

    search_string = ''
    if type(arg) == list or type(arg) == tuple:
        search_string = ' '.join(arg)

    v = get_vrf(opts.get('vrf_rt'), default_var='default_list_vrf_rt', abort=True)

    if v.rt == 'all':
        vrf_q = None
    else:
        vrf_q = {
            'operator': 'equals',
            'val1': 'vrf_rt',
            'val2': v.rt
        }

    offset = 0
    limit = 100
    while True:
        res = Pool.smart_search(search_string, { 'offset': offset, 'max_result': limit }, vrf_q)
        if offset == 0: # first time in loop?
            if len(res['result']) == 0:
                print "No matching pools found"
                return

            print "%-19s %-2s %-39s %-13s  %-8s %s" % (
                "Name", "#", "Description", "Default type", "4 / 6", "Implied VRF"
                )
            print "------------------------------------------------------------------------------------------------"

        for p in res['result']:
            if len(str(p.description)) > 38:
                desc = p.description[0:34] + "..."
            else:
                desc = p.description

            vrf_rt = '-'
            vrf_name = '-'
            if p.vrf is not None:
                vrf_rt = p.vrf.rt or '-'
                vrf_name = p.vrf.name

            tags = '-'
            if len(p.tags) > 0:
                tags = "#%d" % (len(p.tags))

            print "%-19s %-2s %-39s %-13s %-2s / %-3s  [RT: %s] %s" % (
                p.name, tags, desc, p.default_type,
                str(p.ipv4_default_prefix_length or '-'),
                str(p.ipv6_default_prefix_length or '-'),
                vrf_rt, vrf_name
            )
        if len(res['result']) < limit:
            break
        offset += limit



def list_vrf(arg, opts, shell_opts):
    """ List VRFs matching a search criteria
    """

    # rt is a regexp match on the VRF RT but as most people don't expect to see
    # 123:123 in the result when searching for '123:1', we anchor it per default
    if 'rt' in opts:
        opts['rt'] = '^' + opts['rt'] + '$'
    query = _expand_list_query(opts)

    offset = 0
    limit = 100
    while True:
        res = VRF.search(query, { 'offset': offset, 'max_result': limit })
        if offset == 0:
            if len(res['result']) == 0:
                print "No matching VRFs found."
                return

            print "%-16s %-22s %-2s %-40s" % ("VRF RT", "Name", "#", "Description")
            print "--------------------------------------------------------------------------------"

        for v in res['result']:
            tags = '-'
            if len(v.tags) > 0:
                tags = '#%d' % len(v.tags)
            if len(unicode(v.description)) > 100:
                desc = v.description[0:97] + "..."
            else:
                desc = v.description
            print "%-16s %-22s %-2s %-40s" % (v.rt or '-', v.name, tags, desc)

        if len(res['result']) < limit:
            break
        offset += limit



def list_prefix(arg, opts, shell_opts):
    """ List prefixes matching 'arg'
    """

    search_string = ''
    if type(arg) == list or type(arg) == tuple:
        search_string = ' '.join(arg)

    v = get_vrf(opts.get('vrf_rt'), default_var='default_list_vrf_rt', abort=True)

    if v.rt == 'all':
        vrf_text = 'any VRF'
        vrf_q = None
    else:
        vrf_text = vrf_format(v)
        vrf_q = {
            'operator': 'equals',
            'val1': 'vrf_rt',
            'val2': v.rt
        }
    print "Searching for prefixes in %s..." % vrf_text


    offset = 0
    # small initial limit for "instant" result
    limit = 50
    min_indent = 0
    while True:
        res = Prefix.smart_search(search_string, { 'parents_depth': -1,
            'include_neighbors': True, 'offset': offset, 'max_result': limit },
            vrf_q)

        if offset == 0: # first time in loop?
            if len(res['result']) == 0:
                print "No addresses matching '%s' found." % search_string
                return

            # Guess the width of the prefix column by looking at the initial
            # result set.
            for p in res['result']:
                indent = p.indent * 2 + len(p.prefix)
                if indent > min_indent:
                    min_indent = indent
            min_indent += 15

            # print column headers
            prefix_str = "%%-14s %%-%ds %%-1s %%-2s %%-19s %%-14s %%-14s %%-s" % min_indent
            column_header = prefix_str % ('VRF', 'Prefix', '', '#', 'Node',
                    'Order', 'Customer', 'Description')
            print column_header
            print "".join("=" for i in xrange(len(column_header)))

        for p in res['result']:
            if p.display == False:
                continue

            try:
                tags = '-'
                if len(p.tags) > 0:
                    tags = '#%d' % len(p.tags)
                print prefix_str % (p.vrf.rt or '-',
                    "".join("  " for i in xrange(p.indent)) + p.display_prefix,
                    p.type[0].upper(), tags, p.node, p.order_id,
                    p.customer_id, p.description
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

def add_prefix(arg, opts, shell_opts):
    """ Add prefix to NIPAP
    """

    # sanity checks
    if 'from-pool' not in opts and 'from-prefix' not in opts and 'prefix' not in opts:
        print >> sys.stderr, "ERROR: 'prefix', 'from-pool' or 'from-prefix' must be specified."
        sys.exit(1)

    if len([opt for opt in opts if opt in ['from-pool', 'from-prefix', 'prefix']]) > 1:
        print >> sys.stderr, "ERROR: Use either assignment 'from-pool', 'from-prefix' or manual mode (using 'prefix')"
        sys.exit(1)

    if 'from-pool' in opts:
        return add_prefix_from_pool(arg, opts)

    args = {}

    p = Prefix()
    p.prefix = opts.get('prefix')
    p.type = opts.get('type')
    p.description = opts.get('description')
    p.node = opts.get('node')
    p.country = opts.get('country')
    p.order_id = opts.get('order_id')
    p.customer_id = opts.get('customer_id')
    p.alarm_priority = opts.get('alarm_priority')
    p.comment = opts.get('comment')
    p.monitor = _str_to_bool(opts.get('monitor'))
    p.vlan = opts.get('vlan')
    p.tags = list(csv.reader([opts.get('tags', '')], escapechar='\\'))[0]

    p.vrf = get_vrf(opts.get('vrf_rt'), abort=True)


    if 'from-prefix' in opts:
        args['from-prefix'] = [ opts['from-prefix'], ]

    if 'prefix_length' in opts:
        args['prefix_length'] = int(opts['prefix_length'])

    if 'family' in opts:
        if opts['family'] == 'ipv4':
            family = 4
        elif opts['family'] == 'ipv6':
            family = 6
        elif opts['family'] == 'dual-stack':
            print >> sys.stderr, "ERROR: dual-stack mode only valid for from-pool assignments"
            sys.exit(1)

        args['family'] = family

    # try to automatically figure out type for new prefix when not
    # allocating from a pool

    # get a list of prefixes that contain this prefix
    vrf_id = 0
    if p.vrf:
        vrf_id = p.vrf.id

    if 'from-prefix' in args:
        parent_prefix = args['from-prefix'][0]
        parent_op = 'equals'
    else:
        parent_prefix = opts.get('prefix').split('/')[0]
        parent_op = 'contains'

    # prefix must be a CIDR network, ie no bits set in host part, so we
    # remove the prefix length part of the prefix as then the backend will
    # assume all bits being set
    auto_type_query = {
            'val1': {
                'val1'      : 'prefix',
                'operator'  : parent_op,
                'val2'      : parent_prefix
                },
            'operator': 'and',
            'val2': {
                'val1'      : 'vrf_id',
                'operator'  : 'equals',
                'val2'      : vrf_id
                }
        }
    res = Prefix.search(auto_type_query, { })

    # no results, ie the requested prefix is a top level prefix
    if len(res['result']) == 0:
        if p.type is None:
            print >> sys.stderr, "ERROR: Type of prefix must be specified ('assignment' or 'reservation')."
            sys.exit(1)
    else:
        # last prefix in list will be the parent of the new prefix
        parent = res['result'][-1]

        # if the parent is an assignment, we can assume the new prefix to be
        # a host and act accordingly
        if parent.type == 'assignment':
            # automatically set type
            if p.type is None:
                print >> sys.stderr, "WARNING: Parent prefix is of type 'assignment'. Automatically setting type 'host' for new prefix."
            elif p.type == 'host':
                pass
            else:
                print >> sys.stderr, "WARNING: Parent prefix is of type 'assignment'. Automatically overriding specified type '%s' with type 'host' for new prefix." % p.type
            p.type = 'host'

            # if it's a manually specified prefix
            if 'prefix' in opts:
                # fiddle prefix length to all bits set
                if parent.family == 4:
                    p.prefix = p.prefix.split('/')[0] + '/32'
                else:
                    p.prefix = p.prefix.split('/')[0] + '/128'

            # for from-prefix, we set prefix_length to host length
            elif 'from-prefix' in opts:
                if parent.family == 4:
                    args['prefix_length'] = 32
                else:
                    args['prefix_length'] = 128

    try:
        p.save(args)
    except NipapError as exc:
        print >> sys.stderr, "Could not add prefix to NIPAP: %s" % str(exc)
        sys.exit(1)

    print "Prefix %s added to %s" % (p.display_prefix, vrf_format(p.vrf))



def add_prefix_from_pool(arg, opts):
    """ Add prefix using from-pool to NIPAP
    """

    args = {}

    # sanity checking
    if 'from-pool' in opts:
        res = Pool.list({ 'name': opts['from-pool'] })
        if len(res) == 0:
            print >> sys.stderr, "No pool named '%s' found." % opts['from-pool']
            sys.exit(1)

        args['from-pool'] = res[0]

    if 'family' not in opts:
        print >> sys.stderr, "ERROR: You have to specify the address family."
        sys.exit(1)

    if opts['family'] == 'ipv4':
        afis = [4]
    elif opts['family'] == 'ipv6':
        afis = [6]
    elif opts['family'] == 'dual-stack':
        afis = [4, 6]
        if 'prefix_length' in opts:
            print >> sys.stderr, "ERROR: 'prefix_length' can not be specified for 'dual-stack' assignment"
            sys.exit(1)
    else:
        print >> sys.stderr, "ERROR: 'family' must be one of: %s" % " ".join(valid_families)
        sys.exit(1)

    if 'prefix_length' in opts:
        args['prefix_length'] = int(opts['prefix_length'])

    for afi in afis:
        p = Prefix()
        p.prefix = opts.get('prefix')
        p.type = opts.get('type')
        p.description = opts.get('description')
        p.node = opts.get('node')
        p.country = opts.get('country')
        p.order_id = opts.get('order_id')
        p.customer_id = opts.get('customer_id')
        p.alarm_priority = opts.get('alarm_priority')
        p.comment = opts.get('comment')
        p.monitor = _str_to_bool(opts.get('monitor'))
        p.vlan = opts.get('vlan')
        p.tags = list(csv.reader([opts.get('tags', '')], escapechar='\\'))[0]

        p.vrf = get_vrf(opts.get('vrf_rt'), abort=True)
        # set type to default type of pool unless already set
        if p.type is None:
            if args['from-pool'].default_type is None:
                print >> sys.stderr, "ERROR: Type not specified and no default-type specified for pool: %s" % opts['from-pool']
            p.type = args['from-pool'].default_type

        args['family'] = afi

        try:
            p.save(args)
        except NipapError as exc:
            print >> sys.stderr, "Could not add prefix to NIPAP: %s" % str(exc)
            sys.exit(1)

        print "Prefix %s added to %s" % (p.display_prefix, vrf_format(p.vrf))



def add_vrf(arg, opts, shell_opts):
    """ Add VRF to NIPAP
    """

    v = VRF()
    v.rt = opts.get('rt')
    v.name = opts.get('name')
    v.description = opts.get('description')
    v.tags = list(csv.reader([opts.get('tags', '')], escapechar='\\'))[0]

    try:
        v.save()
    except pynipap.NipapError as exc:
        print >> sys.stderr, "Could not add VRF to NIPAP: %s" % str(exc)
        sys.exit(1)

    print "Added %s" % (vrf_format(v))



def add_pool(arg, opts, shell_opts):
    """ Add a pool.
    """

    p = Pool()
    p.name = opts.get('name')
    p.description = opts.get('description')
    p.default_type = opts.get('default-type')
    p.ipv4_default_prefix_length = opts.get('ipv4_default_prefix_length')
    p.ipv6_default_prefix_length = opts.get('ipv6_default_prefix_length')
    if 'tags' in opts:
        tags = list(csv.reader([opts.get('tags', '')], escapechar='\\'))[0]
        p.tags = {}
        for tag_name in tags:
            tag = Tag()
            tag.name = tag_name
            p.tags[tag_name] = tag

    try:
        p.save()
    except pynipap.NipapError as exc:
        print >> sys.stderr, "Could not add pool to NIPAP: %s" % str(exc)
        sys.exit(1)

    print "Pool '%s' created." % (p.name)



"""
    VIEW FUNCTIONS
"""
def view_vrf(arg, opts, shell_opts):
    """ View a single VRF
    """

    if arg is None:
        print >> sys.stderr, "ERROR: Please specify the RT of the VRF to view."
        sys.exit(1)

    # interpret as default VRF (ie, RT = None)
    if arg.lower() in ('-', 'none'):
        arg = None

    try:
        v = VRF.search({
            'val1': 'rt',
            'operator': 'equals',
            'val2': arg }
            )['result'][0]
    except (KeyError, IndexError):
        print >> sys.stderr, "VRF with [RT: %s] not found." % str(arg)
        sys.exit(1)

    print "-- VRF"
    print "  %-26s : %d" % ("ID", v.id)
    print "  %-26s : %s" % ("RT", v.rt)
    print "  %-26s : %s" % ("Name", v.name)
    print "  %-26s : %s" % ("Description", v.description)

    print "-- Tags"
    for tag_name in sorted(v.tags, key=lambda s: s.lower()):
        print "  %s" % tag_name
    # statistics
    if v.total_addresses_v4 == 0:
        used_percent_v4 = 0
    else:
        used_percent_v4 = (float(v.used_addresses_v4)/v.total_addresses_v4)*100
    if v.total_addresses_v6 == 0:
        used_percent_v6 = 0
    else:
        used_percent_v6 = (float(v.used_addresses_v6)/v.total_addresses_v6)*100
    print "-- Statistics"
    print "  %-26s : %s" % ("IPv4 prefixes", v.num_prefixes_v4)
    print "  %-26s : %.0f / %.0f (%.2f%% of %.0f)" % ("IPv4 addresses Used / Free",
            v.used_addresses_v4, v.free_addresses_v4, used_percent_v4,
            v.total_addresses_v4)
    print "  %-26s : %s" % ("IPv6 prefixes", v.num_prefixes_v6)
    print "  %-26s : %.4e / %.4e (%.2f%% of %.4e)" % ("IPv6 addresses Used / Free",
            v.used_addresses_v6, v.free_addresses_v6, used_percent_v6,
            v.total_addresses_v6)



def view_pool(arg, opts, shell_opts):
    """ View a single pool
    """

    res = Pool.list({ 'name': arg })

    if len(res) == 0:
        print "No pool with name '%s' found." % arg
        return

    p = res[0]

    vrf_rt = None
    vrf_name = None
    if p.vrf:
        vrf_rt = p.vrf.rt
        vrf_name = p.vrf.name

    print  "-- Pool "
    print "  %-26s : %d" % ("ID", p.id)
    print "  %-26s : %s" % ("Name", p.name)
    print "  %-26s : %s" % ("Description", p.description)
    print "  %-26s : %s" % ("Default type", p.default_type)
    print "  %-26s : %s / %s" % ("Implied VRF RT / name", vrf_rt, vrf_name)
    print "  %-26s : %s / %s" % ("Preflen (v4/v6)", str(p.ipv4_default_prefix_length), str(p.ipv6_default_prefix_length))

    print "-- Tags"
    for tag_name in sorted(p.tags, key=lambda s: s.lower()):
        print "  %s" % tag_name

    # statistics
    print "-- Statistics"
    # total / used / free prefixes
    if p.total_prefixes_v4 == 0:
        used_percent_v4 = 0
    else:
        used_percent_v4 = (float(p.used_prefixes_v4)/p.total_prefixes_v4)*100
    if p.total_prefixes_v6 == 0:
        used_percent_v6 = 0
    else:
        used_percent_v6 = (float(p.used_prefixes_v6)/p.total_prefixes_v6)*100
    print "  %-26s : %.0f / %.0f (%.2f%% of %.0f)" % ("IPv4 prefixes Used / Free",
            p.used_prefixes_v4, p.free_prefixes_v4, used_percent_v4,
            p.total_prefixes_v4)
    print "  %-26s : %.4e / %.4e (%.2f%% of %.4e)" % ("IPv6 prefixes Used / Free",
            p.used_prefixes_v6, p.free_prefixes_v6, used_percent_v6,
            p.total_prefixes_v6)

    # total / used / free addresses
    if p.total_addresses_v4 == 0:
        used_percent_v4 = 0
    else:
        used_percent_v4 = (float(p.used_addresses_v4)/p.total_addresses_v4)*100
    if p.total_addresses_v6 == 0:
        used_percent_v6 = 0
    else:
        used_percent_v6 = (float(p.used_addresses_v6)/p.total_addresses_v6)*100
    print "  %-26s : %.0f / %.0f (%.2f%% of %.0f)" % ("IPv4 addresses Used / Free",
            p.used_addresses_v4, p.free_addresses_v4, used_percent_v4,
            p.total_addresses_v4)
    print "  %-26s : %.4e / %.4e (%.2f%% of %.4e)" % ("IPv6 addresses Used / Free",
            p.used_addresses_v6, p.free_addresses_v6, used_percent_v6,
            p.total_addresses_v6)

    print "\n-- Prefixes in pool - v4: %d  v6: %d" % (p.member_prefixes_v4,
            p.member_prefixes_v6)

    res = Prefix.list({ 'pool_id': p.id})
    for pref in res:
        print "  %s" % pref.display_prefix



def view_prefix(arg, opts, shell_opts):
    """ View a single prefix.
    """

    q = { 'prefix': arg }

    v = get_vrf(opts.get('vrf_rt'), abort=True)
    if v.rt != 'all':
        q['vrf_rt'] = v.rt

    res = Prefix.list(q)

    if len(res) == 0:
        vrf_text = 'any VRF'
        if v.rt != 'all':
            vrf_text = vrf_format(v)
        print >> sys.stderr, "Address %s not found in %s." % (arg, vrf_text)
        sys.exit(1)

    p = res[0]
    vrf = p.vrf.rt

    print  "-- Address "
    print "  %-26s : %s" % ("Prefix", p.prefix)
    print "  %-26s : %s" % ("Display prefix", p.display_prefix)
    print "  %-26s : %s" % ("Type", p.type)
    print "  %-26s : IPv%s" % ("Family", p.family)
    print "  %-26s : %s" % ("VRF", vrf)
    print "  %-26s : %s" % ("Description", p.description)
    print "  %-26s : %s" % ("Node", p.node)
    print "  %-26s : %s" % ("Country", p.country)
    print "  %-26s : %s" % ("Order", p.order_id)
    print "  %-26s : %s" % ("Customer", p.customer_id)
    print "  %-26s : %s" % ("VLAN", p.vlan)
    print "  %-26s : %s" % ("Alarm priority", p.alarm_priority)
    print "  %-26s : %s" % ("Monitor", p.monitor)
    print "  %-26s : %s" % ("Added", p.added)
    print "  %-26s : %s" % ("Last modified", p.last_modified)
    if p.family == 4:
        print "  %-26s : %s / %s (%.2f%% of %s)" % ("Addresses Used / Free", p.used_addresses,
                p.free_addresses, (float(p.used_addresses)/p.total_addresses)*100,
                p.total_addresses)
    else:
        print "  %-26s : %.4e / %.4e (%.2f%% of %.4e)" % ("Addresses Used / Free", p.used_addresses,
                p.free_addresses, (float(p.used_addresses)/p.total_addresses)*100,
                p.total_addresses)
    print "-- Tags"
    for tag_name in sorted(p.tags, key=lambda s: s.lower()):
        print "  %s" % tag_name
    print "-- Inherited Tags"
    for tag_name in sorted(p.inherited_tags, key=lambda s: s.lower()):
        print "  %s" % tag_name
    print "-- Comment"
    print p.comment or ''



"""
    REMOVE FUNCTIONS
"""

def remove_vrf(arg, opts, shell_opts):
    """ Remove VRF
    """

    remove_confirmed = shell_opts.force

    res = VRF.list({ 'rt': arg })
    if len(res) < 1:
        print >> sys.stderr, "VRF with [RT: %s] not found." % arg
        sys.exit(1)

    v = res[0]

    if not remove_confirmed:
        print "RT: %s\nName: %s\nDescription: %s" % (v.rt, v.name, v.description)
        print "\nWARNING: THIS WILL REMOVE THE VRF INCLUDING ALL ITS ADDRESSES"
        res = raw_input("Do you really want to remove %s? [y/N]: " % vrf_format(v))

        if res == 'y':
            remove_confirmed = True
        else:
            print "Operation canceled."

    if remove_confirmed:
        v.remove()
        print "%s removed." % vrf_format(v)



def remove_pool(arg, opts, shell_opts):
    """ Remove pool
    """

    remove_confirmed = shell_opts.force

    res = Pool.list({ 'name': arg })
    if len(res) < 1:
        print >> sys.stderr, "No pool with name '%s' found." % arg
        sys.exit(1)

    p = res[0]

    if not remove_confirmed:
        res = raw_input("Do you really want to remove the pool '%s'? [y/N]: " % p.name)

        if res == 'y':
            remove_confirmed = True
        else:
            print "Operation canceled."

    if remove_confirmed:
        p.remove()
        print "Pool '%s' removed." % p.name


def remove_prefix(arg, opts, shell_opts):
    """ Remove prefix
    """

    # set up some basic variables
    remove_confirmed = shell_opts.force
    auth_src = set()
    recursive = False

    if opts.get('recursive') is True:
        recursive = True

    spec = { 'prefix': arg }
    v = get_vrf(opts.get('vrf_rt'), abort=True)
    if v.rt != 'all':
        spec['vrf_rt'] = v.rt

    res = Prefix.list(spec)

    if len(res) < 1:
        vrf_text = 'any VRF'
        if v.rt != 'all':
            vrf_text = vrf_format(v)
        print >> sys.stderr, "Prefix %s not found in %s." % (arg, vrf_text)
        sys.exit(1)

    p = res[0]

    if p.authoritative_source != 'nipap':
        auth_src.add(p.authoritative_source)

    if not remove_confirmed:
        if recursive is True or p.type == 'assignment':
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

            # if recursive is False, this delete will fail, ask user to do recursive
            # delete instead
            if recursive is False:
                if len(pres['result']) > 1:
                    print "WARNING: %s in %s contains %s hosts." % (p.prefix, vrf_format(p.vrf), len(pres['result']))
                    res = raw_input("Would you like to recursively delete %s and all hosts? [y/N]: " % (p.prefix))
                    if res.lower() in [ 'y', 'yes' ]:
                        recursive = True
                    else:
                        print >> sys.stderr, "ERROR: Removal of assignment containing hosts is prohibited. Aborting removal of %s in %s." % (p.prefix, vrf_format(p.vrf))
                        sys.exit(1)

        if recursive is True:
            if len(pres['result']) <= 1:
                res = raw_input("Do you really want to remove the prefix %s in %s? [y/N]: " % (p.prefix, vrf_format(p.vrf)))

                if res.lower() in [ 'y', 'yes' ]:
                    remove_confirmed = True

            else:
                print "Recursively deleting %s in %s will delete the following prefixes:" % (p.prefix, vrf_format(p.vrf))

                # Iterate prefixes to print a few of them and check the prefixes'
                # authoritative source
                i = 0
                for rp in pres['result']:
                    if i <= 10:
                        print "%-29s %-2s %-19s %-14s %-14s %-40s" % ("".join("  " for i in
                            range(rp.indent)) + rp.display_prefix,
                            rp.type[0].upper(), rp.node, rp.order_id,
                            rp.customer_id, rp.description)

                    if i == 10:
                        print ".. and %s other prefixes" % (len(pres['result']) - 10)

                    if rp.authoritative_source != 'nipap':
                        auth_src.add(rp.authoritative_source)

                    i += 1

                if len(auth_src) == 0:
                    # Simple case; all prefixes were added from NIPAP
                    res = raw_input("Do you really want to recursively remove %s prefixes in %s? [y/N]: " % (len(pres['result']),
                                vrf_format(vrf)))

                    if res.lower() in [ 'y', 'yes' ]:
                        remove_confirmed = True

                else:
                    # we have prefixes with authoritative source != nipap
                    auth_src = list(auth_src)
                    plural = ""

                    # format prompt depending on how many different sources we have
                    if len(auth_src) == 1:
                        systems = "'%s'" % auth_src[0]
                        prompt = "Enter the name of the managing system to continue or anything else to abort: "

                    else:
                        systems = ", ".join("'%s'" % x for x in auth_src[1:]) + " and '%s'" % auth_src[0]
                        plural = "s"
                        prompt = "Enter the name of the last managing system to continue or anything else to abort: "

                    print ("Prefix %s in %s contains prefixes managed by the system%s %s. " +
                        "Are you sure you want to remove them? ") % (p.prefix,
                                vrf_format(p.vrf), plural, systems)
                    res = raw_input(prompt)

                    # Did the user provide the correct answer?
                    if res.lower() == auth_src[0].lower():
                        remove_confirmed = True
                    else:
                        print >> sys.stderr, "System names did not match."
                        sys.exit(1)

        else:
            # non recursive delete
            if len(auth_src) > 0:
                auth_src = list(auth_src)
                print ("Prefix %s in %s is managed by the system '%s'. " +
                    "Are you sure you want to remove it? ") % (p.prefix,
                            vrf_format(p.vrf), auth_src[0])
                res = raw_input("Enter the name of the managing system to continue or anything else to abort: ")

                if res.lower() == auth_src[0].lower():
                    remove_confirmed = True

                else:
                    print >> sys.stderr, "System names did not match."
                    sys.exit(1)

            else:
                res = raw_input("Do you really want to remove the prefix %s in %s? [y/N]: " % (p.prefix, vrf_format(p.vrf)))
                if res.lower() in [ 'y', 'yes' ]:
                    remove_confirmed = True

    if remove_confirmed is True:
        p.remove(recursive = recursive)
        if recursive is True:
            print "Prefix %s and %s other prefixes in %s removed." % (p.prefix,
                    (len(pres['result']) - 1), vrf_format(p.vrf))
        else:
            print "Prefix %s in %s removed." % (p.prefix, vrf_format(p.vrf))

    else:
        print "Operation canceled."


"""
    MODIFY FUNCTIONS
"""

def modify_vrf(arg, opts, shell_opts):
    """ Modify a VRF with the options set in opts
    """

    res = VRF.list({ 'rt': arg })
    if len(res) < 1:
        print >> sys.stderr, "VRF with [RT: %s] not found." % arg
        sys.exit(1)

    v = res[0]

    if 'rt' in opts:
        v.rt = opts['rt']
    if 'name' in opts:
        v.name = opts['name']
    if 'description' in opts:
        v.description = opts['description']
    if 'tags' in opts:
        tags = list(csv.reader([opts.get('tags', '')], escapechar='\\'))[0]
        v.tags = {}
        for tag_name in tags:
            tag = Tag()
            tag.name = tag_name
            v.tags[tag_name] = tag

    v.save()

    print "%s saved." % vrf_format(v)



def modify_pool(arg, opts, shell_opts):
    """ Modify a pool with the options set in opts
    """

    res = Pool.list({ 'name': arg })
    if len(res) < 1:
        print >> sys.stderr, "No pool with name '%s' found." % arg
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
    if 'tags' in opts:
        tags = list(csv.reader([opts.get('tags', '')], escapechar='\\'))[0]
        p.tags = {}
        for tag_name in tags:
            tag = Tag()
            tag.name = tag_name
            p.tags[tag_name] = tag

    p.save()

    print "Pool '%s' saved." % p.name



def grow_pool(arg, opts, shell_opts):
    """ Expand a pool with the ranges set in opts
    """
    if not pool:
        print >> sys.stderr, "No pool with name '%s' found." % arg
        sys.exit(1)

    if not 'add' in opts:
        print >> sys.stderr, "Please supply a prefix to add to pool '%s'" % pool.name
        sys.exit(1)

    # Figure out VRF.
    # If pool already has a member prefix, implied_vrf will be set. Look for new
    # prefix to add in the same vrf as implied_vrf.
    # If pool has no members, then use get_vrf() to get vrf to search in for
    # prefix to add.
    if pool.vrf is not None:
        v = pool.vrf
    else:
        v = get_vrf(opts.get('vrf_rt'), abort=True)

    q = { 'prefix': opts['add'] }
    if v.rt != 'all':
        q['vrf_rt'] = v.rt

    res = Prefix.list(q)

    if len(res) == 0:
        print >> sys.stderr, "No prefix found matching %s in %s." % (opts['add'], vrf_format(v))
        sys.exit(1)
    elif res[0].pool:
        if res[0].pool == pool:
            print >> sys.stderr, "Prefix %s in %s is already assigned to that pool." % (opts['add'], vrf_format(v))
        else:
            print >> sys.stderr, "Prefix %s in %s is already assigned to a different pool ('%s')." % (opts['add'], vrf_format(v), res[0].pool.name)
        sys.exit(1)

    res[0].pool = pool
    res[0].save()
    print "Prefix %s in %s added to pool '%s'." % (res[0].prefix, vrf_format(v), pool.name)



def shrink_pool(arg, opts, shell_opts):
    """ Shrink a pool by removing the ranges in opts from it
    """
    if not pool:
        print >> sys.stderr, "No pool with name '%s' found." % arg
        sys.exit(1)

    if 'remove' in opts:
        res = Prefix.list({'prefix': opts['remove'], 'pool_id': pool.id})

        if len(res) == 0:
            print >> sys.stderr, "Pool '%s' does not contain %s." % (pool.name,
                opts['remove'])
            sys.exit(1)

        res[0].pool = None
        res[0].save()
        print "Prefix %s removed from pool '%s'." % (res[0].prefix, pool.name)
    else:
        print >> sys.stderr, "Please supply a prefix to add or remove to '%s':" % (
            pool.name)
        for pref in Prefix.list({'pool_id': pool.id}):
            print "  %s" % pref.prefix



def modify_prefix(arg, opts, shell_opts):
    """ Modify the prefix 'arg' with the options 'opts'
    """

    modify_confirmed = shell_opts.force

    spec = { 'prefix': arg }
    v = get_vrf(opts.get('vrf_rt'), abort=True)
    spec['vrf_rt'] = v.rt

    res = Prefix.list(spec)
    if len(res) == 0:
        print >> sys.stderr, "Prefix %s not found in %s." % (arg, vrf_format(v))
        return

    p = res[0]

    if 'prefix' in opts:
        p.prefix = opts['prefix']
    if 'description' in opts:
        p.description = opts['description']
    if 'comment' in opts:
        p.comment = opts['comment']
    if 'tags' in opts:
        tags = list(csv.reader([opts.get('tags', '')], escapechar='\\'))[0]
        p.tags = {}
        for tag_name in tags:
            tag = Tag()
            tag.name = tag_name
            p.tags[tag_name] = tag
    if 'node' in opts:
        p.node = opts['node']
    if 'type' in opts:
        p.type = opts['type']
    if 'country' in opts:
        p.country = opts['country']
    if 'order_id' in opts:
        p.order_id = opts['order_id']
    if 'customer_id' in opts:
        p.customer_id = opts['customer_id']
    if 'vlan' in opts:
        p.vlan = opts['vlan']
    if 'alarm_priority' in opts:
        p.alarm_priority = opts['alarm_priority']
    if 'monitor' in opts:
        p.monitor = _str_to_bool(opts['monitor'])

    # Promt user if prefix has authoritative source != nipap
    if not modify_confirmed and p.authoritative_source.lower() != 'nipap':

        res = raw_input("Prefix %s in %s is managed by system '%s'. Are you sure you want to modify it? [y/n]: " %
            (p.prefix, vrf_format(p.vrf), p.authoritative_source))

        # If the user declines, short-circuit...
        if res.lower() not in [ 'y', 'yes' ]:
            print "Operation aborted."
            return

    try:
        p.save()
    except NipapError as exc:
        print >> sys.stderr, "Could not save prefix changes: %s" % str(exc)
        sys.exit(1)

    print "Prefix %s in %s saved." % (p.display_prefix, vrf_format(p.vrf))



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



def complete_tags(arg):
    """ Complete NIPAP prefix type
    """
    search_string = '^'
    if arg is not None:
        search_string += arg

    res = Tag.search({
        'operator': 'regex_match',
        'val1': 'name',
        'val2': search_string
    })

    ret = []
    for t in res['result']:
        ret.append(t.name)

    return ret



def complete_pool_members(arg):
    """ Complete member prefixes of pool
    """
    # pool should already be globally set
    res = []
    for member in Prefix.list({ 'pool_id': pool.id }):
        res.append(member.prefix)

    return _complete_string(arg, res)



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
        }, { 'max_result': 100000 } )

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
                        'order_id': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                            }
                        },
                        'customer_id': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                            }
                        },
                        'tags': {
                            'type': 'option',
                            'content_type': unicode,
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                                'complete': complete_tags,
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
                        'vlan': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': int
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
                                'order_id': {
                                    'type': 'option',
                                    'argument': {
                                        'type': 'value',
                                        'content_type': unicode,
                                    }
                                },
                                'customer_id': {
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
                                'tags': {
                                    'type': 'option',
                                    'content_type': unicode,
                                    'argument': {
                                        'type': 'value',
                                        'content_type': unicode,
                                        'complete': complete_tags,
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
                                'vlan': {
                                    'type': 'option',
                                    'argument': {
                                        'type': 'value',
                                        'content_type': int
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
                        },
                        'tags': {
                            'type': 'option',
                            'content_type': unicode,
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                                'complete': complete_tags,
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
                                },
                                'tags': {
                                    'type': 'option',
                                    'content_type': unicode,
                                    'argument': {
                                        'type': 'value',
                                        'content_type': unicode,
                                        'complete': complete_tags,
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
                        },
                        'tags': {
                            'type': 'option',
                            'content_type': unicode,
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                                'complete': complete_tags,
                            }
                        }
                    }
                },

                # list
                'list': {
                    'type': 'command',
                    'exec': list_pool,
                    'rest_argument': {
                        'type': 'value',
                        'content_type': unicode,
                        'description': 'Pool',
                    },
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
                        },
                        'vrf_rt': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                                'descripton': 'The implied VRF of the pool',
                                'complete': complete_vrf_virtual
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

                # resize
                'resize': {
                    'type': 'command',
                    'exec_immediately': get_pool,
                    'argument': {
                        'type': 'value',
                        'content_type': unicode,
                        'description': 'Pool name',
                        'complete': complete_pool_name,
                    },
                    'children': {
                        'add': {
                            'type': 'option',
                            'exec': grow_pool,
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
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
                        },
                        'remove': {
                            'type': 'option',
                            'exec': shrink_pool,
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                                'complete': complete_pool_members,
                            }
                        }
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
                                },
                                'tags': {
                                    'type': 'option',
                                    'content_type': unicode,
                                    'argument': {
                                        'type': 'value',
                                        'content_type': unicode,
                                        'complete': complete_tags,
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
    except ValueError as exc:
        print >> sys.stderr, "Error: %s" % str(exc)
        sys.exit(1)

    # execute command
    if cmd.exe is None:
        print "Incomplete command specified"
        print "valid completions: %s" % " ".join(cmd.next_values())
        sys.exit(1)

    try:
        cmd.exe(cmd.arg, cmd.exe_options)
    except NipapError as exc:
        print >> sys.stderr, "Command failed:\n  %s" % str(exc)
        sys.exit(1)

