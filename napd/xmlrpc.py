# vim: et :
""" XML-RPC glue class
    ==================

    This module contains a "glue class" used by Twisted to export the Nap API functions over XML-RPC.

    For a detailed description of the API, see :doc:`nap`.
"""
from twisted.web import http, xmlrpc, server
from twisted.internet import defer, protocol, reactor
import logging
import xmlrpclib

import nap


class NapXMLRPC:
    stop = None

    def __init__(self, port = 1337):
        self.port = port


    def run(self):
        from twisted.internet import reactor
        protocol = NapProtocol()
        reactor.listenTCP(self.port, server.Site(protocol))
        reactor.run()


class NapProtocol(xmlrpc.XMLRPC):
    """ Class to allow XML-RPC access to the lovely NAP system.
    """

    def __init__(self):
        xmlrpc.XMLRPC.__init__(self)
        self.allowNone = True
        self.request = None
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Initialising NAP Protocol")

        self.nap = nap.Nap()


    def render(self, request):
        self.request = request

        # TODO: add authentication! how should we do auth?

        request.content.seek(0, 0)
        args, functionPath = xmlrpclib.loads(request.content.read())

        try:
            function = self._getFunction(functionPath)
        except xmlrpclib.Fault, f:
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


    def xmlrpc_echo(self, message=None):
        if 'message' is not None:
            return message

        return "This is an echo function, if you pass me a string, I will return it to you"


    #
    # SCHEMA FUNCTIONS
    #
    def xmlrpc_add_schema(self, args):
        """ Add a new network schema.
        """

        try:
            return self.nap.add_schema(args.get('attr'))
        except nap.NapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    def xmlrpc_remove_schema(self, args):
        """ Removes a schema.
        """

        try:
            self.nap.remove_schema(args.get('schema'))
        except nap.NapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    def xmlrpc_list_schema(self, args = {}):
        """ List schemas.
        """

        try:
            return self.nap.list_schema(args.get('schema'))
        except nap.NapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    def xmlrpc_edit_schema(self, args):
        """ Edit a schema.
        """

        try:
            self.nap.edit_schema(args.get('schema'), args.get('attr'))
        except nap.NapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    def xmlrpc_search_schema(self, args):
        """ Search for schemas.

            The 'query' input is a specially crafted dict/struct which
            permits quite flexible searches.
        """

        try:
            return self.nap.search_schema(args.get('query'), args.get('search_options'))
        except nap.NapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    def xmlrpc_smart_search_schema(self, args):
        """ Perform a smart search.

            The smart search function tries to extract a query from a text
            string. This query is then passed to the search_prefix function,
            which performs the actual search.
        """

        try:
            return self.nap.smart_search_schema(args.get('query_string'), args.get('search_options'))
        except nap.NapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    #
    # POOL FUNCTIONS
    #
    def xmlrpc_add_pool(self, args):
        """ Add a pool.
        """

        try:
            return self.nap.add_pool(args.get('schema'), args.get('attr'))
        except nap.NapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    def xmlrpc_remove_pool(self, args):
        """ Remove a pool.
        """

        try:
            self.nap.remove_pool(args.get('schema'), args.get('pool'))
        except nap.NapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    def xmlrpc_list_pool(self, args):
        """ List pools.
        """

        try:
            return self.nap.list_pool(args.get('schema'), args.get('pool'))
        except nap.NapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    def xmlrpc_edit_pool(self, args):
        """ Edit pool.
        """

        try:
            return self.nap.edit_pool(args.get('schema'), args.get('pool'), args.get('attr'))
        except nap.NapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    def xmlrpc_search_pool(self, args):
        """ Search for pools.

            The 'query' input is a specially crafted dict/struct which
            permits quite flexible searches.
        """

        try:
            return self.nap.search_pool(args.get('schema'), args.get('query'), args.get('search_options'))
        except nap.NapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    def xmlrpc_smart_search_pool(self, args):
        """ Perform a smart search.

            The smart search function tries to extract a query from a text
            string. This query is then passed to the search_prefix function,
            which performs the actual search.
        """

        try:
            return self.nap.smart_search_pool(args.get('schema'), args.get('query_string'), args.get('search_options'))
        except nap.NapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    #
    # PREFIX FUNCTIONS
    #


    def xmlrpc_add_prefix(self, args):
        """ Add a prefix.
        """

        try:
            return self.nap.add_prefix(args.get('schema'), args.get('attr'), args.get('args'))
        except nap.NapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))



    def xmlrpc_list_prefix(self, args):
        """ List prefixes.
        """

        try:
            return self.nap.list_prefix(args.get('schema'), args.get('prefix'))
        except nap.NapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))



    def xmlrpc_edit_prefix(self, args):
        """ Edit prefix.
        """

        try:
            return self.nap.edit_prefix(args.get('schema'), args.get('prefix'), args.get('attr'))
        except nap.NapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))



    def xmlrpc_remove_prefix(self, args):
        """ Remove a prefix.
        """

        try:
            return self.nap.remove_prefix(args.get('schema'), args.get('prefix'))
        except nap.NapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))



    def xmlrpc_search_prefix(self, args):
        """ Search for prefixes.

            The 'query' input is a specially crafted dict/struct which
            permits quite flexible searches.
        """

        try:
            return self.nap.search_prefix(args.get('schema'), args.get('query'), args.get('search_options'))
        except nap.NapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))



    def xmlrpc_smart_search_prefix(self, args):
        """ Perform a smart search.

            The smart search function tries to extract a query from a text
            string. This query is then passed to the search_prefix function,
            which performs the actual search.
        """

        try:
            return self.nap.smart_search_prefix(args.get('schema'), args.get('query_string'), args.get('search_options'))
        except nap.NapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))



    def xmlrpc_find_free_prefix(self, args):
        """ Find a free prefix.
        """

        try:
            return self.nap.find_free_prefix(args.get('schema'), args.get('args'))
        except nap.NapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))
