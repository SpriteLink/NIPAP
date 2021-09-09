#!/usr/bin/python3
""" Script to remove prefixes that has expired in NIPAP

    This script removes prefixes in NIPAP with status quarantine
    and that has expired.

    Usage:

    When the script is executed, it deletes all prefixes with status 
    "quarantine" and where the expires date has passed.

    Prefixes within prefixes are recursively deleted only if the
    type is Assigned.
"""

import os
import sys
import socket
import argparse
from datetime import datetime
import configparser

from pynipap import Prefix, NipapAuthError
import pynipap

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
        print("Connection refused, please check hostname and port", file=sys.stderr)
        sys.exit(1)
    except NipapAuthError:
        print("Authentication error, please check your username / password", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print("Error: %s" %str(exc), file=sys.stderr)
        sys.exit(1)

    prefixes = res['result']

    if len(prefixes) > 0:
        print("%s: Expired quarantined prefixes found, they will be removed" %datetime.now().strftime("%Y-%m-%d, %H:%M:%S"))

    for p in prefixes:
        recursive = True if p.type == "assignment" else False
        p.remove(recursive)
        print("Removed prefix %s" %p.prefix)

    if len(prefixes) > 0:
        print("Removed %s expired prefixes" %str(len(prefixes)))


if __name__ == '__main__':
    # read configuration
    cfg = configparser.ConfigParser()
    cfg.read(os.path.expanduser('~/.nipaprc'))
    
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
    pynipap.AuthOptions({'authoritative_source': 'Expired quarantined prefixes removal script'})
    pynipap.xmlrpc_uri = xmlrpc_uri

    _remove_expired_prefixes()

    print("Done")
    
