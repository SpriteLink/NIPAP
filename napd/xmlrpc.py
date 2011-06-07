# vim: et :
from twisted.web import http, xmlrpc, server
from twisted.internet import defer, protocol, reactor
import logging
import xmlrpclib

import nap

# map exception types to error codes, used for 
# creating suitable xmlrpclib.Fault-objects
# TODO: there are normal python ValueErrors raised, catch them too! make sure
#       we don't leak internal information in the exception and if possible try
#       to point out which argument (if any) caused the exception
errcode_map = {
    nap.NapError: 1000,
    nap.NapInputError: 1100,
    nap.NapMissingInputError: 1110,
    nap.NapExtraneousInputError: 1120,
    nap.NapValueError: 1200,
}


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
#        self.con_pg = psycopg2.connect("host='localhost' dbname='nap' user='nap' password='Je9ydmLsBw7gg'")
#        self.curs_pg = self.con_pg.cursor()

        self.nap = nap.Nap()


    def render(self, request):
        llf = "XMLRPC render: "
        lle = llf + "Authentication failed: "
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


    def xmlrpc_echo(self, args = []):
        if 'message' in args:
            return { 'result': 'success', 'message': 'Echo from NAPD: ' + args['message'] }

        return { 'result': 'success', 'message': "This is an echo function, if you pass me a string in the argument named 'message', I will return it to you" }

    
    #
    # SCHEMA FUNCTIONS
    #
    def xmlrpc_add_schema(self, attr):
        """ Add a new network schema.
        """

        try:
            return self.nap.add_schema(attr)
        except nap.NapError, e:
            return xmlrpclib.Fault(errcode_map[type(e)], str(e))


    def xmlrpc_remove_schema(self, spec):
        """ Removes a schema.
        """

        try:
            self.nap.remove_schema(spec)
        except nap.NapError, e:
            return xmlrpclib.Fault(errcode_map[type(e)], str(e))


    def xmlrpc_list_schema(self, spec=None):
        """ List schemas.
        """

        try:
            return self.nap.list_schema(spec)
        except nap.NapError, e:
            return xmlrpclib.Fault(errcode_map[type(e)], str(e))

    
    def xmlrpc_edit_schema(self, spec, attr):
        """ Edit a schema.
        """

        try:
            self.nap.edit_schema(spec, attr)
        except nap.NapError, e:
            return xmlrpclib.Fault(errcode_map[type(e)], str(e))

    #
    # POOL FUNCTIONS
    #
    def xmlrpc_add_pool(self, attr):
        """ Add a pool.
        """

        try:
            return self.nap.add_pool(attr)
        except nap.NapError, e:
            return xmlrpclib.Fault(errcode_map[type(e)], str(e))


    def xmlrpc_remove_pool(self, spec):
        """ Remove a pool.
        """

        try:
            self.nap.remove_pool(spec)
        except nap.NapError, e:
            return xmlrpclib.Fault(errcode_map[type(e)], str(e))


    def xmlrpc_list_pool(self, spec=None):
        """ List pools.
        """

        try:
            return self.nap.list_pool(spec)
        except nap.NapError, e:
            return xmlrpclib.Fault(errcode_map[type(e)], str(e))


    def xmlrpc_edit_pool(self, spec, attr):
        """ Edit pool.
        """

        try:
            return self.nap.edit_pool(spec, attr)
        except nap.NapError, e:
            return xmlrpclib.Fault(errcode_map[type(e)], str(e))


    #
    # PREFIX FUNCTIONS
    #


    def xmlrpc_add_prefix(self, attr):
        """ Add a prefix. 
        """

        try:
            return self.nap.add_prefix(spec, attr)
        except nap.NapError, e:
            return xmlrpclib.Fault(errcode_map[type(e)], str(e))


    def xmlrpc_list_prefix(self, spec):
        """ List prefixes.
        """

        try:
            return self.nap.list_prefix(spec)
        except nap.NapError, e:
            return xmlrpclib.Fault(errcode_map[type(e)], str(e))


    def xmlrpc_edit_prefix(self, spec, attr):
        """ Edit prefix.
        """

        try:
            return self.nap.edit_prefix(spec)
        except nap.NapError, e:
            return xmlrpclib.Fault(errcode_map[type(e)], str(e))


    def xmlrpc_remove_prefix(self, spec):
        """ Remove a prefix.
        """

        try:
            return self.nap.edit_prefix(spec)
        except nap.NapError, e:
            return xmlrpclib.Fault(errcode_map[type(e)], str(e))


    def xmlrpc_find_free_prefix(self, spec, wanted_length, num = 1):
        """ Find a free prefix.
        """

        try:
            return self.nap.find_free_prefix(spec, wantd_length, num)
        except nap.NapError, e:
            return xmlrpclib.Fault(errcode_map[type(e)], str(e))

