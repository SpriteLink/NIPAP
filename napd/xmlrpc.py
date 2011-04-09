# vim: et :
from twisted.web import http, xmlrpc, server
from twisted.internet import defer, protocol, reactor
import base64
import logging
import os
import random
import re
import sha
import sys
import time
import xmlrpclib

import psycopg2

# Naming convention for XML-RPC interface
# all functions returning a list of something should be named list* and the thing they return
# for example listMovies()
# functions returning information about one thing are called get*
# similarly, setting functions are called set*

# logging
# llf = log line function
# lle = log line error, general function for use within function for error message




class NapXMLRPC():
    stop = None

    def __init__(self, port = 1337):
        self.port = port


    def run(self):
        from twisted.internet import reactor
        protocol = NapProtocol()
        reactor.listenTCP(self.port, server.Site(protocol))
        reactor.run()



        
class NapProtocol(xmlrpc.XMLRPC):
    """ Class to allow XML-RPC access to the lovely NAP system
    """

    def __init__(self):
        xmlrpc.XMLRPC.__init__(self)
        self.allowNone = True
        self.request = None
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Initialising NAP Protocol")
        self.con_pg = psycopg2.connect("host='localhost' dbname='nap' user='nap' password='Je9ydmLsBw7gg'")
        self.curs_pg = self.con_pg.cursor()



    def render(self, request):
        llf = "XMLRPC render: "
        lle = llf + "Authentication failed: "
        self.request = request

        # TODO: add authentication! how should we do auth?

        request.content.seek(0, 0)
        args, functionPath = xmlrpclib.loads(request.content.read())

        try:
            function = self._getFunction(functionPath)
        except Fault, f:
            self._cbRender(f, request)
        else:
            request.setHeader("content-type", "text/xml")
            defer.maybeDeferred(function, *args).addErrback(
                    self._ebRender
                    ).addCallback(
                    self._cbRender, request
                    )

        return server.NOT_DONE_YET



    def authorize(self, required = []):
        # TODO: re-add authorization!
        return 1

        llf = "XMLRPC authorize: "
        lle = llf + "Authorization failed for '" + self.request.getUser() + "': "
        self.logger.info(llf + "Authorizing user '" + self.request.getUser() + "': Required groups: " + str(required))

        # for failing auth, do this:
        if 1 == 2:
            self.logger.error(lle + "No rows from database")
            request.setResponseCode(http.UNAUTHORIZED)
            return { 'result': 'failure', 'message': 'Authorization Failed!' }


    def xmlrpc_echo(self, args = []):
        if 'message' in args:
            return { 'result': 'success', 'message': 'Echo from NAPD: ' + args['message'] }

        return { 'result': 'success', 'message': "This is an echo function, if you pass me a string in the argument named 'message', I will return it to you" }

    def xmlrpc_add_prefix(self, args):
        pass

    def xmlrpc_list_prefix(self, args):
        sql_where = ''
        sql_args = {
                'node': None
                }
        if 'node' in args:
            sql_where = 'WHERE node ~* %(node)s'
            sql_args['node'] = args['node']
            print sql_where

        query = """ SELECT prefix, description, node, comment, type, country, span_order, alarm_priority FROM ip_net_plan %s """ % ( sql_where )
        self.curs_pg.execute(query, sql_args)
        result = []
        while True:
            row = self.curs_pg.fetchone()
            if row is None:
                break

            ri = {}
            ri['prefix'] = row[0]
            ri['description'] = row[1]
            ri['node'] = row[2]
            ri['comment'] = row[3]
            ri['type'] = row[4]
            ri['country'] = row[5]
            ri['span_order'] = row[6]
            ri['alarm_priority'] = row[7]
            result.append(ri)

        return { 'result': 'success', 'prefixes': result }

