#!/usr/bin/python

import xmlrpclib

import optparse

parser = optparse.OptionParser()
parser.add_option('-p', '--port', dest='port', type='int', default='1337', help="TCP port")

(options, args) = parser.parse_args()

server_url = 'http://tone.tele2.net:%(port)d/XMLRPC' % { 'port': options.port }
print server_url
server = xmlrpclib.Server(server_url, allow_none=1);

#
# echo test
#
print "try the echo function without args"
args = {}
print "ARGS:", args
print "RESULT:", server.echo()
print ""

print "try the echo function with a message argument"
args = { 'message': 'Please reply to me, Obi-Wan Kenobi, you are my only hope!' }
print "ARGS:", args
print "RESULT:", server.echo( args )
print ""


#
# try list function
#
print "try the list prefix function with a node argument"
args = { 'node': 'kst5-core-3' }
print "ARGS:", args
print "RESULT:", server.list_prefix( args )
print ""



