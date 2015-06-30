#!/usr/bin/python
""" This is a generic file exporter for NIPAP

    It fetches prefixes based on a provided query string and feeds that into a
    template that can be used to produce a configuration file for another
    program, such as ISC DHCP.

    It will read .nipaprc per default or rely on command line options for
    connection settings to the backend.
"""

from __future__ import print_function

import ConfigParser
import os
# use local pynipap, useful if we are developing
import sys
sys.path.append('../pynipap')
from pynipap import Prefix, Pool, VRF
import pynipap

import IPy
import jinja2

#
# Fill in your code here
#

class ConfigExport:
    def __init__(self, template_filename, output_filename):
        """ Init!
        """
        self.output_filename = output_filename

        env = jinja2.Environment(loader=jinja2.FileSystemLoader(['./']))
        self.t = env.get_template(template_filename)
        self.prefixes = []


    def get_prefixes(self, query):
        """ Get prefix data from NIPAP
        """
        try:
            res = Prefix.smart_search(query, {})
        except socket.error:
            print >> sys.stderr, "Connection refused, please check hostname & port"
            sys.exit(1)
        except xmlrpclib.ProtocolError:
            print >> sys.stderr, "Authentication failed, please check your username / password"
            sys.exit(1)

        for p in res['result']:
            p.prefix_ipy = IPy.IP(p.prefix)
            self.prefixes.append(p)


    def write_conf(self):
        """ Write the config to file
        """
        f = open(self.output_filename, 'w')
        print(self.t.render(prefixes=self.prefixes), file=f)
        f.close()



if __name__ == '__main__':
    # read configuration
    cfg = ConfigParser.ConfigParser()
    cfg.read(os.path.expanduser('~/.nipaprc'))

    import optparse
    parser = optparse.OptionParser()
    # standard options to specify nipapd connection
    parser.add_option('--username', help="NIPAP backend username")
    parser.add_option('--password', help="NIPAP backend password")
    parser.add_option('--host', help="NIPAP backend host")
    parser.add_option('--port', help="NIPAP backend port")

    parser.add_option('--template', help="template file")
    parser.add_option('--output-file', help="output file")
    parser.add_option('--query', default='', help="query for filtering prefixes")
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

    if not options.template:
        print("Please specify a template file", file=sys.stderr)
        sys.exit(1)

    if not options.output_file:
        print("Please specify an output file", file=sys.stderr)
        sys.exit(1)

    ce = ConfigExport(options.template, options.output_file)
    ce.get_prefixes(options.query)
    ce.write_conf()
