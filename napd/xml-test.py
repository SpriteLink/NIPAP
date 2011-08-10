#!/usr/bin/python

import xmlrpclib

import optparse

parser = optparse.OptionParser()
parser.add_option('-p', '--port', dest='port', type='int', default='1337', help="TCP port")

(options, args) = parser.parse_args()

server_url = 'http://127.0.0.1:%(port)d/XMLRPC' % { 'port': options.port }
server = xmlrpclib.Server(server_url, allow_none=1);

print server.search_prefix({ 'name': 'test-schema' }, {'operator': 'contained_within', 'val2': '10.0.0.0/30', 'val1': 'prefix'}, { 'include_all_children': False })

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



