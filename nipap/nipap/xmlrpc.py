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
import twisted
import twisted.python.versions
from twisted.web import http, xmlrpc, server
from twisted.internet import defer, protocol, reactor
from twisted.python import log
import logging
import xmlrpclib
from nipapconfig import NipapConfig

from backend import Nipap, NipapError
import nipap
from authlib import AuthFactory, AuthError


class NipapXMLRPC:

    stop = None
    _cfg = None
    _protocol = None
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

        if self._cfg.getboolean('nipapd', 'debug'):
            self.root_logger.setLevel(logging.DEBUG)



    def run(self):
        """ Create the reactor and start it
        """

        # most signals are handled by Twisted by default but for SIGHUP to
        # behave as we want (ie, reload the configuration file) we need to
        # install a custom handler
        import signal
        signal.signal(signal.SIGHUP, self._sighup)

        # setup twisted logging
        log.defaultObserver.stop()
        log.defaultObserver = None
        observer = log.PythonLoggingObserver()
        observer.start()

        # twist it!
        self._protocol = NipapProtocol()
        # listen on all interface
        if self._cfg.get('nipapd', 'listen') is None or self._cfg.get('nipapd', 'listen') == '':
            self.logger.info("Listening to all addresses on port " + self._cfg.getint('nipapd', 'port'))
            reactor.listenTCP(self._cfg.getint('nipapd', 'port'), server.Site(self._protocol))
        else:
            # If the used has listed specific addresses to listen to, loop
            # through them and start listening to them. It is possible to
            # specify port per IP by separating the address and port with a +
            # character.
            listen = self._cfg.get('nipapd', 'listen')
            for entry in listen.split(','):
                if len(entry.split('+')) > 1:
                    address = entry.split('+')[0]
                    port = int(entry.split('+')[1])
                else:
                    address = entry
                    port = int(self._cfg.get('nipapd', 'port'))
                self.logger.info("Listening to address " + address + " on port " + str(port))
                reactor.listenTCP(port, server.Site(self._protocol), interface=address)

        # finally, start the reactor!
        reactor.run()



    def _sighup(self, num, frame):
        """ Custom signal handler for SIGHUP
        """
        self.logger.info("Received SIGHUP - reloading configuration")
        self._cfg.read_file()
        self._protocol._auth_fact.reload()
        self.init()



class NipapProtocol(xmlrpc.XMLRPC):
    """ Class to allow XML-RPC access to the lovely NIPAP system.
    """

    _auth_fact = None

    def __init__(self):
        xmlrpc.XMLRPC.__init__(self)
        self.allowNone = True
        self.request = None
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Initialising NIPAP Protocol")

        self.nipap = Nipap()
        self._auth_fact = AuthFactory()


    def render(self, request):

        request.content.seek(0, 0)
        args, functionPath = xmlrpclib.loads(request.content.read())

        # Authentication
        #
        # Fetch auth options from args
        auth_options = {}
        nipap_args = {}

        # validate function arguments
        if len(args) == 1:
            nipap_args = args[0]
        else:
            self.logger.info("Malformed request: got %d parameters" % len(args))
            f = xmlrpclib.Fault(1000, ("NIPAP API functions take exactly 1 "
                "argument (%d given)") % len(args))
            self._cbRender(f, request)
            return server.NOT_DONE_YET

        if type(nipap_args) != dict:
            f = xmlrpclib.Fault(1000, ("Function argument must be XML-RPC "
                "struct/Python dict (Python %s given)." %
                type(nipap_args).__name__ ))
            self._cbRender(f, request)
            return server.NOT_DONE_YET

        # fetch auth options
        try:
            auth_options = nipap_args['auth']
            if type(auth_options) is not dict:
                raise ValueError()
        except (KeyError, ValueError):
            f = xmlrpclib.Fault(1000,
                ("Missing/invalid authentication options in request."))
            self._cbRender(f, request)
            return server.NOT_DONE_YET

        # fetch authoritative source
        try:
            auth_source = auth_options['authoritative_source']
        except KeyError:
            f = xmlrpclib.Fault(1000,
                ("Missing authoritative source in auth options."))
            self._cbRender(f, request)
            return server.NOT_DONE_YET

        # fetch auth object for session
        try:
            auth = self._auth_fact.get_auth(request.getUser(), request.getPassword(), auth_source, auth_options or {})
        except AuthError, exp:
            self.logger.error("Authentication failed: %s" % str(exp))
            request.setResponseCode(http.UNAUTHORIZED)
            return "Authentication error."

        # authenticated?
        if not auth.authenticate():
            request.setResponseCode(http.UNAUTHORIZED)
            return "Authentication failed."

        # Replace auth options in API call arguments with auth object
        try:
            args[0]['auth'] = auth
        except:
            pass

        # Authentication done
        ver = twisted.python.versions.Version('twisted', 11, 1, 0)
        try:
            if twisted._version.version >= ver:
                function = self.lookupProcedure(functionPath)
            else:
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



    def xmlrpc_echo(self, args):
        """ An echo function

            An API test function which simply echoes what is is passed in the
            'message' element in the args-dict..

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `message` [string]
                String to echo.

            Returns a string.
        """
        if args.get('message') is not None:
            return args.get('message')

        return ("This is an echo function, if you pass me a string in the "
            "argument 'message', I will return it to you")



    def xmlrpc_version(self, args):
        """ Returns nipapd version

            Returns a string.
        """

        return nipap.__version__



    #
    # VRF FUNCTIONS
    #
    def xmlrpc_add_vrf(self, args):
        """ Add a new VRF.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `attr` [struct]
                VRF attributes.

            Returns the internal database ID for the VRF.
        """

        try:
            return self.nipap.add_vrf(args.get('auth'), args.get('attr'))
        except NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    def xmlrpc_remove_vrf(self, args):
        """ Removes a VRF.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `vrf` [struct]
                A VRF spec.
        """

        try:
            self.nipap.remove_vrf(args.get('auth'), args.get('vrf'))
        except NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    def xmlrpc_list_vrf(self, args):
        """ List VRFs.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `vrf` [struct]
                Specifies VRF attributes to match (optional).

            Returns a list of structs matching the VRF spec.
        """

        try:
            return self.nipap.list_vrf(args.get('auth'), args.get('vrf'))
        except NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    def xmlrpc_edit_vrf(self, args):
        """ Edit a VRF.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `vrf` [struct]
                A VRF spec specifying which VRF(s) to edit.
            * `attr` [struct]
                VRF attributes.
        """

        try:
            return self.nipap.edit_vrf(args.get('auth'), args.get('vrf'), args.get('attr'))
        except NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    def xmlrpc_search_vrf(self, args):
        """ Search for VRFs.

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
            return self.nipap.search_vrf(args.get('auth'), args.get('query'), args.get('search_options') or {})
        except NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    def xmlrpc_smart_search_vrf(self, args):
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
            return self.nipap.smart_search_vrf(args.get('auth'),
                    args.get('query_string'), args.get('search_options', {}),
                    args.get('extra_query'))
        except NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    #
    # POOL FUNCTIONS
    #
    def xmlrpc_add_pool(self, args):
        """ Add a pool.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `attr` [struct]
                Attributes which will be set on the new pool.

            Returns ID of created pool.
        """

        try:
            return self.nipap.add_pool(args.get('auth'), args.get('attr'))
        except NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    def xmlrpc_remove_pool(self, args):
        """ Remove a pool.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `pool` [struct]
                Specifies what pool(s) to remove.
        """

        try:
            self.nipap.remove_pool(args.get('auth'), args.get('pool'))
        except NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    def xmlrpc_list_pool(self, args):
        """ List pools.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `pool` [struct]
                Specifies pool attributes which will be matched.

            Returns a list of structs describing the matching pools.
        """

        try:
            return self.nipap.list_pool(args.get('auth'), args.get('pool'))
        except NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    def xmlrpc_edit_pool(self, args):
        """ Edit pool.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `pool` [struct]
                Specifies pool attributes to match.
            * `attr` [struct]
                Pool attributes to set.
        """

        try:
            return self.nipap.edit_pool(args.get('auth'), args.get('pool'), args.get('attr'))
        except NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    def xmlrpc_search_pool(self, args):
        """ Search for pools.

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
            return self.nipap.search_pool(args.get('auth'), args.get('query'), args.get('search_options') or {})
        except NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    def xmlrpc_smart_search_pool(self, args):
        """ Perform a smart search.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `query` [string]
                The search string.
            * `search_options` [struct]
                Options for the search query, such as limiting the number
                of results returned.

            Returns a struct containing search result, interpretation of the
            query string and the search options used.
        """

        try:
            return self.nipap.smart_search_pool(args.get('auth'),
                    args.get('query_string'), args.get('search_options') or {},
                    args.get('extra_query', {}))
        except NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))


    #
    # PREFIX FUNCTIONS
    #


    def xmlrpc_add_prefix(self, args):
        """ Add a prefix.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `attr` [struct]
                Attributes to set on the new prefix.
            * `args` [srgs]
                Arguments for addition of prefix, such as what pool or prefix
                it should be allocated from.

            Returns ID of created prefix.
        """

        try:
            return self.nipap.add_prefix(args.get('auth'), args.get('attr'), args.get('args'))
        except NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))



    def xmlrpc_list_prefix(self, args):
        """ List prefixes.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `prefix` [struct]
                Prefix attributes to match.

            Returns a list of structs describing the matching prefixes.
        """

        try:
            return self.nipap.list_prefix(args.get('auth'), args.get('prefix') or {})
        except NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))



    def xmlrpc_edit_prefix(self, args):
        """ Edit prefix.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `prefix` [struct]
                Prefix attributes which describes what prefix(es) to edit.
            * `attr` [struct]
                Attribuets to set on the new prefix.
        """

        try:
            return self.nipap.edit_prefix(args.get('auth'), args.get('prefix'), args.get('attr'))
        except NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))



    def xmlrpc_remove_prefix(self, args):
        """ Remove a prefix.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `prefix` [struct]
                Attributes used to select what prefix to remove.
        """

        try:
            return self.nipap.remove_prefix(args.get('auth'), args.get('prefix'), args.get('recursive'))
        except NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))



    def xmlrpc_search_prefix(self, args):
        """ Search for prefixes.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `query` [struct]
                A struct specifying the search query.
            * `search_options` [struct]
                Options for the search query, such as limiting the number
                of results returned.

            Returns a struct containing the search result together with the
            search options used.
        """

        try:
            return self.nipap.search_prefix(args.get('auth'), args.get('query'), args.get('search_options') or {})
        except NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))



    def xmlrpc_smart_search_prefix(self, args):
        """ Perform a smart search.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `query_string` [string]
                The search string.
            * `search_options` [struct]
                Options for the search query, such as limiting the number
                of results returned.
            * `extra_query` [struct]
                Extra search terms, will be AND:ed together with what is
                extracted from the query string.

            Returns a struct containing search result, interpretation of the
            query string and the search options used.
        """

        try:
            return self.nipap.smart_search_prefix(args.get('auth'),
                    args.get('query_string'), args.get('search_options') or {},
                    args.get('extra_query'))
        except NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))



    def xmlrpc_find_free_prefix(self, args):
        """ Find a free prefix.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `args` [struct]
                Arguments for the find_free_prefix-function such as what prefix
                or pool to allocate from.
        """

        try:
            return self.nipap.find_free_prefix(args.get('auth'), args.get('vrf'), args.get('args'))
        except NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))



    #
    # ASN FUNCTIONS
    #
    def xmlrpc_add_asn(self, args):
        """ Add a new ASN.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `attr` [struct]
                ASN attributes.

            Returns the ASN.
        """

        try:
            return self.nipap.add_asn(args.get('auth'), args.get('attr'))
        except NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))



    def xmlrpc_remove_asn(self, args):
        """ Removes an ASN.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `asn` [integer]
                An ASN.
        """

        try:
            self.nipap.remove_asn(args.get('auth'), args.get('asn'))
        except NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))



    def xmlrpc_list_asn(self, args):
        """ List ASNs.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `asn` [struct]
                Specifies ASN attributes to match (optional).

            Returns a list of ASNs matching the ASN spec as a list of structs.
        """

        try:
            return self.nipap.list_asn(args.get('auth'), args.get('asn') or {})
        except NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))



    def xmlrpc_edit_asn(self, args):
        """ Edit an ASN.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `asn` [integer]
                An integer specifying which ASN to edit.
            * `attr` [struct]
                ASN attributes.
        """

        try:
            return self.nipap.edit_asn(args.get('auth'), args.get('asn'), args.get('attr'))
        except NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))



    def xmlrpc_search_asn(self, args):
        """ Search ASNs.

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
            return self.nipap.search_asn(args.get('auth'), args.get('query'), args.get('search_options') or {})
        except NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))



    def xmlrpc_smart_search_asn(self, args):
        """ Perform a smart search among ASNs.

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
            return self.nipap.smart_search_asn(args.get('auth'), args.get('query_string'), args.get('search_options') or {})
        except NipapError, e:
            return xmlrpclib.Fault(e.error_code, str(e))



# vim: et :
