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

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', help="NIPAP backend username")
    parser.add_argument('--password', help="NIPAP backend password")
    parser.add_argument('--host', help="NIPAP backend host")
    parser.add_argument('--port', help="NIPAP backend port")
    args = parser.parse_args()

    auth_uri = "{0!s}:{1!s}@".format(args.username or cfg.get('global', 'username'),
            args.password or cfg.get('global', 'password'))

    xmlrpc_uri = "http://{auth_uri!s}{host!s}:{port!s}".format(**{
            'auth_uri'  : auth_uri,
            'host'      : args.host or cfg.get('global', 'hostname'),
            'port'      : args.port or cfg.get('global', 'port')
            })
    pynipap.AuthOptions({ 'authoritative_source': 'nipap' })
    pynipap.xmlrpc_uri = xmlrpc_uri

