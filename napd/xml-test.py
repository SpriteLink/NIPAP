#!/usr/bin/python

import xmlrpclib

import optparse
import time

parser = optparse.OptionParser()
parser.add_option('-p', '--port', dest='port', type='int', default='1337', help="TCP port")

(options, args) = parser.parse_args()

server_url = 'http://127.0.0.1:%(port)d/XMLRPC' % { 'port': options.port }
server = xmlrpclib.Server(server_url, allow_none=1);
time.sleep(5)

t0 = time.time()
res = server.smart_search_prefix({ 'name': 'global' }, 'avk', { 'max_result': 500 })
t1 = time.time()
d1 = t1-t0
print "Timing:", d1
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



