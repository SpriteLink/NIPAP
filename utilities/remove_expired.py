#!/usr/bin/python
""" Script to remove prefixes that has expired in NIPAP

    This script removes prefixes in NIPAP with status quarantine
    and that has expired.

    Usage:

    When the script is executed, it deletes all prefixes with status 
    "quarantine" and where the expires date has passed.

    Prefixes within prefixes are recursively deleted only if the
    type is Assigned.
"""

import ConfigParser
import os
import datetime
# use local pynipap, useful if we are developing
import sys
sys.path.append('../pynipap')
from pynipap import Prefix
import pynipap
import socket,xmlrpclib


def _remove_expired_prefixes():
    query = { 
        'operator': 'and',
        'val1': {
            'operator': 'equals',
            'val1': 'status',
            'val2': 'quarantine' 
        },
        'val2': {
            'operator': 'less_or_equal',
            'val1': 'expires',
            'val2': 'Now()'
        }
    }

    try:
        res = Prefix.search(query)
    
    except socket.error:
        print >> sys.stderr, "Connection refused, please check hostname and port"
        sys.exit(1)
    except xmlrpclib.ProtocolError:
        print >> sys.stderr, "Authentication error, please check your username / password"
        sys.exit(1)

    prefixes = res['result']

    if len(prefixes) > 0:
        print datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S") + ": Expired quarantined prefixes found, they will be removed"

    for p in prefixes:
        recursive = True if p.type == "assignment" else False
        p.remove(recursive)
        print "Removed prefix " + p.prefix

    if len(prefixes) > 0:
        print  "Removed " + str(len(prefixes)) + " expired prefixes"


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

    auth_uri = "%s:%s@" % (args.username or cfg.get('global', 'username'),
            args.password or cfg.get('global', 'password'))

    xmlrpc_uri = "http://%(auth_uri)s%(host)s:%(port)s" % {
            'auth_uri'  : auth_uri,
            'host'      : args.host or cfg.get('global', 'hostname'),
            'port'      : args.port or cfg.get('global', 'port')
            }
    pynipap.AuthOptions({ 'authoritative_source': 'Expired quarantined prefixes removal script' })
    pynipap.xmlrpc_uri = xmlrpc_uri

    _remove_expired_prefixes()

    print "Done"