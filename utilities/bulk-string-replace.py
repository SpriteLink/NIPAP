#! /usr/bin/env python
""" Tool to replace strings in NIPAP

    This tool is used to replace strings in NIPAP, helpful when for example
    moving many prefixes from a node to another. Instead of manually update
    prefix nodes and descriptions, this tool replaces all instances of a string
    with another.
    
    Currently the following attributes are checked for strings to replace:
    * node
    * description

    Usage: bulk-string-replace.py pattern replacement

    When the script is executed, it begins by fetching all prefixes from NIPAP
    which matches the pattern. It then iterates over them and prints out a
    "diff", showing what lines matches and what they would be changed to. Above
    each entry a number is displayed which identifies the entry.

    Then the user is asked to select what changes to perform. The selection is
    done by entering the numbers identifying the entries to change. Three types
    of input is supported:
    * The string 'all' - perform all listed replacements
    * A comma separated list of numbers (eg. 5,7,12,37).
      Replacement will be performed on the listed entries.
    * A comma separated list of numbers prefixed with an exclamation mark (!, eg
      !5,7,12,37). Replacement will be performed on all entries EXCEPT the
      listed entries.
"""

import ConfigParser
import os
import time
import re
import sys

from pynipap import Prefix, Pool, VRF
import pynipap

BATCH_SIZE = 100

COLOR_RESET = "\x1b[0m"
COLOR_RED = "\x1b[91m"
COLOR_GREEN = "\x1b[92m"

def replace(pattern, replacement):

    # Fetch prefixes matching the string to replace
    print "Fetching prefixes from NIPAP... ",
    sys.stdout.flush()
    n = 1
    prefix_list = []
    t0 = time.time()
    query = {
        'operator': 'or',
        'val1': {
            'operator': 'regex_match',
            'val1': 'description',
            'val2': pattern
        },
        'val2': {
            'operator': 'regex_match',
            'val1': 'node',
            'val2': pattern
        }
    }
    full_result = Prefix.search(query, { 'parents_depth': -1, 'max_result': BATCH_SIZE })
    prefix_result = full_result['result']
    prefix_list += prefix_result
    print len(prefix_list), 
    sys.stdout.flush()
    while len(prefix_result) == 100:
        full_result = Prefix.smart_search(pattern, { 'parents_depth': -1, 'max_result': BATCH_SIZE, 'offset': n * BATCH_SIZE })
        prefix_result = full_result['result']
        prefix_list += prefix_result
        print len(prefix_list), 
        sys.stdout.flush()
        n += 1

    t1 = time.time()
    print " done in {0:.1f} seconds".format((t1 - t0))

    # Display list
    print_pattern = "%-2s%-14s%-2s%-30s%-20s%s"
    print "\n\nPrefixes to change:"
    print print_pattern % ("", "VRF", "", "Prefix", "Node", "Description")
    i_match = 0
    for i, prefix in enumerate(prefix_list):
        if prefix.match:
            print COLOR_RESET,
            print " -- {0:d} --".format(i)
            color = COLOR_RED
        else:
            color = COLOR_RESET
            
        print (color + print_pattern) % (
            "-" if prefix.match else "",
            prefix.vrf.rt,
            prefix.type[0].upper(),
            (("  " * prefix.indent) + prefix.display_prefix)[:min([ len(prefix.display_prefix) + 2*prefix.indent, 30 ])],
            (prefix.node or '')[:min([ len(prefix.node or ''), 20 ])],
            (prefix.description or '')[:min([ len(prefix.description or ''), 900 ])]
        )
        if prefix.match:
            new_prefix_node = re.sub(pattern, replacement, (prefix.node or ''), flags=re.IGNORECASE)
            new_prefix_desc = re.sub(pattern, replacement, (prefix.description or ''), flags=re.IGNORECASE)
            print (COLOR_GREEN + print_pattern) % (
                "+",
                prefix.vrf.rt,
                prefix.type[0].upper(),
                ("  " * prefix.indent + prefix.display_prefix)[:min([ len(prefix.display_prefix) + 2*prefix.indent, 30 ])],
                new_prefix_node[:min([ len(new_prefix_node), 20 ])],
                new_prefix_desc[:min([ len(new_prefix_desc), 90 ])]
            )


    # reset colors
    print COLOR_RESET,

    # Perform action?
    print "Select replacements to perform"
    print "Enter comma-separated selection (eg. 5,7,10) or \"all\" for all prefixes."
    print "Prefix list with ! to invert selection (eg !5,7,10 to perform operation on all except the entered prefixes)"
    inp = raw_input("Selection: ").strip()

    if len(inp) == 0:
        print "Empty selection, quitting."
        sys.exit(0)

    invert = False
    if inp[0] == "!":
        inp = inp[1:]
        invert = True

    rename_all = False
    if inp == 'all':
        rename_all = True
        selection = []
    else:
        selection = inp.split(",")
        try:
            selection = map(lambda x: int(x.strip()), selection)
        except ValueError as e:
            print >> sys.stderr, "Could not parse selection: {0!s}".format(str(e))
            sys.exit(1)

    for i, prefix in enumerate(prefix_list):

        if prefix.match and ((invert and i not in selection) or (not invert and i in selection) or rename_all):
            if prefix.node is not None:
                prefix.node = re.sub(pattern, replacement, prefix.node, flags=re.IGNORECASE)
            if prefix.description is not None:
                prefix.description = re.sub(pattern, replacement, prefix.description, flags=re.IGNORECASE)

            print "Saving prefix {0!s}...".format(prefix.display_prefix)
            prefix.save()

if __name__ == '__main__':

    # Read config from ~/.nipaprc
    cfg = ConfigParser.ConfigParser()
    cfg.read(os.path.expanduser('~/.nipaprc'))

    # Parse command line arguments
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('pattern', help="pattern to replace")
    parser.add_argument('replacement', help="string to replace pattern with")
    parser.add_argument('--username', help="username")
    parser.add_argument('--password', help="password")
    parser.add_argument('--host', help="NIPAP backend host")
    parser.add_argument('--port', help="NIPAP backend port")
    args = parser.parse_args()

    # Set up NIPAP
    auth_uri = "{0!s}:{1!s}@".format(args.username or cfg.get('global', 'username'),
            args.password or cfg.get('global', 'password'))

    xmlrpc_uri = "http://{auth_uri!s}[{host!s}]:{port!s}".format(**{
            'auth_uri'  : auth_uri,
            'host'      : args.host or cfg.get('global', 'hostname'),
            'port'      : args.port or cfg.get('global', 'port')
            })
    pynipap.AuthOptions({ 'authoritative_source': 'nipap' })
    pynipap.xmlrpc_uri = xmlrpc_uri

    replace(args.pattern, args.replacement)
