#!/usr/bin/env python3
""" NIPAP shell command

    A shell command to interact with NIPAP.
"""

from __future__ import print_function

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

import csv
import os
import pipes
import re
import shlex
import string
import subprocess
import sys

import IPy

import pynipap
from pynipap import Pool, Prefix, Tag, VRF, NipapError
from .command import Command


# definitions
valid_countries = [
    'AT', 'DE', 'DK', 'EE', 'FI', 'FR',
    'GB', 'HR', 'LT', 'LV', 'KZ', 'NL',
    'RU', 'SE', 'US' ] # test test, fill up! :)
valid_prefix_types = [ 'host', 'reservation', 'assignment' ]
valid_prefix_status = [ 'assigned', 'reserved', 'quarantine' ]
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

    # get connection parameters, first from environment variables if they are
    # defined, otherwise from .nipaprc
    try:
        con_params = {
            'username': os.getenv('NIPAP_USERNAME') or cfg.get('global', 'username'),
            'password': os.getenv('NIPAP_PASSWORD') or cfg.get('global', 'password'),
            'hostname': os.getenv('NIPAP_HOST') or cfg.get('global', 'hostname'),
            'port'    : os.getenv('NIPAP_PORT') or cfg.get('global', 'port')
        }
    except (configparser.NoOptionError, configparser.NoSectionError) as exc:
        print("ERROR:", str(exc), file=sys.stderr)
        print("HINT: Please define the username, password, hostname and port in your .nipaprc under the section 'global' or provide them through the environment variables NIPAP_HOST, NIPAP_PORT, NIPAP_USERNAME and NIPAP_PASSWORD.", file=sys.stderr)
        sys.exit(1)

    # if we haven't got a password (from env var or config) we interactively
    # prompt for one
    if con_params['password'] is None:
        import getpass
        con_params['password'] = getpass.getpass()

    # build XML-RPC URI
    pynipap.xmlrpc_uri = "http://{username!s}:{password!s}@{hostname!s}:{port!s}".format(**con_params)

    ao = pynipap.AuthOptions({
        'authoritative_source': 'nipap',
        'username': os.getenv('NIPAP_IMPERSONATE_USERNAME') or con_params['username'],
        'full_name': os.getenv('NIPAP_IMPERSONATE_FULL_NAME'),
        })



def vrf_format(vrf):
    return "VRF '{0!s}' [RT: {1!s}]".format(vrf.name, vrf.rt or '-')


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
            print("Pool '{0!s}' not found.".format(str(arg)), file=sys.stderr)
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
        except configparser.NoOptionError:
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
                print("VRF with [RT: {0!s}] not found.".format(str(vrf_rt)), file=sys.stderr)
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
def _parse_interp_pool(query, indent=-5, pandop=False):
    if 'interpretation' not in query:
        return
    interp = query['interpretation']
    text = None
    text2 = None
    andop = False

    # "Major" parser error, unable to parse string
    if interp.get('error') is True and interp['operator'] is None:

        if interp['error_message'] == 'unclosed quote':
            text = "{0!s}: {1!s}, please close quote!".format(interp['string'], interp['error_message'])
            text2 = "This is not a proper search term as it contains an uneven amount of quotes."

        elif interp['error_message'] == 'unclosed parentheses':
            text = "{0!s}: {1!s}, please close parentheses!".format(interp['string'], interp['error_message'])
            text2 = "This is not a proper search term as it contains an uneven amount of parentheses."

    elif interp['operator'] in ['and', 'or']:
        andop = True

    elif interp['attribute'] == 'tag' and interp['operator'] == 'equals_any':
        text = "{0!s}: {1!s} must contain {2!s}".format(interp['string'], interp['interpretation'], interp['string'][1:])
        text2 = "The tag(s) or inherited tag(s) must contain {0!s}".format(interp['string'][1:])

    else:
        text = "{0!s}: {1!s} matching {2!s}".format(interp['string'], interp['interpretation'], interp['string'])

    # "Minor" error messages, string could be parsed but contain errors
    if interp.get('error') is True and interp['operator'] is not None: # .get() for backwards compatibiliy
        if interp['error_message'] == 'invalid value':
            text += ": invalid value!"
            text2 = "The value provided is not valid for the attribute '{0!s}'.".format(interp['attribute'])

        elif interp['error_message'] == 'unknown attribute':
            text += ": unknown attribute '{0!s}'!".format(interp['attribute'])
            text2 = "There is no pool attribute '{0!s}'.".format(interp['attribute'])

        else:
            text += ": {0!s}, invalid query".format(interp['error_message'])
            text2 = "This is not a proper search query."

    if text:
        if pandop:
            a = '     '
            if indent > 1:
                a = ' `-- '
            print("{ind}{a}AND-- {t}".format(ind=' '*indent, a=a, t=text))
        else:
            print("{0!s}       `-- {1!s}".format(' '*indent, text))
    if text2:
        print("{0!s}   {1!s}".format(' '*indent, text2))
    if type(query['val1']) is dict:
        _parse_interp_pool(query['val1'], indent+6, andop)
    if type(query['val2']) is dict:
        _parse_interp_pool(query['val2'], indent+6)


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
            if shell_opts.show_interpretation:
                print("Query interpretation:")
                _parse_interp_pool(res['interpretation'])

            if res['error']:
                print("Query failed: {0!s}".format(res['error_message']))
                return

            if len(res['result']) == 0:
                print("No matching pools found")
                return

            print("{0:<19!s} {1:<2!s} {2:<39!s} {3:<13!s}  {4:<8!s} {5!s}".format(
                "Name", "#", "Description", "Default type", "4 / 6", "Implied VRF"
                ))
            print("------------------------------------------------------------------------------------------------")

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
                tags = "#{0:d}".format((len(p.tags)))

            print("{0:<19!s} {1:<2!s} {2:<39!s} {3:<13!s} {4:<2!s} / {5:<3!s}  [RT: {6!s}] {7!s}".format(
                p.name, tags, desc, p.default_type,
                str(p.ipv4_default_prefix_length or '-'),
                str(p.ipv6_default_prefix_length or '-'),
                vrf_rt, vrf_name
            ))
        if len(res['result']) < limit:
            break
        offset += limit


def _parse_interp_vrf(query, indent=-5, pandop=False):
    if 'interpretation' not in query:
        return
    interp = query['interpretation']
    text = None
    text2 = None
    andop = False

    # "Major" parser error, unable to parse string
    if interp.get('error') is True and interp['operator'] is None:

        if interp['error_message'] == 'unclosed quote':
            text = "{0!s}: {1!s}, please close quote!".format(interp['string'], interp['error_message'])
            text2 = "This is not a proper search term as it contains an uneven amount of quotes."

        elif interp['error_message'] == 'unclosed parentheses':
            text = "{0!s}: {1!s}, please close parentheses!".format(interp['string'], interp['error_message'])
            text2 = "This is not a proper search term as it contains an uneven amount of parentheses."

    elif interp['operator'] in ['and', 'or']:
        andop = True

    elif interp['attribute'] == 'tag' and interp['operator'] == 'equals_any':
        text = "{0!s}: {1!s} must contain {2!s}".format(interp['string'], interp['interpretation'], interp['string'][1:])
        text2 = "The tag(s) or inherited tag(s) must contain {0!s}".format(interp['string'][1:])

    else:
        text = "{0!s}: {1!s} matching {2!s}".format(interp['string'], interp['interpretation'], interp['string'])

    # "Minor" error messages, string could be parsed but contain errors
    if interp.get('error') is True and interp['operator'] is not None: # .get() for backwards compatibiliy
        if interp['error_message'] == 'invalid value':
            text += ": invalid value!"
            text2 = "The value provided is not valid for the attribute '{0!s}'.".format(interp['attribute'])

        elif interp['error_message'] == 'unknown attribute':
            text += ": unknown attribute '{0!s}'!".format(interp['attribute'])
            text2 = "There is no pool attribute '{0!s}'.".format(interp['attribute'])

        else:
            text += ": {0!s}, invalid query".format(interp['error_message'])
            text2 = "This is not a proper search query."

    if text:
        if pandop:
            a = '     '
            if indent > 1:
                a = ' `-- '
            print("{ind}{a}AND-- {t}".format(ind=' '*indent, a=a, t=text))
        else:
            print("{0!s}       `-- {1!s}".format(' '*indent, text))
    if text2:
        print("{0!s}   {1!s}".format(' '*indent, text2))
    if type(query['val1']) is dict:
        _parse_interp_vrf(query['val1'], indent+6, andop)
    if type(query['val2']) is dict:
        _parse_interp_vrf(query['val2'], indent+6)

def list_vrf(arg, opts, shell_opts):
    """ List VRFs matching a search criteria
    """

    search_string = ''
    if type(arg) == list or type(arg) == tuple:
        search_string = ' '.join(arg)

    offset = 0
    limit = 100
    while True:
        res = VRF.smart_search(search_string, { 'offset': offset, 'max_result': limit })
        if offset == 0:
            if shell_opts.show_interpretation:
                print("Query interpretation:")
                _parse_interp_vrf(res['interpretation'])

            if res['error']:
                print("Query failed: {0!s}".format(res['error_message']))
                return

            if len(res['result']) == 0:
                print("No VRFs matching '{0!s}' found.".format(search_string))
                return

            print("{0:<16!s} {1:<22!s} {2:<2!s} {3:<40!s}".format("VRF RT", "Name", "#", "Description"))
            print("--------------------------------------------------------------------------------")

        for v in res['result']:
            tags = '-'
            if len(v.tags) > 0:
                tags = '#{0:d}'.format(len(v.tags))
            if len(str(v.description)) > 100:
                desc = v.description[0:97] + "..."
            else:
                desc = v.description
            print("{0:<16!s} {1:<22!s} {2:<2!s} {3:<40!s}".format(v.rt or '-', v.name, tags, desc))

        if len(res['result']) < limit:
            break
        offset += limit


def _parse_interp_prefix(query, indent=-5, pandop=False):
    if 'interpretation' not in query:
        return
    interp = query['interpretation']
    text = None
    text2 = None
    andop = False

    # "Major" parser error, unable to parse string
    if interp.get('error') is True and interp['operator'] is None:

        if interp['error_message'] == 'unclosed quote':
            text = "{0!s}: {1!s}, please close quote!".format(interp['string'], interp['error_message'])
            text2 = "This is not a proper search term as it contains an uneven amount of quotes."

        elif interp['error_message'] == 'unclosed parentheses':
            text = "{0!s}: {1!s}, please close parentheses!".format(interp['string'], interp['error_message'])
            text2 = "This is not a proper search term as it contains an uneven amount of parentheses."

    elif interp['operator'] in ['and', 'or']:
        andop = True

    elif interp['attribute'] == 'tag' and interp['operator'] == 'equals_any':
        text = "{0!s}: {1!s} must contain {2!s}".format(interp['string'], interp['interpretation'], interp['string'][1:])
        text2 = "The tag(s) or inherited tag(s) must contain {0!s}".format(interp['string'][1:])

    elif interp['attribute'] == 'prefix' and interp['operator'] == 'contained_within_equals':
        if 'strict_prefix' in interp and 'expanded' in interp:
            text = "{0!s}: {1!s} within {2!s}".format(interp['string'],
                    interp['interpretation'],
                    interp['strict_prefix'])
            text2 = "Prefix must be contained within {0!s}, which is the base prefix of {1!s} (automatically expanded from {2!s}).".format(interp['strict_prefix'], interp['expanded'], interp['string'])

        elif 'strict_prefix' in interp:
            text = "{0!s}: {1!s} within {2!s}".format(interp['string'],
                    interp['interpretation'],
                    interp['strict_prefix'])
            text2 = "Prefix must be contained within {0!s}, which is the base prefix of {1!s}.".format(interp['strict_prefix'], interp['string'])

        elif 'expanded' in interp:
            text = "{0!s}: {1!s} within {2!s}".format(interp['string'],
                    interp['interpretation'],
                    interp['expanded'])
            text2 = "Prefix must be contained within {0!s} (automatically expanded from {1!s}).".format(interp['expanded'], interp['string'])
        else:
            text = "{0!s}: {1!s} within {2!s}".format(interp['string'],
                    interp['interpretation'],
                    interp['string'])
            text2 = "Prefix must be contained within {0!s}.".format((interp['string']))

    elif interp['attribute'] == 'prefix' and interp['operator'] == 'contains_equals':
        text = "{0!s}: Prefix that contains {1!s}".format(interp['string'],
                interp['string'])

    elif interp['attribute'] == 'prefix' and interp['operator'] == 'contains_equals':
        text = "{0!s}: {1!s} equal to {2!s}".format(interp['string'],
                interp['interpretation'], interp['string'])

    else:
        text = "{0!s}: {1!s} matching {2!s}".format(interp['string'], interp['interpretation'], interp['string'])

    # "Minor" error messages, string could be parsed but contain errors
    if interp.get('error') is True and interp['operator'] is not None: # .get() for backwards compatibiliy
        if interp['error_message'] == 'invalid value':
            text += ": invalid value!"
            text2 = "The value provided is not valid for the attribute '{0!s}'.".format(interp['attribute'])

        elif interp['error_message'] == 'unknown attribute':
            text += ": unknown attribute '{0!s}'!".format(interp['attribute'])
            text2 = "There is no prefix attribute '{0!s}'.".format(interp['attribute'])

        else:
            text += ": {0!s}, invalid query".format(interp['error_message'])
            text2 = "This is not a proper search query."

    if text:
        if pandop:
            a = '     '
            if indent > 1:
                a = ' `-- '
            print("{ind}{a}AND-- {t}".format(ind=' '*indent, a=a, t=text))
        else:
            print("{0!s}       `-- {1!s}".format(' '*indent, text))
    if text2:
        print("{0!s}   {1!s}".format(' '*indent, text2))
    if type(query['val1']) is dict:
        _parse_interp_prefix(query['val1'], indent+6, andop)
    if type(query['val2']) is dict:
        _parse_interp_prefix(query['val2'], indent+6)


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
    print("Searching for prefixes in {0!s}...".format(vrf_text))

    col_def = {
            'added': { 'title': 'Added' },
            'alarm_priority': { 'title': 'Alarm Prio' },
            'authoritative_source': { 'title': 'Auth source' },
            'children': { 'title': 'Children' },
            'comment': { 'title': 'Comment' },
            'customer_id': { 'title': 'Customer ID' },
            'description': { 'title': 'Description' },
            'expires': { 'title': 'Expires' },
            'free_addresses': { 'title': 'Free addresses' },
            'monitor': { 'title': 'Monitor' },
            'last_modified': { 'title': 'Last mod' },
            'node': { 'title': 'Node' },
            'order_id': { 'title': 'Order ID' },
            'pool_name': { 'title': 'Pool name' },
            'prefix': { 'title': 'Prefix' },
            'status': { 'title': 'Status' },
            'tags': { 'title': '#' },
            'total_addresses': { 'title': 'Total addresses' },
            'type': { 'title': '' },
            'used_addresses': { 'title': 'Used addresses' },
            'vlan': { 'title': 'VLAN' },
            'vrf_rt': { 'title': 'VRF RT' },
            }
    # default columns
    columns = [ 'vrf_rt', 'prefix', 'type', 'tags', 'node', 'order_id', 'customer_id', 'description' ]

    # custom columns? prefer shell opts, then look in config file
    custom_columns = None
    if shell_opts.columns and len(shell_opts.columns) > 0:
        custom_columns = shell_opts.columns
    elif cfg.get('global', 'prefix_list_columns'):
        custom_columns = cfg.get('global', 'prefix_list_columns')

    # parse custom columns
    if custom_columns:
        # should we append columns or replace default?
        if custom_columns[0] == '+':
            col_append = True
        else:
            col_append = False
            columns = []

        # read in custom columns
        for col in list(csv.reader([custom_columns.lstrip('+') or ''], escapechar='\\'))[0]:
            col = col.strip()
            if col not in col_def:
                print("Invalid column:", col, file=sys.stderr)
                sys.exit(1)
            columns.append(col)

    offset = 0
    # small initial limit for "instant" result
    limit = 50
    prefix_str = ""
    while True:
        res = Prefix.smart_search(search_string, { 'parents_depth': -1,
            'include_neighbors': True, 'offset': offset, 'max_result': limit },
            vrf_q)

        if offset == 0: # first time in loop?
            if shell_opts.show_interpretation:
                print("Query interpretation:")
                _parse_interp_prefix(res['interpretation'])

            if res['error']:
                print("Query failed: {0!s}".format(res['error_message']))
                return

            if len(res['result']) == 0:
                print("No addresses matching '{0!s}' found.".format(search_string))
                return

            # guess column width by looking at the initial result set
            for p in res['result']:
                for colname, col in col_def.items():
                    val = getattr(p, colname, '')
                    col['width'] = max(len(colname), col.get('width', 0),
                                       len(str(val)))

                # special handling of a few columns
                col_def['vrf_rt']['width'] = max(col_def['vrf_rt'].get('width', 8),
                                                 len(str(p.vrf.rt)))
                col_def['prefix']['width'] = max(col_def['prefix'].get('width', 0)-12,
                                                 p.indent * 2 + len(p.prefix)) + 12
                try:
                    col_def['pool_name']['width'] = max(col_def['pool_name'].get('width', 8),
                                                        len(str(p.pool.name)))
                except:
                    pass
            # override certain column widths
            col_def['type']['width'] = 1
            col_def['tags']['width'] = 2

            col_header_data = {}
            # build prefix formatting string
            for colname, col in [(k, col_def[k]) for k in columns]:
                prefix_str += "{{{0!s}:<{1:d}}}  ".format(colname, col['width'])
                col_header_data[colname] = col['title']

            column_header = prefix_str.format(**col_header_data)
            print(column_header)
            print("".join("=" for i in range(len(column_header))))

        for p in res['result']:
            if p.display == False:
                continue

            col_data = {}
            try:
                for colname, col in col_def.items():
                    col_data[colname] = str(getattr(p, colname, None))

                # overwrite some columns due to special handling
                col_data['tags'] = '-'
                if len(p.tags) > 0:
                    col_data['tags'] = '#{0:d}'.format(len(p.tags))

                try: 
                    col_data['pool_name'] = p.pool.name
                except:
                    pass

                col_data['prefix'] = "".join("  " for i in range(p.indent)) + p.display_prefix
                col_data['type'] = p.type[0].upper()
                col_data['vrf_rt'] = p.vrf.rt or '-'

                print(prefix_str.format(**col_data))

            except UnicodeEncodeError as e:
                print("\nCrazy encoding for prefix {0!s}\n".format(p.prefix), file=sys.stderr)

        if len(res['result']) < limit:
            break
        offset += limit

        # let consecutive limit be higher to tax the XML-RPC backend less
        limit = 200




"""
    ADD FUNCTIONS
"""
def _prefix_from_opts(opts):
    """ Return a prefix based on options passed from command line

        Used by add_prefix() and add_prefix_from_pool() to avoid duplicate
        parsing
    """
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
    p.status = opts.get('status') or 'assigned' # default to assigned
    p.tags = list(csv.reader([opts.get('tags', '')], escapechar='\\'))[0]
    p.expires = opts.get('expires')
    return p



def add_prefix(arg, opts, shell_opts):
    """ Add prefix to NIPAP
    """

    # sanity checks
    if 'from-pool' not in opts and 'from-prefix' not in opts and 'prefix' not in opts:
        print("ERROR: 'prefix', 'from-pool' or 'from-prefix' must be specified.", file=sys.stderr)
        sys.exit(1)

    if len([opt for opt in opts if opt in ['from-pool', 'from-prefix', 'prefix']]) > 1:
        print("ERROR: Use either assignment 'from-pool', 'from-prefix' or manual mode (using 'prefix')", file=sys.stderr)
        sys.exit(1)

    if 'from-pool' in opts:
        return add_prefix_from_pool(arg, opts)

    args = {}
    p = _prefix_from_opts(opts)
    p.vrf = get_vrf(opts.get('vrf_rt'), abort=True)

    for avp in opts.get('extra-attribute', []):
        try:
            key, value = avp.split('=', 1)
        except ValueError:
            print("ERROR: Incorrect extra-attribute: {0!s}. Accepted form: 'key=value'\n".format(avp), file=sys.stderr)
            return
        p.avps[key] = value

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
            print("ERROR: dual-stack mode only valid for from-pool assignments", file=sys.stderr)
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
        # If no prefix length is specified it is assumed to be a host and we do
        # a search for prefixes that contains the specified prefix. The last
        # entry will be the parent of the new prefix and we can look at it to
        # determine type.
        # If prefix length is specified (i.e. CIDR format) we check if prefix
        # length equals max length in which case we assume a host prefix,
        # otherwise we search for the network using an equal match and by
        # zeroing out bits in the host part.
        if len(opts.get('prefix').split("/")) == 2:
            ip = IPy.IP(opts.get('prefix').split("/")[0])
            plen = int(opts.get('prefix').split("/")[1])
            if ip.version() == 4 and plen == 32 or ip.version() == 6 and plen == 128:
                parent_prefix = str(ip)
                parent_op = 'contains'
            else:
                parent_prefix = str(IPy.IP(opts.get('prefix'), make_net=True))
                parent_op = 'equals'
        else:
            parent_prefix = opts.get('prefix')
            parent_op = 'contains'

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
            print("ERROR: Type of prefix must be specified ('assignment' or 'reservation').", file=sys.stderr)
            sys.exit(1)
    else:
        # last prefix in list will be the parent of the new prefix
        parent = res['result'][-1]

        # if the parent is an assignment, we can assume the new prefix to be
        # a host and act accordingly
        if parent.type == 'assignment':
            # automatically set type
            if p.type is None:
                print("WARNING: Parent prefix is of type 'assignment'. Automatically setting type 'host' for new prefix.", file=sys.stderr)
            elif p.type == 'host':
                pass
            else:
                print("WARNING: Parent prefix is of type 'assignment'. Automatically overriding specified type '{0!s}' with type 'host' for new prefix.".format(p.type), file=sys.stderr)
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
        print("Could not add prefix to NIPAP: {0!s}".format(str(exc)), file=sys.stderr)
        sys.exit(1)

    if p.type == 'host':
        print("Host {0!s} added to {1!s}: {2!s}".format(p.display_prefix,
                vrf_format(p.vrf), p.node or p.description))
    else:
        print("Network {0!s} added to {1!s}: {2!s}".format(p.display_prefix,
                vrf_format(p.vrf), p.description))

    if opts.get('add-hosts') is not None:
        if p.type != 'assignment':
            print("ERROR: Not possible to add hosts to non-assignment", file=sys.stderr)
            sys.exit(1)

        for host in opts.get('add-hosts').split(','):
            h_opts = {
                    'from-prefix': p.prefix,
                    'vrf_rt': p.vrf.rt,
                    'type': 'host',
                    'node': host
                    }
            add_prefix({}, h_opts, {})



def add_prefix_from_pool(arg, opts):
    """ Add prefix using from-pool to NIPAP
    """

    args = {}

    # sanity checking
    if 'from-pool' in opts:
        res = Pool.list({ 'name': opts['from-pool'] })
        if len(res) == 0:
            print("No pool named '{0!s}' found.".format(opts['from-pool']), file=sys.stderr)
            sys.exit(1)

        args['from-pool'] = res[0]

    if 'family' not in opts:
        print("ERROR: You have to specify the address family.", file=sys.stderr)
        sys.exit(1)

    if opts['family'] == 'ipv4':
        afis = [4]
    elif opts['family'] == 'ipv6':
        afis = [6]
    elif opts['family'] == 'dual-stack':
        afis = [4, 6]
        if 'prefix_length' in opts:
            print("ERROR: 'prefix_length' can not be specified for 'dual-stack' assignment", file=sys.stderr)
            sys.exit(1)
    else:
        print("ERROR: 'family' must be one of: {0!s}".format(" ".join(valid_families)), file=sys.stderr)
        sys.exit(1)

    if 'prefix_length' in opts:
        args['prefix_length'] = int(opts['prefix_length'])

    for afi in afis:
        p = _prefix_from_opts(opts)

        if opts.get('vrf_rt') is None:
            # if no VRF is specified use the pools implied VRF
            p.vrf = args['from-pool'].vrf
        else:
            # use the specified VRF
            p.vrf = get_vrf(opts.get('vrf_rt'), abort=True)

        # set type to default type of pool unless already set
        if p.type is None:
            if args['from-pool'].default_type is None:
                print("ERROR: Type not specified and no default-type specified for pool: {0!s}".format(opts['from-pool']), file=sys.stderr)
            p.type = args['from-pool'].default_type

        for avp in opts.get('extra-attribute', []):
            try:
                key, value = avp.split('=', 1)
            except ValueError:
                print("ERROR: Incorrect extra-attribute: {0!s}. Accepted form: 'key=value'\n".format(avp), file=sys.stderr)
                return
            p.avps[key] = value


        args['family'] = afi

        try:
            p.save(args)
        except NipapError as exc:
            print("Could not add prefix to NIPAP: {0!s}".format(str(exc)), file=sys.stderr)
            sys.exit(1)

        if p.type == 'host':
            print("Host {0!s} added to {1!s}: {2!s}".format(p.display_prefix,
                    vrf_format(p.vrf), p.node or p.description))
        else:
            print("Network {0!s} added to {1!s}: {2!s}".format(p.display_prefix,
                    vrf_format(p.vrf), p.description))

        if opts.get('add-hosts') is not None:
            if p.type != 'assignment':
                print("ERROR: Not possible to add hosts to non-assignment", file=sys.stderr)
                sys.exit(1)

            for host in opts.get('add-hosts').split(','):
                h_opts = {
                        'from-prefix': p.prefix,
                        'vrf_rt': p.vrf.rt,
                        'type': 'host',
                        'node': host
                        }
                add_prefix({}, h_opts, {})



def add_vrf(arg, opts, shell_opts):
    """ Add VRF to NIPAP
    """

    v = VRF()
    v.rt = opts.get('rt')
    v.name = opts.get('name')
    v.description = opts.get('description')
    v.tags = list(csv.reader([opts.get('tags', '')], escapechar='\\'))[0]

    for avp in opts.get('extra-attribute', []):
        try:
            key, value = avp.split('=', 1)
        except ValueError:
            print("ERROR: Incorrect extra-attribute: {0!s}. Accepted form: 'key=value'\n".format(avp), file=sys.stderr)
            return
        v.avps[key] = value

    try:
        v.save()
    except pynipap.NipapError as exc:
        print("Could not add VRF to NIPAP: {0!s}".format(str(exc)), file=sys.stderr)
        sys.exit(1)

    print("Added {0!s}".format((vrf_format(v))))



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

    for avp in opts.get('extra-attribute', []):
        try:
            key, value = avp.split('=', 1)
        except ValueError:
            print("ERROR: Incorrect extra-attribute: {0!s}. Accepted form: 'key=value'\n".format(avp), file=sys.stderr)
            return
        p.avps[key] = value

    try:
        p.save()
    except pynipap.NipapError as exc:
        print("Could not add pool to NIPAP: {0!s}".format(str(exc)), file=sys.stderr)
        sys.exit(1)

    print("Pool '{0!s}' created.".format((p.name)))



"""
    VIEW FUNCTIONS
"""
def view_vrf(arg, opts, shell_opts):
    """ View a single VRF
    """

    if arg is None:
        print("ERROR: Please specify the RT of the VRF to view.", file=sys.stderr)
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
        print("VRF with [RT: {0!s}] not found.".format(str(arg)), file=sys.stderr)
        sys.exit(1)

    print("-- VRF")
    print("  {0:<26!s} : {1:d}".format("ID", v.id))
    print("  {0:<26!s} : {1!s}".format("RT", v.rt))
    print("  {0:<26!s} : {1!s}".format("Name", v.name))
    print("  {0:<26!s} : {1!s}".format("Description", v.description))

    print("-- Extra Attributes")
    if v.avps is not None:
        for key in sorted(v.avps, key=lambda s: s.lower()):
            print("  {0:<26!s} : {1!s}".format(key, v.avps[key]))

    print("-- Tags")
    for tag_name in sorted(v.tags, key=lambda s: s.lower()):
        print("  {0!s}".format(tag_name))
    # statistics
    if v.total_addresses_v4 == 0:
        used_percent_v4 = 0
    else:
        used_percent_v4 = (float(v.used_addresses_v4)/v.total_addresses_v4)*100
    if v.total_addresses_v6 == 0:
        used_percent_v6 = 0
    else:
        used_percent_v6 = (float(v.used_addresses_v6)/v.total_addresses_v6)*100
    print("-- Statistics")
    print("  {0:<26!s} : {1!s}".format("IPv4 prefixes", v.num_prefixes_v4))
    print("  {0:<26!s} : {1:.0f} / {2:.0f} ({3:.2f}% of {4:.0f})".format("IPv4 addresses Used / Free",
            v.used_addresses_v4, v.free_addresses_v4, used_percent_v4,
            v.total_addresses_v4))
    print("  {0:<26!s} : {1!s}".format("IPv6 prefixes", v.num_prefixes_v6))
    print("  {0:<26!s} : {1:.4e} / {2:.4e} ({3:.2f}% of {4:.4e})".format("IPv6 addresses Used / Free",
            v.used_addresses_v6, v.free_addresses_v6, used_percent_v6,
            v.total_addresses_v6))



def view_pool(arg, opts, shell_opts):
    """ View a single pool
    """

    res = Pool.list({ 'name': arg })

    if len(res) == 0:
        print("No pool with name '{0!s}' found.".format(arg))
        return

    p = res[0]

    vrf_rt = None
    vrf_name = None
    if p.vrf:
        vrf_rt = p.vrf.rt
        vrf_name = p.vrf.name

    print("-- Pool ")
    print("  {0:<26!s} : {1:d}".format("ID", p.id))
    print("  {0:<26!s} : {1!s}".format("Name", p.name))
    print("  {0:<26!s} : {1!s}".format("Description", p.description))
    print("  {0:<26!s} : {1!s}".format("Default type", p.default_type))
    print("  {0:<26!s} : {1!s} / {2!s}".format("Implied VRF RT / name", vrf_rt, vrf_name))
    print("  {0:<26!s} : {1!s} / {2!s}".format("Preflen (v4/v6)", str(p.ipv4_default_prefix_length), str(p.ipv6_default_prefix_length)))

    print("-- Extra Attributes")
    if p.avps is not None:
        for key in sorted(p.avps, key=lambda s: s.lower()):
            print("  {0:<26!s} : {1!s}".format(key, p.avps[key]))

    print("-- Tags")
    for tag_name in sorted(p.tags, key=lambda s: s.lower()):
        print("  {0!s}".format(tag_name))

    # statistics
    print("-- Statistics")

    # IPv4 total / used / free prefixes
    if p.member_prefixes_v4 == 0:
        print("  IPv4 prefixes Used / Free  : N/A (No IPv4 member prefixes)")
    elif p.ipv4_default_prefix_length is None:
        print("  IPv4 prefixes Used / Free  : N/A (IPv4 default prefix length is not set)")
    else:
        if p.total_prefixes_v4 == 0:
            used_percent_v4 = 0
        else:
            used_percent_v4 = (float(p.used_prefixes_v4)/p.total_prefixes_v4)*100

        print("  {0:<26!s} : {1:.0f} / {2:.0f} ({3:.2f}% of {4:.0f})".format("IPv4 prefixes Used / Free",
                p.used_prefixes_v4, p.free_prefixes_v4, used_percent_v4,
                p.total_prefixes_v4))

    # IPv6 total / used / free prefixes
    if p.member_prefixes_v6 == 0:
        print("  IPv6 prefixes Used / Free  : N/A (No IPv6 member prefixes)")
    elif p.ipv6_default_prefix_length is None:
        print("  IPv6 prefixes Used / Free  : N/A (IPv6 default prefix length is not set)")
    else:
        if p.total_prefixes_v6 == 0:
            used_percent_v6 = 0
        else:
            used_percent_v6 = (float(p.used_prefixes_v6)/p.total_prefixes_v6)*100
        print("  {0:<26!s} : {1:.4e} / {2:.4e} ({3:.2f}% of {4:.4e})".format("IPv6 prefixes Used / Free",
                p.used_prefixes_v6, p.free_prefixes_v6, used_percent_v6,
                p.total_prefixes_v6))


    # IPv4 total / used / free addresses
    if p.member_prefixes_v4 == 0:
        print("  IPv4 addresses Used / Free  : N/A (No IPv4 member prefixes)")
    elif p.ipv4_default_prefix_length is None:
        print("  IPv4 addresses Used / Free  : N/A (IPv4 default prefix length is not set)")
    else:
        if p.total_addresses_v4 == 0:
            used_percent_v4 = 0
        else:
            used_percent_v4 = (float(p.used_addresses_v4)/p.total_addresses_v4)*100

        print("  {0:<26!s} : {1:.0f} / {2:.0f} ({3:.2f}% of {4:.0f})".format("IPv4 addresses Used / Free",
                p.used_addresses_v4, p.free_addresses_v4, used_percent_v4,
                p.total_addresses_v4))

    # IPv6 total / used / free addresses
    if p.member_prefixes_v6 == 0:
        print("  IPv6 addresses Used / Free  : N/A (No IPv6 member prefixes)")
    elif p.ipv6_default_prefix_length is None:
        print("  IPv6 addresses Used / Free  : N/A (IPv6 default prefix length is not set)")
    else:
        if p.total_addresses_v6 == 0:
            used_percent_v6 = 0
        else:
            used_percent_v6 = (float(p.used_addresses_v6)/p.total_addresses_v6)*100
        print("  {0:<26!s} : {1:.4e} / {2:.4e} ({3:.2f}% of {4:.4e})".format("IPv6 addresses Used / Free",
                p.used_addresses_v6, p.free_addresses_v6, used_percent_v6,
                p.total_addresses_v6))

    print("\n-- Prefixes in pool - v4: {0:d}  v6: {1:d}".format(p.member_prefixes_v4,
            p.member_prefixes_v6))

    res = Prefix.list({ 'pool_id': p.id})
    for pref in res:
        print("  {0!s}".format(pref.display_prefix))



def view_prefix(arg, opts, shell_opts):
    """ View a single prefix.
    """
    # Internally, this function searches in the prefix column which means that
    # hosts have a prefix length of 32/128 while they are normally displayed
    # with the prefix length of the network they are in. To allow the user to
    # input either, e.g. 1.0.0.1 or 1.0.0.1/31 we strip the prefix length bits
    # to assume /32 if the address is not a network address. If it is the
    # network address we always search using the specified mask. In certain
    # cases there is a host with the network address, typically when /31 or /127
    # prefix lengths are used, for example 1.0.0.0/31 and 1.0.0.0/32 (first host
    # in /31 network) in which case it becomes necessary to distinguish between
    # the two using the mask.
    try:
        # this fails if bits are set on right side of mask
        ip = IPy.IP(arg)
    except ValueError:
        arg = arg.split('/')[0]

    q = { 'prefix': arg }

    v = get_vrf(opts.get('vrf_rt'), abort=True)
    if v.rt != 'all':
        q['vrf_rt'] = v.rt

    res = Prefix.list(q)

    if len(res) == 0:
        vrf_text = 'any VRF'
        if v.rt != 'all':
            vrf_text = vrf_format(v)
        print("Address {0!s} not found in {1!s}.".format(arg, vrf_text), file=sys.stderr)
        sys.exit(1)

    p = res[0]
    vrf = p.vrf.rt

    print("-- Address ")
    print("  {0:<26!s} : {1!s}".format("Prefix", p.prefix))
    print("  {0:<26!s} : {1!s}".format("Display prefix", p.display_prefix))
    print("  {0:<26!s} : {1!s}".format("Type", p.type))
    print("  {0:<26!s} : {1!s}".format("Status", p.status))
    print("  {0:<26!s} : IPv{1!s}".format("Family", p.family))
    print("  {0:<26!s} : {1!s}".format("VRF", vrf))
    print("  {0:<26!s} : {1!s}".format("Description", p.description))
    print("  {0:<26!s} : {1!s}".format("Node", p.node))
    print("  {0:<26!s} : {1!s}".format("Country", p.country))
    print("  {0:<26!s} : {1!s}".format("Order", p.order_id))
    print("  {0:<26!s} : {1!s}".format("Customer", p.customer_id))
    print("  {0:<26!s} : {1!s}".format("VLAN", p.vlan))
    print("  {0:<26!s} : {1!s}".format("Alarm priority", p.alarm_priority))
    print("  {0:<26!s} : {1!s}".format("Monitor", p.monitor))
    print("  {0:<26!s} : {1!s}".format("Added", p.added))
    print("  {0:<26!s} : {1!s}".format("Last modified", p.last_modified))
    print("  {0:<26!s} : {1!s}".format("Expires", p.expires or '-'))
    if p.family == 4:
        print("  {0:<26!s} : {1!s} / {2!s} ({3:.2f}% of {4!s})".format("Addresses Used / Free", p.used_addresses,
                p.free_addresses, (float(p.used_addresses)/p.total_addresses)*100,
                p.total_addresses))
    else:
        print("  {0:<26!s} : {1:.4e} / {2:.4e} ({3:.2f}% of {4:.4e})".format("Addresses Used / Free", p.used_addresses,
                p.free_addresses, (float(p.used_addresses)/p.total_addresses)*100,
                p.total_addresses))
    print("-- Extra Attributes")
    if p.avps is not None:
        for key in sorted(p.avps, key=lambda s: s.lower()):
            print("  {0:<26!s} : {1!s}".format(key, p.avps[key]))
    print("-- Tags")
    for tag_name in sorted(p.tags, key=lambda s: s.lower()):
        print("  {0!s}".format(tag_name))
    print("-- Inherited Tags")
    for tag_name in sorted(p.inherited_tags, key=lambda s: s.lower()):
        print("  {0!s}".format(tag_name))
    print("-- Comment")
    print(p.comment or '')



"""
    REMOVE FUNCTIONS
"""

def remove_vrf(arg, opts, shell_opts):
    """ Remove VRF
    """

    remove_confirmed = shell_opts.force

    res = VRF.list({ 'rt': arg })
    if len(res) < 1:
        print("VRF with [RT: {0!s}] not found.".format(arg), file=sys.stderr)
        sys.exit(1)

    v = res[0]

    if not remove_confirmed:
        print("RT: {0!s}\nName: {1!s}\nDescription: {2!s}".format(v.rt, v.name, v.description))
        print("\nWARNING: THIS WILL REMOVE THE VRF INCLUDING ALL ITS ADDRESSES")
        res = input("Do you really want to remove {0!s}? [y/N]: ".format(vrf_format(v)))

        if res == 'y':
            remove_confirmed = True
        else:
            print("Operation canceled.")

    if remove_confirmed:
        v.remove()
        print("{0!s} removed.".format(vrf_format(v)))



def remove_pool(arg, opts, shell_opts):
    """ Remove pool
    """

    remove_confirmed = shell_opts.force

    res = Pool.list({ 'name': arg })
    if len(res) < 1:
        print("No pool with name '{0!s}' found.".format(arg), file=sys.stderr)
        sys.exit(1)

    p = res[0]

    if not remove_confirmed:
        res = input("Do you really want to remove the pool '{0!s}'? [y/N]: ".format(p.name))

        if res == 'y':
            remove_confirmed = True
        else:
            print("Operation canceled.")

    if remove_confirmed:
        p.remove()
        print("Pool '{0!s}' removed.".format(p.name))


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
        print("Prefix {0!s} not found in {1!s}.".format(arg, vrf_text), file=sys.stderr)
        sys.exit(1)

    p = res[0]

    if p.authoritative_source != 'nipap':
        auth_src.add(p.authoritative_source)

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

    if not remove_confirmed:

        # if recursive is False, this delete will fail, ask user to do recursive
        # delete instead
        if p.type == 'assignment':
            if len(pres['result']) > 1:
                print("WARNING: {0!s} in {1!s} contains {2!s} hosts.".format(p.prefix, vrf_format(p.vrf), len(pres['result'])))
                res = input("Would you like to recursively delete {0!s} and all hosts? [y/N]: ".format((p.prefix)))
                if res.lower() in [ 'y', 'yes' ]:
                    recursive = True
                else:
                    print("ERROR: Removal of assignment containing hosts is prohibited. Aborting removal of {0!s} in {1!s}.".format(p.prefix, vrf_format(p.vrf)), file=sys.stderr)
                    sys.exit(1)

        if recursive is True:
            if len(pres['result']) <= 1:
                res = input("Do you really want to remove the prefix {0!s} in {1!s}? [y/N]: ".format(p.prefix, vrf_format(p.vrf)))

                if res.lower() in [ 'y', 'yes' ]:
                    remove_confirmed = True

            else:
                print("Recursively deleting {0!s} in {1!s} will delete the following prefixes:".format(p.prefix, vrf_format(p.vrf)))

                # Iterate prefixes to print a few of them and check the prefixes'
                # authoritative source
                i = 0
                for rp in pres['result']:
                    if i <= 10:
                        print("{0:<29!s} {1:<2!s} {2:<19!s} {3:<14!s} {4:<14!s} {5:<40!s}".format("".join("  " for i in
                            range(rp.indent)) + rp.display_prefix,
                            rp.type[0].upper(), rp.node, rp.order_id,
                            rp.customer_id, rp.description))

                    if i == 10:
                        print(".. and {0!s} other prefixes".format((len(pres['result']) - 10)))

                    if rp.authoritative_source != 'nipap':
                        auth_src.add(rp.authoritative_source)

                    i += 1

                if len(auth_src) == 0:
                    # Simple case; all prefixes were added from NIPAP
                    res = input("Do you really want to recursively remove {0!s} prefixes in {1!s}? [y/N]: ".format(len(pres['result']),
                                vrf_format(vrf)))

                    if res.lower() in [ 'y', 'yes' ]:
                        remove_confirmed = True

                else:
                    # we have prefixes with authoritative source != nipap
                    auth_src = list(auth_src)
                    plural = ""

                    # format prompt depending on how many different sources we have
                    if len(auth_src) == 1:
                        systems = "'{0!s}'".format(auth_src[0])
                        prompt = "Enter the name of the managing system to continue or anything else to abort: "

                    else:
                        systems = ", ".join("'{0!s}'".format(x) for x in auth_src[1:]) + " and '{0!s}'".format(auth_src[0])
                        plural = "s"
                        prompt = "Enter the name of the last managing system to continue or anything else to abort: "

                    print(("Prefix %s in %s contains prefixes managed by the system%s %s. " +
                        "Are you sure you want to remove them? ") % (p.prefix,
                                vrf_format(p.vrf), plural, systems))
                    res = input(prompt)

                    # Did the user provide the correct answer?
                    if res.lower() == auth_src[0].lower():
                        remove_confirmed = True
                    else:
                        print("System names did not match.", file=sys.stderr)
                        sys.exit(1)

        else:
            # non recursive delete
            if len(auth_src) > 0:
                auth_src = list(auth_src)
                print(("Prefix %s in %s is managed by the system '%s'. " +
                    "Are you sure you want to remove it? ") % (p.prefix,
                            vrf_format(p.vrf), auth_src[0]))
                res = input("Enter the name of the managing system to continue or anything else to abort: ")

                if res.lower() == auth_src[0].lower():
                    remove_confirmed = True

                else:
                    print("System names did not match.", file=sys.stderr)
                    sys.exit(1)

            else:
                res = input("Do you really want to remove the prefix {0!s} in {1!s}? [y/N]: ".format(p.prefix, vrf_format(p.vrf)))
                if res.lower() in [ 'y', 'yes' ]:
                    remove_confirmed = True

    if remove_confirmed is True:
        p.remove(recursive = recursive)
        if recursive is True:
            print("Prefix {0!s} and {1!s} other prefixes in {2!s} removed.".format(p.prefix,
                    (len(pres['result']) - 1), vrf_format(p.vrf)))
        else:
            print("Prefix {0!s} in {1!s} removed.".format(p.prefix, vrf_format(p.vrf)))

    else:
        print("Operation canceled.")


"""
    MODIFY FUNCTIONS
"""

def modify_vrf(arg, opts, shell_opts):
    """ Modify a VRF with the options set in opts
    """

    res = VRF.list({ 'rt': arg })
    if len(res) < 1:
        print("VRF with [RT: {0!s}] not found.".format(arg), file=sys.stderr)
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

    for avp in opts.get('extra-attribute', []):
        try:
            key, value = avp.split('=', 1)
        except ValueError:
            print("ERROR: Incorrect extra-attribute: {0!s}. Accepted form: 'key=value'\n".format(avp), file=sys.stderr)
            return
        v.avps[key] = value

    v.save()

    print("{0!s} saved.".format(vrf_format(v)))



def modify_pool(arg, opts, shell_opts):
    """ Modify a pool with the options set in opts
    """

    res = Pool.list({ 'name': arg })
    if len(res) < 1:
        print("No pool with name '{0!s}' found.".format(arg), file=sys.stderr)
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

    for avp in opts.get('extra-attribute', []):
        try:
            key, value = avp.split('=', 1)
        except ValueError:
            print("ERROR: Incorrect extra-attribute: {0!s}. Accepted form: 'key=value'\n".format(avp), file=sys.stderr)
            return
        p.avps[key] = value


    p.save()

    print("Pool '{0!s}' saved.".format(p.name))



def grow_pool(arg, opts, shell_opts):
    """ Expand a pool with the ranges set in opts
    """
    if not pool:
        print("No pool with name '{0!s}' found.".format(arg), file=sys.stderr)
        sys.exit(1)

    if not 'add' in opts:
        print("Please supply a prefix to add to pool '{0!s}'".format(pool.name), file=sys.stderr)
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
        print("No prefix found matching {0!s} in {1!s}.".format(opts['add'], vrf_format(v)), file=sys.stderr)
        sys.exit(1)
    elif res[0].pool:
        if res[0].pool == pool:
            print("Prefix {0!s} in {1!s} is already assigned to that pool.".format(opts['add'], vrf_format(v)), file=sys.stderr)
        else:
            print("Prefix {0!s} in {1!s} is already assigned to a different pool ('{2!s}').".format(opts['add'], vrf_format(v), res[0].pool.name), file=sys.stderr)
        sys.exit(1)

    res[0].pool = pool
    res[0].save()
    print("Prefix {0!s} in {1!s} added to pool '{2!s}'.".format(res[0].prefix, vrf_format(v), pool.name))



def shrink_pool(arg, opts, shell_opts):
    """ Shrink a pool by removing the ranges in opts from it
    """
    if not pool:
        print("No pool with name '{0!s}' found.".format(arg), file=sys.stderr)
        sys.exit(1)

    if 'remove' in opts:
        res = Prefix.list({'prefix': opts['remove'], 'pool_id': pool.id})

        if len(res) == 0:
            print("Pool '{0!s}' does not contain {1!s}.".format(pool.name,
                opts['remove']), file=sys.stderr)
            sys.exit(1)

        res[0].pool = None
        res[0].save()
        print("Prefix {0!s} removed from pool '{1!s}'.".format(res[0].prefix, pool.name))
    else:
        print("Please supply a prefix to add or remove to '{0!s}':".format((
            pool.name)), file=sys.stderr)
        for pref in Prefix.list({'pool_id': pool.id}):
            print("  {0!s}".format(pref.prefix))



def modify_prefix(arg, opts, shell_opts):
    """ Modify the prefix 'arg' with the options 'opts'
    """

    modify_confirmed = shell_opts.force

    spec = { 'prefix': arg }
    v = get_vrf(opts.get('vrf_rt'), abort=True)
    spec['vrf_rt'] = v.rt

    res = Prefix.list(spec)
    if len(res) == 0:
        print("Prefix {0!s} not found in {1!s}.".format(arg, vrf_format(v)), file=sys.stderr)
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
    if 'status' in opts:
        p.status = opts['status']
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
    if 'expires' in opts:
        p.expires = opts['expires']

    for avp in opts.get('extra-attribute', []):
        try:
            key, value = avp.split('=', 1)
        except ValueError:
            print("ERROR: Incorrect extra-attribute: {0!s}. Accepted form: 'key=value'\n".format(avp), file=sys.stderr)
            return
        p.avps[key] = value


    # Promt user if prefix has authoritative source != nipap
    if not modify_confirmed and p.authoritative_source.lower() != 'nipap':

        res = input("Prefix {0!s} in {1!s} is managed by system '{2!s}'. Are you sure you want to modify it? [y/n]: ".format(p.prefix, vrf_format(p.vrf), p.authoritative_source))

        # If the user declines, short-circuit...
        if res.lower() not in [ 'y', 'yes' ]:
            print("Operation aborted.")
            return

    try:
        p.save()
    except NipapError as exc:
        print("Could not save prefix changes: {0!s}".format(str(exc)), file=sys.stderr)
        sys.exit(1)

    print("Prefix {0!s} in {1!s} saved.".format(p.display_prefix, vrf_format(p.vrf)))



def prefix_attr_add(arg, opts, shell_opts):
    """ Add attributes to a prefix
    """

    spec = { 'prefix': arg }
    v = get_vrf(opts.get('vrf_rt'), abort=True)
    spec['vrf_rt'] = v.rt

    res = Prefix.list(spec)
    if len(res) == 0:
        print("Prefix {0!s} not found in {1!s}.".format(arg, vrf_format(v)), file=sys.stderr)
        return

    p = res[0]

    for avp in opts.get('extra-attribute', []):
        try:
            key, value = avp.split('=', 1)
        except ValueError:
            print("ERROR: Incorrect extra-attribute: {0!s}. Accepted form: 'key=value'\n".format(avp), file=sys.stderr)
            sys.exit(1)

        if key in p.avps:
            print("Unable to add extra-attribute: '{0!s}' already exists.".format(key), file=sys.stderr)
            sys.exit(1)

        p.avps[key] = value

    try:
        p.save()
    except NipapError as exc:
        print("Could not save prefix changes: {0!s}".format(str(exc)), file=sys.stderr)
        sys.exit(1)

    print("Prefix {0!s} in {1!s} saved.".format(p.display_prefix, vrf_format(p.vrf)))



def prefix_attr_remove(arg, opts, shell_opts):
    """ Remove attributes from a prefix
    """

    spec = { 'prefix': arg }
    v = get_vrf(opts.get('vrf_rt'), abort=True)
    spec['vrf_rt'] = v.rt

    res = Prefix.list(spec)
    if len(res) == 0:
        print("Prefix {0!s} not found in {1!s}.".format(arg, vrf_format(v)), file=sys.stderr)
        return

    p = res[0]

    for key in opts.get('extra-attribute', []):
        if key not in p.avps:
            print("Unable to remove extra-attribute: '{0!s}' does not exist.".format(key), file=sys.stderr)
            sys.exit(1)

        del p.avps[key]

    try:
        p.save()
    except NipapError as exc:
        print("Could not save prefix changes: {0!s}".format(str(exc)), file=sys.stderr)
        sys.exit(1)

    print("Prefix {0!s} in {1!s} saved.".format(p.display_prefix, vrf_format(p.vrf)))



def vrf_attr_add(arg, opts, shell_opts):
    """ Add attributes to a VRF
    """

    if arg is None:
        print("ERROR: Please specify the RT of the VRF to view.", file=sys.stderr)
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
        print("VRF with [RT: {0!s}] not found.".format(str(arg)), file=sys.stderr)
        sys.exit(1)

    for avp in opts.get('extra-attribute', []):
        try:
            key, value = avp.split('=', 1)
        except ValueError:
            print("ERROR: Incorrect extra-attribute: {0!s}. Accepted form: 'key=value'\n".format(avp), file=sys.stderr)
            sys.exit(1)

        if key in v.avps:
            print("Unable to add extra-attribute: '{0!s}' already exists.".format(key), file=sys.stderr)
            sys.exit(1)

        v.avps[key] = value

    try:
        v.save()
    except NipapError as exc:
        print("Could not save VRF changes: {0!s}".format(str(exc)), file=sys.stderr)
        sys.exit(1)

    print("{0!s} saved.".format(vrf_format(v)))



def vrf_attr_remove(arg, opts, shell_opts):
    """ Remove attributes from a prefix
    """

    if arg is None:
        print("ERROR: Please specify the RT of the VRF to view.", file=sys.stderr)
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
        print("VRF with [RT: {0!s}] not found.".format(str(arg)), file=sys.stderr)
        sys.exit(1)

    for key in opts.get('extra-attribute', []):
        if key not in v.avps:
            print("Unable to remove extra-attribute: '{0!s}' does not exist.".format(key), file=sys.stderr)
            sys.exit(1)

        del v.avps[key]

    try:
        v.save()
    except NipapError as exc:
        print("Could not save VRF changes: {0!s}".format(str(exc)), file=sys.stderr)
        sys.exit(1)

    print("{0!s} saved.".format(vrf_format(v)))



def pool_attr_add(arg, opts, shell_opts):
    """ Add attributes to a pool
    """

    res = Pool.list({ 'name': arg })
    if len(res) < 1:
        print("No pool with name '{0!s}' found.".format(arg), file=sys.stderr)
        sys.exit(1)

    p = res[0]

    for avp in opts.get('extra-attribute', []):
        try:
            key, value = avp.split('=', 1)
        except ValueError:
            print("ERROR: Incorrect extra-attribute: {0!s}. Accepted form: 'key=value'\n".format(avp), file=sys.stderr)
            sys.exit(1)

        if key in p.avps:
            print("Unable to add extra-attribute: '{0!s}' already exists.".format(key), file=sys.stderr)
            sys.exit(1)

        p.avps[key] = value

    try:
        p.save()
    except NipapError as exc:
        print("Could not save pool changes: {0!s}".format(str(exc)), file=sys.stderr)
        sys.exit(1)

    print("Pool '{0!s}' saved.".format(p.name))



def pool_attr_remove(arg, opts, shell_opts):
    """ Remove attributes from a prefix
    """

    res = Pool.list({ 'name': arg })
    if len(res) < 1:
        print("No pool with name '{0!s}' found.".format(arg), file=sys.stderr)
        sys.exit(1)

    p = res[0]

    for key in opts.get('extra-attribute', []):
        if key not in p.avps:
            print("Unable to remove extra-attribute: '{0!s}' does not exist.".format(key), file=sys.stderr)
            sys.exit(1)

        del p.avps[key]

    try:
        p.save()
    except NipapError as exc:
        print("Could not save pool changes: {0!s}".format(str(exc)), file=sys.stderr)
        sys.exit(1)

    print("Pool '{0!s}' saved.".format(p.name))



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



def complete_prefix_status(arg):
    """ Complete NIPAP prefix status
    """
    return _complete_string(arg, valid_prefix_status)



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
    except configparser.NoOptionError:
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
        search_string = '^{0!s}'.format(arg)

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
        search_string = '^{0!s}'.format(arg)

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
                        'add-hosts': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': str,
                            }
                        },
                        'comment': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': str,
                            }
                        },
                        'country': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': str,
                                'complete': complete_country,
                            }
                        },
                        'description': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': str,
                            }
                        },
                        'family': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': str,
                                'complete': complete_family,
                            }
                        },
                        'status': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'description': 'Prefix status: {0!s}'.format(' | '.join(valid_prefix_status)),
                                'content_type': str,
                                'complete': complete_prefix_status,
                            }
                        },
                        'type': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'description': 'Prefix type: reservation | assignment | host',
                                'content_type': str,
                                'complete': complete_prefix_type,
                            }
                        },
                        'from-pool': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': str,
                                'complete': complete_pool_name,
                            }
                        },
                        'from-prefix': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': str,
                            }
                        },
                        'node': {
                            'type': 'option',
                            'content_type': str,
                            'argument': {
                                'type': 'value',
                                'content_type': str,
                                'complete': complete_node,
                            }
                        },
                        'order_id': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': str,
                            }
                        },
                        'customer_id': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': str,
                            }
                        },
                        'tags': {
                            'type': 'option',
                            'content_type': str,
                            'argument': {
                                'type': 'value',
                                'content_type': str,
                                'complete': complete_tags,
                            }
                        },
                        'extra-attribute': {
                            'type': 'option',
                            'multiple': True,
                            'content_type': str,
                            'argument': {
                                'type': 'value',
                                'content_type': str,
                            },
                        },
                        'vrf_rt': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': str,
                                'complete': complete_vrf,
                            }
                        },
                        'prefix': {
                            'type': 'option',
                            'content_type': str,
                            'argument': {
                                'type': 'value',
                                'content_type': str,
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
                                'content_type': str,
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
                                'content_type': str,
                                'complete': complete_priority,
                            }
                        },
                        'expires': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': str,
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
                        'content_type': str,
                    },
                    'children': {
                        'vrf_rt': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': str,
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
                        'content_type': str,
                        'description': 'Prefix to edit',
                    },
                    'children': {
                        'vrf_rt': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': str,
                                'description': 'VRF',
                                'complete': complete_vrf,
                            },
                            'exec_immediately': get_vrf
                        },
                        'add': {
                            'type': 'command',
                            'exec': prefix_attr_add,
                            'children': {
                                'extra-attribute': {
                                    'type': 'option',
                                    'multiple': True,
                                    'content_type': str,
                                    'argument': {
                                        'type': 'value',
                                        'content_type': str,
                                    },
                                },
                            }
                        },
                        'remove': {
                            'type': 'command',
                            'exec': prefix_attr_remove,
                            'children': {
                                'extra-attribute': {
                                    'type': 'option',
                                    'multiple': True,
                                    'content_type': str,
                                    'argument': {
                                        'type': 'value',
                                        'content_type': str,
                                    },
                                },
                            }
                        },
                        'set': {
                            'type': 'command',
                            'exec': modify_prefix,
                            'children': {
                                'comment': {
                                    'type': 'option',
                                    'argument': {
                                        'type': 'value',
                                        'content_type': str,
                                    }
                                },
                                'country': {
                                    'type': 'option',
                                    'argument': {
                                        'type': 'value',
                                        'content_type': str,
                                        'complete': complete_country,
                                    }
                                },
                                'description': {
                                    'type': 'option',
                                    'argument': {
                                        'type': 'value',
                                        'content_type': str,
                                    }
                                },
                                'family': {
                                    'type': 'option',
                                    'argument': {
                                        'type': 'value',
                                        'content_type': str,
                                        'complete': complete_family,
                                    }
                                },
                                'status': {
                                    'type': 'option',
                                    'argument': {
                                        'type': 'value',
                                        'description': 'Prefix status: {0!s}'.format(' | '.join(valid_prefix_status)),
                                        'content_type': str,
                                        'complete': complete_prefix_status,
                                    }
                                },
                                'type': {
                                    'type': 'option',
                                    'argument': {
                                        'type': 'value',
                                        'description': 'Prefix type: reservation | assignment | host',
                                        'content_type': str,
                                        'complete': complete_prefix_type,
                                    }
                                },
                                'extra-attribute': {
                                    'type': 'option',
                                    'multiple': True,
                                    'content_type': str,
                                    'argument': {
                                        'type': 'value',
                                        'content_type': str,
                                    },
                                },
                                'node': {
                                    'type': 'option',
                                    'content_type': str,
                                    'argument': {
                                        'type': 'value',
                                        'content_type': str,
                                        'complete': complete_node,
                                    }
                                },
                                'order_id': {
                                    'type': 'option',
                                    'argument': {
                                        'type': 'value',
                                        'content_type': str,
                                    }
                                },
                                'customer_id': {
                                    'type': 'option',
                                    'argument': {
                                        'type': 'value',
                                        'content_type': str,
                                    }
                                },
                                'prefix': {
                                    'type': 'option',
                                    'content_type': str,
                                    'argument': {
                                        'type': 'value',
                                        'content_type': str,
                                    }
                                },
                                'tags': {
                                    'type': 'option',
                                    'content_type': str,
                                    'argument': {
                                        'type': 'value',
                                        'content_type': str,
                                        'complete': complete_tags,
                                    }
                                },
                                'vrf_rt': {
                                    'type': 'option',
                                    'argument': {
                                        'type': 'value',
                                        'content_type': str,
                                        'complete': complete_vrf,
                                    }
                                },
                                'monitor': {
                                    'type': 'option',
                                    'argument': {
                                        'type': 'value',
                                        'content_type': str,
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
                                        'content_type': str,
                                        'complete': complete_priority,
                                    }
                                },
                                'expires': {
                                    'type': 'option',
                                    'argument': {
                                        'type': 'value',
                                        'content_type': str,
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
                        'content_type': str,
                        'description': 'Remove address'
                    },
                    'children': {
                        'vrf_rt': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': str,
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
                        'content_type': str,
                        'description': 'Address to view'
                    },
                    'children': {
                        'vrf_rt': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': str,
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
                                'content_type': str,
                                'description': 'VRF RT'
                            }
                        },
                        'name': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': str,
                                'description': 'VRF name',
                            }

                        },
                        'description': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': str,
                                'description': 'Description of the VRF'
                            }
                        },
                        'tags': {
                            'type': 'option',
                            'content_type': str,
                            'argument': {
                                'type': 'value',
                                'content_type': str,
                                'complete': complete_tags,
                            }
                        }
                    }
                },

                # list
                'list': {
                    'type': 'command',
                    'exec': list_vrf,
                    'rest_argument': {
                        'type': 'value',
                        'content_type': str,
                    },
                    'children': {
                    }
                },

                # view
                'view': {
                    'exec': view_vrf,
                    'type': 'command',
                    'argument': {
                        'type': 'value',
                        'content_type': str,
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
                        'content_type': str,
                        'description': 'VRF',
                        'complete': complete_vrf,
                    }
                },

                # modify
                'modify': {
                    'type': 'command',
                    'argument': {
                        'type': 'value',
                        'content_type': str,
                        'description': 'VRF',
                        'complete': complete_vrf,
                    },
                    'children': {
                        'add': {
                            'type': 'command',
                            'exec': vrf_attr_add,
                            'children': {
                                'extra-attribute': {
                                    'type': 'option',
                                    'multiple': True,
                                    'content_type': str,
                                    'argument': {
                                        'type': 'value',
                                        'content_type': str,
                                    },
                                },
                            }
                        },
                        'remove': {
                            'type': 'command',
                            'exec': vrf_attr_remove,
                            'children': {
                                'extra-attribute': {
                                    'type': 'option',
                                    'multiple': True,
                                    'content_type': str,
                                    'argument': {
                                        'type': 'value',
                                        'content_type': str,
                                    },
                                },
                            }
                        },
                        'set': {
                            'type': 'command',
                            'exec': modify_vrf,
                            'children': {
                                'rt': {
                                    'type': 'option',
                                    'argument': {
                                        'type': 'value',
                                        'content_type': str,
                                        'description': 'VRF RT'
                                    }
                                },
                                'name': {
                                    'type': 'option',
                                    'argument': {
                                        'type': 'value',
                                        'content_type': str,
                                        'description': 'VRF name',
                                    }

                                },
                                'description': {
                                    'type': 'option',
                                    'argument': {
                                        'type': 'value',
                                        'content_type': str,
                                        'description': 'Description of the VRF'
                                    }
                                },
                                'tags': {
                                    'type': 'option',
                                    'content_type': str,
                                    'argument': {
                                        'type': 'value',
                                        'content_type': str,
                                        'complete': complete_tags,
                                    }
                                },
                                'extra-attribute': {
                                    'type': 'option',
                                    'multiple': True,
                                    'content_type': str,
                                    'argument': {
                                        'type': 'value',
                                        'content_type': str,
                                    },
                                },
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
                                'content_type': str,
                                'descripton': 'Default prefix type: reservation | assignment | host',
                                'complete': complete_prefix_type,
                            }
                        },
                        'name': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': str,
                                'descripton': 'Name of the pool'
                            }
                        },
                        'description': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': str,
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
                            'content_type': str,
                            'argument': {
                                'type': 'value',
                                'content_type': str,
                                'complete': complete_tags,
                            }
                        },
                        'extra-attribute': {
                            'type': 'option',
                            'multiple': True,
                            'content_type': str,
                            'argument': {
                                'type': 'value',
                                'content_type': str,
                            },
                        },
                    }
                },

                # list
                'list': {
                    'type': 'command',
                    'exec': list_pool,
                    'rest_argument': {
                        'type': 'value',
                        'content_type': str,
                    },
                    'children': {
                        'vrf_rt': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': str,
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
                        'content_type': str,
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
                        'content_type': str,
                        'description': 'Pool name',
                        'complete': complete_pool_name,
                    },
                    'children': {
                        'add': {
                            'type': 'option',
                            'exec': grow_pool,
                            'argument': {
                                'type': 'value',
                                'content_type': str,
                            },
                            'children': {
                                'vrf_rt': {
                                    'type': 'option',
                                    'argument': {
                                        'type': 'value',
                                        'content_type': str,
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
                                'content_type': str,
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
                        'content_type': str,
                        'description': 'Pool name',
                        'complete': complete_pool_name,
                    },
                    'children': {
                        'add': {
                            'type': 'command',
                            'exec': pool_attr_add,
                            'children': {
                                'extra-attribute': {
                                    'type': 'option',
                                    'multiple': True,
                                    'content_type': str,
                                    'argument': {
                                        'type': 'value',
                                        'content_type': str,
                                    },
                                },
                            }
                        },
                        'remove': {
                            'type': 'command',
                            'exec': pool_attr_remove,
                            'children': {
                                'extra-attribute': {
                                    'type': 'option',
                                    'multiple': True,
                                    'content_type': str,
                                    'argument': {
                                        'type': 'value',
                                        'content_type': str,
                                    },
                                },
                            }
                        },
                        'set': {
                            'type': 'command',
                            'exec': modify_pool,
                            'children': {
                                'default-type': {
                                    'type': 'option',
                                    'argument': {
                                        'type': 'value',
                                        'content_type': str,
                                        'descripton': 'Default prefix type: reservation | assignment | host',
                                        'complete': complete_prefix_type,
                                    }
                                },
                                'name': {
                                    'type': 'option',
                                    'argument': {
                                        'type': 'value',
                                        'content_type': str,
                                        'descripton': 'Name of the pool'
                                    }
                                },
                                'description': {
                                    'type': 'option',
                                    'argument': {
                                        'type': 'value',
                                        'content_type': str,
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
                                    'content_type': str,
                                    'argument': {
                                        'type': 'value',
                                        'content_type': str,
                                        'complete': complete_tags,
                                    }
                                },
                                'extra-attribute': {
                                    'type': 'option',
                                    'multiple': True,
                                    'content_type': str,
                                    'argument': {
                                        'type': 'value',
                                        'content_type': str,
                                    },
                                },
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
                        'content_type': str,
                        'description': 'Pool name',
                        'complete': complete_pool_name,
                    }
                }
            }
        }
    }
}


if __name__ == '__main__':

    try:
        cmd = Command(cmds, sys.argv[1::])
    except ValueError as exc:
        print("Error: {0!s}".format(str(exc)), file=sys.stderr)
        sys.exit(1)

    # execute command
    if cmd.exe is None:
        print("Incomplete command specified")
        print("valid completions: {0!s}".format(" ".join(cmd.next_values())))
        sys.exit(1)

    try:
        cmd.exe(cmd.arg, cmd.exe_options)
    except NipapError as exc:
        print("Command failed:\n  {0!s}".format(str(exc)), file=sys.stderr)
        sys.exit(1)

