#!/usr/bin/env python3
# coding: utf-8

import xmlrpc.client

import argparse
import time
import sys

parser = argparse.ArgumentParser()
parser.add_argument('-p', '--port', dest='port', type=int, default='1337', help="TCP port")
parser.add_argument('-U', '--user')
parser.add_argument('-P', '--password')

args = parser.parse_args()

cred = ''
if args.user and args.password:
    cred = args.user + ':' + args.password + '@'

server_url = 'http://%(cred)s127.0.0.1:%(port)d/XMLRPC' % {
    'port': args.port,
    'cred': cred,
}
server = xmlrpc.client.Server(server_url, allow_none=1)

ad = {'authoritative_source': 'nipap'}
query = {'val1': 'name', 'operator': 'regex_match', 'val2': '(foo|b.*)'}

res = server.list_vrf({'auth': ad, 'spec': {}})
print(res)
# res = server.smart_search_prefix({ 'auth': ad, 'query_string': '', 'search_options': { 'include_all_parents': True } })
# res = server.smart_search_prefix({ 'auth': ad, 'query_string': 'foo', 'search_options': { 'include_all_parents': True } })
# res = server.smart_search_prefix({ 'auth': ad, 'query_string': 'foo', 'search_options': { 'include_all_parents': True } })
# res = server.add_prefix({ 'spec': { 'prefix': '2.0.0.0/8' } })
# print res
# res = server.smart_search_prefix({ 'auth': ad, 'query_string': 'test1', 'search_options': { 'include_all_parents': True, 'root_prefix': '1.0.4.0/24' } })
# res = server.smart_search_prefix({ 'auth': ad, 'query_string': 'THISWILLNEVERMATCH', 'search_options': { 'include_all_parents': True, 'parent_prefix': 11963 } })
# res = server.smart_search_prefix({ 'auth': ad, 'query_string': 'test1', 'search_options': { 'include_all_parents': True, 'parent_prefix': 'bajs' } })

for p in res['result']:
    print(p)
# for p in res:
#    print res[p]
# print "".join(" " for i in xrange(p['indent'])), p['prefix'], p['match']

# res = server.list_pool({ 'auth': ad, 'pool': { 'id': 1003 } })
# res = server.version()

sys.exit(0)

remove_query = {'auth': {'authoritative_source': 'kll'}, 'schema': {'id': 1}}
# server.remove_schema(remove_query)
# print server.list_vrf({ 'auth': ad })
# sys.exit(0)
# print server.add_vrf({ 'auth': { 'authoritative_source': 'kll' },
#        'attr': {
#            'vrf': '1257:124',
#            'name': 'test2',
#            'description': 'my test VRF'
#            }
#        }
#    )
# print server.list_vrf({ 'auth': ad, 'vrf': {} })
# print server.add_prefix({ 'auth': ad, 'attr': {
#            'prefix': '1.0.0.0/24',
#            'type': 'assignment',
#            'description': 'test'
#        }
#    })
#
# print "All VRFs:"
# res = server.list_prefix({ 'auth': ad })
# for p in res:
#    print "%10s %s" % (p['vrf_name'], p['prefix'])
#
# print "VRF: test2"
# res = server.list_prefix({ 'auth': ad,
#        'prefix': {
#            'vrf': '1257:124'
#            }
#        })
# for p in res:
#    print "%10s %s" % (p['vrf_name'], p['prefix'])

# t0 = time.time()
# import sys
# ss = u'ballong'
# print "Type of search string:", type(ss)
# print ss
# res = server.search_schema({ 'operator': 'regex_match', 'val1': 'name', 'val2': 'test' }, { 'max_result': 500 })
a = {
    'auth': {'authoritative_source': 'kll'},
    'query_string': 'test',
    'search_options': {'include_all_parents': True, 'root_prefix': '1.3.0.0/16'},
}
res = server.smart_search_prefix(a)
for p in res['result']:
    print((p['vrf_rt'], p['display_prefix'], p['description'], p['match']))
# res = server.smart_search_prefix('test', { 'root_prefix': '1.3.0.0/8', 'max_result': 500 })
# t1 = time.time()
# d1 = t1-t0
# print "Timing:", d1
# print res

#
# echo test
#
# print "try the echo function without args"
# args = {}
# print "ARGS:", args
# print "RESULT:", server.echo()
# print ""
#
# print "try the echo function with a message argument"
# args = { 'message': 'Please reply to me, Obi-Wan Kenobi, you are my only hope!' }
# print "ARGS:", args
# print "RESULT:", server.echo( args )
# print ""


#
# try list function
#
# print "try the list prefix function with a node argument"
# args = { 'node': 'kst5-core-3' }
# print "ARGS:", args
# print "RESULT:", server.list_prefix( args )
# print ""
