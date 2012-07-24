#!/usr/bin/python

import os
import csv

import sys
sys.path.append('../pynipap')
import pynipap

class Export:
	def __init__(self, xmlrpc_uri):
		self.xmlrpc_uri = xmlrpc_uri


	def write(self, output_file, schema_name):
		"""
		"""
		f = open(output_file, "w+")
		writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)

		pynipap.xmlrpc_uri = xmlrpc_uri
		ao = pynipap.AuthOptions({ 'authoritative_source': 'nipap' })

		import socket,xmlrpclib
		try:
			schema = pynipap.Schema.list({ 'name': schema_name })[0]
		except socket.error:
			print >> sys.stderr, "Connection refused, please check hostname & port"
			sys.exit(1)
		except xmlrpclib.ProtocolError:
			print >> sys.stderr, "Authentication failed, please check your username / password"
			sys.exit(1)
		except IndexError:
			print >> sys.stderr, "Non existing schema (", schema_name, ")"
			sys.exit(1)

		res = pynipap.Prefix.smart_search(schema, ' ', { 'include_all_parents': True })
		for p in res['result']:
			writer.writerow([p.display_prefix, p.type, p.node, p.order_id, p.description])


if __name__ == '__main__':
	import optparse
	parser = optparse.OptionParser()
	parser.add_option('--username', default='', help="Username")
	parser.add_option('--password', default='', help="Password")
	parser.add_option('--host', help="NIPAP backend host")
	parser.add_option('--port', default=1337, help="NIPAP backend port")
	parser.add_option('--schema', help="Schema name")
	parser.add_option('--file', help="Output file")

	(options, args) = parser.parse_args()

	if options.host is None:
		print >> sys.stderr, "Please specify the NIPAP backend host to work with"
		sys.exit(1)

	if options.schema is None:
		print >> sys.stderr, "Please specify a schema to export"
		sys.exit(1)

	if options.file is None:
		print >> sys.stderr, "Please specify an output file"
		sys.exit(1)

	auth_uri = ''
	if options.username:
		auth_uri = "%s:%s@" % (options.username, options.password)

	xmlrpc_uri = "http://%(auth_uri)s%(host)s:%(port)s" % {
			'auth_uri'	: auth_uri,
			'host'		: options.host,
			'port'		: options.port
			}

	wr = Export(xmlrpc_uri)
	wr.write(options.file, options.schema)
