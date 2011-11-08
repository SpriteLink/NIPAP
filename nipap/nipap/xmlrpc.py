# vim: et :
""" XML-RPC glue class
    ==================

    This module contains a "glue class" used by Twisted to export the NIPAP API
    functions over XML-RPC.

    Each function call takes only one argument, an XML-RPC struct which
    contains the function arguments which are passed on to the
    :class:`Nipap`-class.

    For a detailed description of the API functions, see :doc:`nipap`.

    Authentication
    --------------
    Authentication is implemented using basic HTTP authentication. The user
    credentials are passed to the :class:`AuthFactory` class together with the
    (optional) auth argument from the arguments-dict. If the authentication
    fails a HTTP 401 is returned.

    See the :doc:`authlib` documentation for a detailed explanation of how the
    authentication system works.

    Classes
    -------
"""
from twisted.web import http, xmlrpc, server
from twisted.internet import defer, protocol, reactor
import logging
import xmlrpclib
from nipapconfig import NipapConfig

import nipap
from authlib import AuthFactory, AuthError


class NipapXMLRPC:
    stop = None
    _cfg = None
    root_logger = None

    def __init__(self, root_logger = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.root_logger = root_logger

        self._cfg = NipapConfig()
        self.cfg_file = None

        # Add dispatch entry for <ex:nil/>
        xmlrpclib.Unmarshaller.dispatch["ex:nil"] = xmlrpclib.Unmarshaller.end_nil

        self.init()


    def init(self):
        """ Non Python init

            This init function should be called after the configuration has
            been read. It is a separate function from __init__ so that it may
            be called if the configuration file is reread when the daemon is
            running.
        """
        # we cannot switch between foreground and background here, so ignoring
        # 'foreground' option

        # syslog
        if self._cfg.getboolean('nipapd', 'syslog'):
            log_syslog = logging.handlers.SysLogHandler(address = '/dev/log')
            log_syslog.setFormatter(logging.Formatter("%(levelname)-8s %(message)s"))
            self.root_logger.addHandler(log_syslog)

        if self._cfg.getboolean('nipapd', 'foreground'):
            # log to stdout
            log_stream = logging.StreamHandler()
            log_stream.setFormatter(logging.Formatter("%(asctime)s: %(levelname)-8s %(message)s"))
            self.root_logger.addHandler(log_stream)
            self.root_logger.setLevel(logging.DEBUG)

        if self._cfg.getboolean('nipapd', 'debug'):
            self.root_logger.setLevel(logging.DEBUG)



    def run(self):
        """ Create the reactor and start it
        """

        # most signals are handled by Twisted by default but for SIGHUP to
        # behave as we want (ie, reload the configuration file) we need to
        # install a custom handler
        import signal
        signal.signal(signal.SIGHUP, self._sigHup)

        from twisted.internet import reactor
        protocol = NipapProtocol()
        reactor.listenTCP(self._cfg.getint('nipapd', 'port'), server.Site(protocol))
        reactor.run()



    def _sigHup(self, num, frame):
        """ Customer signal handler for SIGHUP
        """
        self.logger.info("Received SIGHUP - reloading configuration")
        self._cfg.read_file()
        self.init()



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

        try:
            auth = AuthFactory.get_auth(request.getUser(), request.getPassword(), auth_options.get('authoritative_source'), auth_options or {})
        except AuthError, exp:
            self.logger.error("Unable to get auth object: %s" % str(exp))
            request.setResponseCode(http.UNAUTHORIZED)
            return "Authentication error."


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

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `attr` [struct]
                Schema attributes.

            Returns the schema ID.
        """

        try:
            return self.nipap.add_schema(args.get('auth'), args.get('attr'))
        except nipap.NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    def xmlrpc_remove_schema(self, args):
        """ Removes a schema.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `schema` [struct]
                A schema spec.
        """

        try:
            self.nipap.remove_schema(args.get('auth'), args.get('schema'))
        except nipap.NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    def xmlrpc_list_schema(self, args = {}):
        """ List schemas.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `schema` [struct]
                Specifies schema attributes to match (optional).

            Returns a list of structs matching the schema spec.
        """

        try:
            return self.nipap.list_schema(args.get('auth'), args.get('schema'))
        except nipap.NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    def xmlrpc_edit_schema(self, args):
        """ Edit a schema.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `schema` [struct]
                A schema spec specifying which schema(s) to edit.
            * `attr` [struct]
                Schema attributes.
        """

        try:
            self.nipap.edit_schema(args.get('auth'), args.get('schema'), args.get('attr'))
        except nipap.NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    def xmlrpc_search_schema(self, args):
        """ Search for schemas.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `query` [struct]
                A struct specifying the search query.
            * `search_options` [struct]
                Options for the search query, such as limiting the number
                of results returned.

            Returns a struct containing search result and the search options
            used.
        """

        try:
            return self.nipap.search_schema(args.get('auth'), args.get('query'), args.get('search_options'))
        except nipap.NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    def xmlrpc_smart_search_schema(self, args):
        """ Perform a smart search.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `query_string` [string]
                The search string.
            * `search_options` [struct]
                Options for the search query, such as limiting the number
                of results returned.

            Returns a struct containing search result, interpretation of the
            search string and the search options used.
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

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `schema` [struct]
                Schema to work in.
            * `attr` [struct]
                Attributes which will be set on the new pool.

            Returns ID of created pool.
        """

        try:
            return self.nipap.add_pool(args.get('auth'), args.get('schema'), args.get('attr'))
        except nipap.NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    def xmlrpc_remove_pool(self, args):
        """ Remove a pool.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `schema` [struct]
                Schema to work in.
            * `pool` [struct]
                Specifies what pool(s) to remove.
        """

        try:
            self.nipap.remove_pool(args.get('auth'), args.get('schema'), args.get('pool'))
        except nipap.NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    def xmlrpc_list_pool(self, args):
        """ List pools.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `schema` [struct]
                Schema to work in.
            * `pool` [struct]
                Specifies pool attributes which will be matched.

            Returns a list of structs describing the matching pools.
        """

        try:
            return self.nipap.list_pool(args.get('auth'), args.get('schema'), args.get('pool'))
        except nipap.NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    def xmlrpc_edit_pool(self, args):
        """ Edit pool.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `schema` [struct]
                Schema to work in.
            * `pool` [struct]
                Specifies pool attributes to match.
            * `attr` [struct]
                Pool attributes to set.
        """

        try:
            return self.nipap.edit_pool(args.get('auth'), args.get('schema'), args.get('pool'), args.get('attr'))
        except nipap.NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    def xmlrpc_search_pool(self, args):
        """ Search for pools.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `schema` [struct]
                Schema to work in.
            * `query` [struct]
                A struct specifying the search query.
            * `search_options` [struct]
                Options for the search query, such as limiting the number
                of results returned.

            Returns a struct containing search result and the search options
            used.
        """

        try:
            return self.nipap.search_pool(args.get('auth'), args.get('schema'), args.get('query'), args.get('search_options'))
        except nipap.NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    def xmlrpc_smart_search_pool(self, args):
        """ Perform a smart search.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `schema` [struct]
                Schema to work in.
            * `query` [string]
                The search string.
            * `search_options` [struct]
                Options for the search query, such as limiting the number
                of results returned.

            Returns a struct containing search result, interpretation of the
            query string and the search options used.
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

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `schema` [struct]
                Schema to work in.
            * `attr` [struct]
                Attributes to set on the new prefix.
            * `args` [srgs]
                Arguments for addition of prefix, such as what pool or prefix
                it should be allocated from.

            Returns ID of created prefix.
        """

        try:
            return self.nipap.add_prefix(args.get('auth'), args.get('schema'), args.get('attr'), args.get('args'))
        except nipap.NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))



    def xmlrpc_list_prefix(self, args):
        """ List prefixes.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `schema` [struct]
                Schema to work in.
            * `prefix` [struct]
                Prefix attributes to match.

            Returns a list of structs describing the matching prefixes.
        """

        try:
            return self.nipap.list_prefix(args.get('auth'), args.get('schema'), args.get('prefix'))
        except nipap.NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))



    def xmlrpc_edit_prefix(self, args):
        """ Edit prefix.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `schema` [struct]
                Schema to work in.
            * `prefix` [struct]
                Prefix attributes which describes what prefix(es) to edit.
            * `attr` [struct]
                Attribuets to set on the new prefix.
        """

        try:
            return self.nipap.edit_prefix(args.get('auth'), args.get('schema'), args.get('prefix'), args.get('attr'))
        except nipap.NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))



    def xmlrpc_remove_prefix(self, args):
        """ Remove a prefix.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `schema` [struct]
                Schema to work in.
            * `prefix` [struct]
                Attributes used to select what prefix to remove.
        """

        try:
            return self.nipap.remove_prefix(args.get('auth'), args.get('schema'), args.get('prefix'))
        except nipap.NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))



    def xmlrpc_search_prefix(self, args):
        """ Search for prefixes.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `schema` [struct]
                Schema to work in.
            * `query` [struct]
                A struct specifying the search query.
            * `search_options` [struct]
                Options for the search query, such as limiting the number
                of results returned.

            Returns a struct containing the search result together with the
            search options used.
        """

        try:
            return self.nipap.search_prefix(args.get('auth'), args.get('schema'), args.get('query'), args.get('search_options'))
        except nipap.NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))



    def xmlrpc_smart_search_prefix(self, args):
        """ Perform a smart search.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `schema` [struct]
                Schema to work in.
            * `query` [string]
                The search string.
            * `search_options` [struct]
                Options for the search query, such as limiting the number
                of results returned.

            Returns a struct containing search result, interpretation of the
            query string and the search options used.
        """

        try:
            return self.nipap.smart_search_prefix(args.get('auth'), args.get('schema'), args.get('query_string'), args.get('search_options'))
        except nipap.NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))



    def xmlrpc_find_free_prefix(self, args):
        """ Find a free prefix.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `schema` [struct]
                Schema to work in.
            * `args` [struct]
                Arguments for the find_free_prefix-function such as what prefix
                or pool to allocate from.
        """

        try:
            return self.nipap.find_free_prefix(args.get('auth'), args.get('schema'), args.get('args'))
        except nipap.NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))
