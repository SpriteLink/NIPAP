#!/usr/bin/python
# coding: utf-8

import xmlrpclib

import optparse
import time

parser = optparse.OptionParser()
parser.add_option('-p', '--port', dest='port', type='int', default='1337', help="TCP port")
parser.add_option('-U', '--user')
parser.add_option('-P', '--password')

(options, args) = parser.parse_args()

cred = ''
if options.user and options.password:
	cred = options.user + ':' + options.password + '@'

server_url = 'http://%(cred)s127.0.0.1:%(port)d/XMLRPC' % { 'port': options.port, 'cred': cred }
server = xmlrpclib.Server(server_url, allow_none=1);

remove_query = {
		'auth': {
			'authoritative_source': 'kll'
			},
		'schema': {
			'id': 1
			}
		}
server.remove_schema(remove_query)

#t0 = time.time()
#import sys
#ss = u'ballong'
#print "Type of search string:", type(ss)
#print ss
##res = server.search_schema({ 'operator': 'regex_match', 'val1': 'name', 'val2': 'test' }, { 'max_result': 500 })
#res = server.smart_search_schema(ss, { 'max_result': 500 })
#t1 = time.time()
#d1 = t1-t0
#print "Timing:", d1
#print res

#
# echo test
#
#print "try the echo function without args"
#args = {}
#print "ARGS:", args
#print "RESULT:", server.echo()
#print ""
#
#print "try the echo function with a message argument"
#args = { 'message': 'Please reply to me, Obi-Wan Kenobi, you are my only hope!' }
#print "ARGS:", args
#print "RESULT:", server.echo( args )
#print ""


#
# try list function
#
#print "try the list prefix function with a node argument"
#args = { 'node': 'kst5-core-3' }
#print "ARGS:", args
#print "RESULT:", server.list_prefix( args )
#print ""



