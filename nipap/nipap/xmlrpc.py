# vim: et :
""" XML-RPC glue class
    ==================

    This module contains a "glue class" used by Twisted to export the NIPAP API functions over XML-RPC.

    For a detailed description of the API, see :doc:`nipap`.
"""
from twisted.web import http, xmlrpc, server
from twisted.internet import defer, protocol, reactor
import logging
import xmlrpclib
from nipapconfig import NipapConfig

import nipap
from authlib import AuthFactory


class NipapXMLRPC:
    stop = None
    _cfg = None

    def __init__(self):
        self._cfg = NipapConfig()


    def run(self):

        # most signals are handled by Twisted by default but for SIGHUP to
        # behave as we want (ie, reload the configuration file) we need to
        # install a custom handler
        import signal
        signal.signal(signal.SIGHUP, self.sigHup)

        from twisted.internet import reactor
        protocol = NipapProtocol()
        reactor.listenTCP(self._cfg.getint('nipapd', 'port'), server.Site(protocol))
        reactor.run()

    def _sigHup(self, num, frame):
        """ Customer signal handler for SIGHUP
        """
        # TODO: refactor the program so that we may reload the configuration
        #       file here
        pass


class NipapProtocol(xmlrpc.XMLRPC):
    """ Class to allow XML-RPC access to the lovely NIPAP system.
    """

    def __init__(self):
        xmlrpc.XMLRPC.__init__(self)
        self.allowNone = True
        self.request = None
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Initialising NIPAP Protocol")

        self.nipap = nipap.Nipap()


    def render(self, request):
        self.request = request

        request.content.seek(0, 0)
        args, functionPath = xmlrpclib.loads(request.content.read())

        # Authentication
        #
        # Fetch auth options from args
        auth_options = {}
        nipap_args = {}

        if len(args) > 0:
            nipap_args = args[0]
        if type(nipap_args) == dict:
            auth_options = nipap_args.get('auth')

        auth = AuthFactory.get_auth(request.getUser(), request.getPassword(), auth_options.get('authoritative_source'), auth_options or {})

        if not auth.authenticate():
            request.setResponseCode(http.UNAUTHORIZED)
            return "Authentication failed."
        # this will throw an error later on - don't worry
        try:
            args[0]['auth'] = auth
        except:
            pass

        # TODO: handle wrong number of arguments - should just be one

        # Authentication done
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
            return self.nipap.add_schema(args.get('auth'), args.get('attr'))
        except nipap.NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    def xmlrpc_remove_schema(self, args):
        """ Removes a schema.
        """

        try:
            self.nipap.remove_schema(args.get('auth'), args.get('schema'))
        except nipap.NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    def xmlrpc_list_schema(self, args = {}):
        """ List schemas.
        """

        try:
            return self.nipap.list_schema(args.get('auth'), args.get('schema'))
        except nipap.NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    def xmlrpc_edit_schema(self, args):
        """ Edit a schema.
        """

        try:
            self.nipap.edit_schema(args.get('auth'), args.get('schema'), args.get('attr'))
        except nipap.NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    def xmlrpc_search_schema(self, args):
        """ Search for schemas.

            The 'query' input is a specially crafted dict/struct which
            permits quite flexible searches.
        """

        try:
            return self.nipap.search_schema(args.get('auth'), args.get('query'), args.get('search_options'))
        except nipap.NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    def xmlrpc_smart_search_schema(self, args):
        """ Perform a smart search.

            The smart search function tries to extract a query from a text
            string. This query is then passed to the search_prefix function,
            which performs the actual search.
        """

        try:
            return self.nipap.smart_search_schema(args.get('auth'), args.get('query_string'), args.get('search_options'))
        except nipap.NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    #
    # POOL FUNCTIONS
    #
    def xmlrpc_add_pool(self, args):
        """ Add a pool.
        """

        try:
            return self.nipap.add_pool(args.get('auth'), args.get('schema'), args.get('attr'))
        except nipap.NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    def xmlrpc_remove_pool(self, args):
        """ Remove a pool.
        """

        try:
            self.nipap.remove_pool(args.get('auth'), args.get('schema'), args.get('pool'))
        except nipap.NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    def xmlrpc_list_pool(self, args):
        """ List pools.
        """

        try:
            return self.nipap.list_pool(args.get('auth'), args.get('schema'), args.get('pool'))
        except nipap.NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    def xmlrpc_edit_pool(self, args):
        """ Edit pool.
        """

        try:
            return self.nipap.edit_pool(args.get('auth'), args.get('schema'), args.get('pool'), args.get('attr'))
        except nipap.NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    def xmlrpc_search_pool(self, args):
        """ Search for pools.

            The 'query' input is a specially crafted dict/struct which
            permits quite flexible searches.
        """

        try:
            return self.nipap.search_pool(args.get('auth'), args.get('schema'), args.get('query'), args.get('search_options'))
        except nipap.NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    def xmlrpc_smart_search_pool(self, args):
        """ Perform a smart search.

            The smart search function tries to extract a query from a text
            string. This query is then passed to the search_prefix function,
            which performs the actual search.
        """

        try:
            return self.nipap.smart_search_pool(args.get('auth'), args.get('schema'), args.get('query_string'), args.get('search_options'))
        except nipap.NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    #
    # PREFIX FUNCTIONS
    #


    def xmlrpc_add_prefix(self, args):
        """ Add a prefix.
        """

        try:
            return self.nipap.add_prefix(args.get('auth'), args.get('schema'), args.get('attr'), args.get('args'))
        except nipap.NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))



    def xmlrpc_list_prefix(self, args):
        """ List prefixes.
        """

        try:
            return self.nipap.list_prefix(args.get('auth'), args.get('schema'), args.get('prefix'))
        except nipap.NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))



    def xmlrpc_edit_prefix(self, args):
        """ Edit prefix.
        """

        try:
            return self.nipap.edit_prefix(args.get('auth'), args.get('schema'), args.get('prefix'), args.get('attr'))
        except nipap.NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))



    def xmlrpc_remove_prefix(self, args):
        """ Remove a prefix.
        """

        try:
            return self.nipap.remove_prefix(args.get('auth'), args.get('schema'), args.get('prefix'))
        except nipap.NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))



    def xmlrpc_search_prefix(self, args):
        """ Search for prefixes.

            The 'query' input is a specially crafted dict/struct which
            permits quite flexible searches.
        """

        try:
            return self.nipap.search_prefix(args.get('auth'), args.get('schema'), args.get('query'), args.get('search_options'))
        except nipap.NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))



    def xmlrpc_smart_search_prefix(self, args):
        """ Perform a smart search.

            The smart search function tries to extract a query from a text
            string. This query is then passed to the search_prefix function,
            which performs the actual search.
        """

        try:
            return self.nipap.smart_search_prefix(args.get('auth'), args.get('schema'), args.get('query_string'), args.get('search_options'))
        except nipap.NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))



    def xmlrpc_find_free_prefix(self, args):
        """ Find a free prefix.
        """

        try:
            return self.nipap.find_free_prefix(args.get('auth'), args.get('schema'), args.get('args'))
        except nipap.NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))
