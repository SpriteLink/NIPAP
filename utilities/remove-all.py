#!/usr/bin/python
""" This script helps you remove all pools, prefixes or VRFs stored in NIPAP

    It can be useful when working on import script and you want to run many
    iterations over and over again, each time with an empty database.

    The audit log in the database will still reflect the deletion of the
    prefixes. There is no way to clear the audit log via the XML-RPC API (per
    design). If you truly want to clear it you will need to login to the
    database and run: DELETE FROM ip_net_log;

    Connection parameters are read from command line arguments or by reading the
    users .nipaprc file.
"""

import ConfigParser
import os
# use local pynipap, useful if we are developing
import sys
sys.path.append('../pynipap')
from pynipap import Prefix, Pool, VRF
import pynipap


if __name__ == '__main__':
    # read configuration
    cfg = ConfigParser.ConfigParser()
    cfg.read(os.path.expanduser('~/.nipaprc'))

    import optparse
    parser = optparse.OptionParser()
    parser.add_option('--username', help="NIPAP backend username")
    parser.add_option('--password', help="NIPAP backend password")
    parser.add_option('--host', help="NIPAP backend host")
    parser.add_option('--port', help="NIPAP backend port")
    parser.add_option('--clear-pools', action='store_true',
                      help="Remove all pools in NIPAP")
    parser.add_option('--clear-prefixes', action='store_true',
                      help="Remove all prefixes in NIPAP")
    parser.add_option('--clear-vrfs', action='store_true',
                      help="Remove all VRFs in NIPAP")
    parser.add_option("-f", "--force", action="store_true", default=False,
                      help="disable interactive prompting of actions")
    (options, args) = parser.parse_args()

    auth_uri = "%s:%s@" % (options.username or cfg.get('global', 'username'),
            options.password or cfg.get('global', 'password'))

    xmlrpc_uri = "http://%(auth_uri)s%(host)s:%(port)s" % {
            'auth_uri'  : auth_uri,
            'host'      : options.host or cfg.get('global', 'hostname'),
            'port'      : options.port or cfg.get('global', 'port')
            }
    pynipap.AuthOptions({ 'authoritative_source': 'nipap' })
    pynipap.xmlrpc_uri = xmlrpc_uri

    if options.clear_vrfs:
        remove_confirmed = options.force
        if not remove_confirmed:
            res = raw_input("Are you sure you want to remove all VRFs? Note how all" +
                            " prefixes in these VRFs WILL BE DELETED. The default VRF" +
                            " will NOT be deleted nor will it be emptied. [y/N]")
        if len(res) > 0 and res.lower()[0] == 'y':
            remove_confirmed = True
        else:
            print "Aborted"

        if remove_confirmed:
            print "Removing: ",
            for v in VRF.list():
                if v.id == 0:
                    continue
                v.remove()
                sys.stdout.write(".")
                sys.stdout.flush()
            print " done!"

    if options.clear_pools:
        remove_confirmed = options.force
        if not remove_confirmed:
            res = raw_input("Are you sure you want to remove all pools? [y/N]")
            if len(res) > 0 and res.lower()[0] == 'y':
                remove_confirmed = True
            else:
                print "Operation aborted."

        if remove_confirmed:
            print "Removing: ",
            for p in Pool.list():
                p.remove()
                sys.stdout.write(".")
                sys.stdout.flush()
            print " done!"

    if options.clear_prefixes:
        remove_confirmed = options.force
        if not remove_confirmed:
            res = raw_input("Are you sure you want to remove all prefixes? [y/N]")
            if len(res) > 0 and res.lower()[0] == 'y':
                remove_confirmed = True
            else:
                print "Aborted"

        if remove_confirmed:
            print "Removing: ",
            for p in Prefix.list({'indent': 0}):
                p.remove(recursive=True)
                sys.stdout.write(".")
                sys.stdout.flush()
            print " done!"

