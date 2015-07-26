#!/usr/bin/python
""" This is a boilerplate for interacting with NIPAP using Pynipap

    It provides things such as basic command line parsing of connection options
    for the backend or reading the users .nipaprc file for getting connectivity
    settings.
"""

import ConfigParser
import os
# use local pynipap, useful if we are developing
import sys
sys.path.append('../pynipap')
from pynipap import Prefix, Pool, VRF
import pynipap

#
# Fill in your code here
#


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

