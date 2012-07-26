"""
    pynipap - a Python NIPAP client library
    =======================================

    pynipap is a Python client library for the NIPAP IP address planning
    system. It is structured as a simple ORM.

    There are three ORM-classes:

    * :class:`Schema`
    * :class:`Pool`
    * :class:`Prefix`

    Each of these maps to the NIPAP objects with the same name. See the main
    NIPAP API documentation for an overview of the different object types and
    what they are used for.

    There are also a few supporting classes:

    * :class:`AuthOptions` - Authentication options.

    And a bunch of exceptions:

    * :class:`NipapError`
    * :class:`NipapNonExistentError`
    * :class:`NipapInputError`
    * :class:`NipapMissingInputError`
    * :class:`NipapExtraneousInputError`
    * :class:`NipapNoSuchOperatorError`
    * :class:`NipapValueError`
    * :class:`NipapDuplicateError`

    General usage
    -------------
    pynipap has been designed to be very simple to use and rapid to get about using.

    Preparations
    ^^^^^^^^^^^^
    Make sure that pynipap is accessible in your `sys.path`, you can test it by
    starting a python shell and running::

        import pynipap

    If that works, you are good to go!

    To simplify your code slightly, you can import the individual classes into
    your main namespace::

        import pynipap
        from pynipap import Schema, Pool, Prefix

    Before you can access NIPAP you need to specify the URL to the NIPAP
    XML-RPC service and the authentication options to use for your connection.
    NIPAP has a authentication system which is somewhat involved, see the main
    NIPAP documentation.

    The URL, including the user credentials, is set in the pynipap module variable `xmlrpc_uri` as so::

        pynipap.xmlrpc_uri = "http://user:pass@127.0.0.1:9002"

    The minimum authentication options which we need to set is the
    `authoritative_source` option, which specifies what system is accessing
    NIPAP. This is logged for each query which alters the NIPAP database and
    attached to each prefix which is created or edited. Well-behaved clients
    are required to honor this and verify that the user really want to alter
    the prefix, when trying to edit a prefix which last was edited by another
    system. The :class:`AuthOptions` class is a class with a shared state,
    similar to a singleton class; that is, when a first instance is created
    each consecutive instances will be copies of the first one. In this way the
    authentication options can be accessed from all of the pynipap classes. ::

        a = AuthOptions({
                'authoritative_source': 'my_fancy_nipap_client' 
            })

    After this, we are good to go!

    Accessing data
    ^^^^^^^^^^^^^^

    To fetch data from NIPAP, a set of static methods (@classmethod) has been
    defined in each of the ORM classes. They are:

    * :func:`get` - Get a single object from its ID.
    * :func:`list` - List objects matching a simple criteria.
    * :func:`search` - Perform a full-blown search.
    * :func:`smart_search` - Perform a magic search from a string.

    Each of these functions return either an instance of the requested class
    (:py:class:`Schema`, :class:`Pool`, :class:`Prefix`) or a list of
    instances. The :func:`search` and :func:`smart_search` functions also
    embeds the lists in dicts which contain search meta data.

    The easiest way to get data out of NIPAP is to use the :func:`get`-method,
    given that you know the ID of the object you want to fetch::

        # Fetch schema with ID 1 and print its name
        schema = Schema.get(1)
        print schema.name

    As all pools and prefixes are bound to a schema, all methods for fetching
    these need a schema object which is takes as a first function argument. ::

        # list all pools in the schema
        pools = Pool.list(schema)

        # print the name of the pools
        for p in pools:
            print p.name

    Each of the list functions can also take a `spec`-dict as a second
    argument. With the spec you can perform a simple search operation by
    specifying object attribute values. ::

        # List pools with a default type of 'assignment'
        pools = Pool.list(schema, { 'default_type': 'assignment' })

    Performing searches
    ^^^^^^^^^^^^^^^^^^^
    Commin' up, commin' up.

    Saving changes
    ^^^^^^^^^^^^^^

    Changes made to objects are not automatically saved. To save the changes,
    simply run the object's :func:`save`-method::

        schema.name = "Spam spam spam"
        schema.save()

    Error handling
    --------------

    As is customary in Python applications, an error results in an exception
    being thrown. All pynipap exceptions extend the main exception
    :class:`NipapError`. A goal with the pynipap library has been to make the
    XML-RPC-channel to the backend as transparent as possible, so the XML-RPC
    Faults which the NIPAP server returns in case of errors are converted and
    re-thrown as new exceptions which also they extend :class:`NipapError`,
    for example the NipapDuplicateError which is thrown when a duplicate key
    error occurs in NIPAP.


    Classes
    -------
"""
import xmlrpclib
import logging
import sys
import os

__version__		= "0.8.0"
__author__		= "Kristian Larsson, Lukas Garberg"
__author_email__= "kll@tele2.net, lukas@spritelink.net"
__copyright__	= "Copyright 2011, Kristian Larsson, Lukas Garberg"
__license__		= "MIT"
__status__		= "Development"
__url__			= "http://SpriteLink.github.com/NIPAP"


# This variable holds the URI to the nipap XML-RPC service which will be used.
# It must be set before the Pynipap can be used!
xmlrpc_uri = None

class AuthOptions:
    """ A global-ish authentication option container.

        Note that this essentially is a global variable. If you handle multiple
        queries from different users, you need to make sure that the
        AuthOptions-instances are set to the current user's.
    """

    __shared_state = {}
    options = None

    def __init__(self, options = None):
        """ Create a shared option container.
        """

        self.__dict__ = self.__shared_state

        if options is not None:
            self.options = options



class XMLRPCConnection:
    """ Handles a shared XML-RPC connection.
    """

    __shared_state = {}

    connection = None
    _logger = None


    def __init__(self):
        """ Create XML-RPC connection.

            The connection will be created to the URL set in the module
            variable `xmlrpc_uri`. The instanciation will fail unless this
            variable is set.
        """

        if xmlrpc_uri is None:
            raise NipapError('XML-RPC URI not specified')


        # Currently not used due to threading safety issues
        # after the introduction of the config object above, the code below
        # does not work at all anymore ;)
        #self.__dict__ = self.__shared_state

        #if len(self.__shared_state) == 0 and url is None:
        #    raise Exception("Missing URL.")

        #if len(self.__shared_state) == 0:

        # creating new instance
        self.connection = xmlrpclib.ServerProxy(xmlrpc_uri, allow_none=True)
        self._logger = logging.getLogger(self.__class__.__name__)



class Pynipap:
    """ A base class for the pynipap model classes.

        All Pynipap classes which maps to data in NIPAP (:py:class:Schema,
        :py:class:Pool, :py:class:Prefix) extends this class.
    """

    _xmlrpc = None
    _logger = None
    id = None

    def __eq__(self, other):
        """ Perform test for equality.
        """

        # Only possible if we have ID numbers set
        if self.id is None or other.id is None:
            return false

        return self.id == other.id



    def __init__(self, id=None):
        """ Creats logger and XML-RPC-connection.
        """

        self._logger = logging.getLogger(self.__class__.__name__)
        self._xmlrpc = XMLRPCConnection()
        self._auth_opts = AuthOptions()
        self.id = id



class Schema(Pynipap):
    """ A schema.
    """

    name = None
    """ The name of the schema, as a string.
    """
    description = None
    """ Schema description, as a string.
    """
    vrf = None
    """ VRF where the schema's addresses reside. A string.
    """


    @classmethod
    def list(cls, spec = {}):
        """ List schemas.
        """

        xmlrpc = XMLRPCConnection()
        schema_list = xmlrpc.connection.list_schema(
            {
                'schema': spec,
                'auth': AuthOptions().options
            })

        res = list()
        for schema in schema_list:
            res.append(Schema.from_dict(schema))

        return res


    @classmethod
    def from_dict(cls, parm):
        """ Create new Schema-object from dict.

            Suitable for creating objects from XML-RPC data.
            All available keys must exist.
        """

        s = Schema()
        s.id = parm['id']
        s.name = parm['name']
        s.description = parm['description']
        s.vrf = parm['vrf']
        return s



    @classmethod
    def get(cls, id):
        """ Get the schema with id 'id'.
        """

        # cached?
        if id in _cache['Schema']:
            log.debug('cache hit for schema %d' % id)
            return _cache['Schema'][id]
        log.debug('cache miss for schema %d' % id)

        try:
            schema = Schema.list({ 'id': id })[0]
        except IndexError, e:
            raise NipapNonExistentError('no schema with ID ' + str(id) + ' found')

        _cache['Schema'][id] = schema
        return schema



    @classmethod
    def search(cls, query, search_opts={}):
        """ Search schemas.
        """

        xmlrpc = XMLRPCConnection()
        try:
            search_result = xmlrpc.connection.search_schema(
                {
                    'query': query,
                    'search_options': search_opts,
                    'auth': AuthOptions().options
                })
        except xmlrpclib.Fault, f:
            raise _fault_to_exception(f)
        result = dict()
        result['result'] = []
        result['search_options'] = search_result['search_options']
        for schema in search_result['result']:
            s = Schema.from_dict(schema)
            result['result'].append(s)

        return result



    @classmethod
    def smart_search(cls, query_string, search_options={}):
        """ Perform a smart schema search.
        """

        xmlrpc = XMLRPCConnection()
        try:
            smart_result = xmlrpc.connection.smart_search_schema(
                {
                    'query_string': query_string,
                    'search_options': search_options,
                    'auth': AuthOptions().options
                })
        except xmlrpclib.Fault, f:
            raise _fault_to_exception(f)
        result = dict()
        result['interpretation'] = smart_result['interpretation']
        result['search_options'] = smart_result['search_options']
        result['result'] = list()
        for schema in smart_result['result']:
            p = Schema.from_dict(schema)
            result['result'].append(p)

        return result



    def save(self):
        """ Save changes made to object to NIPAP.
        """

        data = {
            'name': self.name,
            'description': self.description,
            'vrf': self.vrf
        }

        if self.id is None:
            # New object, create
            try:
                self.id = self._xmlrpc.connection.add_schema(
                    {
                        'attr': data,
                        'auth': self._auth_opts.options
                    })
            except xmlrpclib.Fault, f:
                raise _fault_to_exception(f)

        else:
            # Old object, edit
            try:
                self._xmlrpc.connection.edit_schema(
                    {
                        'schema': { 'id': self.id },
                        'attr': data,
                        'auth': self._auth_opts.options
                    })
            except xmlrpclib.Fault, f:
                raise _fault_to_exception(f)

        _cache['Schema'][self.id] = self



    def remove(self):
        """ Remove schema.
        """

        try:
            self._xmlrpc.connection.remove_schema(
                {
                    'schema': { 'id': self.id },
                    'auth': self._auth_opts.options
                })
        except xmlrpclib.Fault, f:
            raise _fault_to_exception(f)
        if self.id in _cache['Schema']:
            del(_cache['Schema'][self.id])



class Pool(Pynipap):
    """ An address pool.
    """

    name = None
    schema = None
    description = None
    default_type = None
    ipv4_default_prefix_length = None
    ipv6_default_prefix_length = None


    def save(self):
        """ Save changes made to pool to NIPAP.
        """

        # verify schema
        if not isinstance(self.schema, Schema):
            raise NipapValueError("missing/invalid schema specified")

        # verify that the schema variable actually contains a schema
        if not isinstance(self.schema, Schema):
            raise NipapValueError("pool does not have a valid schema set")

        data = {
            'name': self.name,
            'description': self.description,
            'default_type': self.default_type,
            'ipv4_default_prefix_length': self.ipv4_default_prefix_length,
            'ipv6_default_prefix_length': self.ipv6_default_prefix_length
        }

        if self.id is None:
            # New object, create
            data['schema'] = self.schema.id,
            try:
                self.id = self._xmlrpc.connection.add_pool(
                    {
                        'schema': { 'id': self.schema.id },
                        'attr': data,
                        'auth': self._auth_opts.options
                    })
            except xmlrpclib.Fault, f:
                raise _fault_to_exception(f)

        else:
            # Old object, edit
            try:
                self._xmlrpc.connection.edit_pool(
                    {
                        'schema': { 'id': self.schema.id },
                        'pool': { 'id': self.id },
                        'attr': data,
                        'auth': self._auth_opts.options
                    })
            except xmlrpclib.Fault, f:
                raise _fault_to_exception(f)

        _cache['Pool'][self.id] = self



    def remove(self):
        """ Remove pool.
        """

        try:
            self._xmlrpc.connection.remove_pool(
                {
                    'schema': { 'id': self.schema.id },
                    'pool': { 'id': self.id },
                    'auth': self._auth_opts.options
                })
        except xmlrpclib.Fault, f:
            raise _fault_to_exception(f)
        if self.id in _cache['Pool']:
            del(_cache['Pool'][self.id])



    @classmethod
    def get(cls, schema, id):
        """ Get the pool with id 'id'.
        """

        # verify schema
        if not isinstance(schema, Schema):
            raise NipapValueError("missing/invalid schema specified")

        # cached?
        if id in _cache['Pool']:
            log.debug('cache hit for pool %d' % id)
            return _cache['Pool'][id]
        log.debug('cache miss for pool %d' % id)

        try:
            pool = Pool.list(schema, {'id': id})[0]
        except KeyError, e:
            raise NipapNonExistentError('no pool with ID ' + str(id) + ' found')

        _cache['Pool'][id] = pool
        return pool



    @classmethod
    def search(cls, schema, query, search_opts={}):
        """ Search pools.
        """

        # verify schema
        if not isinstance(schema, Schema):
            raise NipapValueError("missing/invalid schema specified")

        xmlrpc = XMLRPCConnection()
        try:
            search_result = xmlrpc.connection.search_pool(
                {
                    'schema': { 'id': schema.id },
                    'query': query,
                    'search_options': search_opts,
                    'auth': AuthOptions().options
                })
        except xmlrpclib.Fault, f:
            raise _fault_to_exception(f)
        result = dict()
        result['result'] = []
        result['search_options'] = search_result['search_options']
        for pool in search_result['result']:
            p = Pool.from_dict(pool)
            result['result'].append(p)

        return result



    @classmethod
    def smart_search(cls, schema, query_string, search_options={}):
        """ Perform a smart pool search.
        """

        # verify schema
        if not isinstance(schema, Schema):
            raise NipapValueError("missing/invalid schema specified")

        xmlrpc = XMLRPCConnection()
        try:
            smart_result = xmlrpc.connection.smart_search_pool(
                {
                    'schema': { 'id': schema.id },
                    'query_string': query_string,
                    'search_options': search_options,
                    'auth': AuthOptions().options
                })
        except xmlrpclib.Fault, f:
            raise _fault_to_exception(f)
        result = dict()
        result['interpretation'] = smart_result['interpretation']
        result['search_options'] = smart_result['search_options']
        result['result'] = list()
        for pool in smart_result['result']:
            p = Pool.from_dict(pool)
            result['result'].append(p)

        return result



    @classmethod
    def from_dict(cls, parm):
        """ Create new Pool-object from dict.

            Suitable for creating objects from XML-RPC data.
            All available keys must exist.
        """

        p = Pool()
        p.id = parm['id']
        p.schema = Schema.get(parm['schema'])
        p.name = parm['name']
        p.description = parm['description']
        p.default_type = parm['default_type']
        p.ipv4_default_prefix_length = parm['ipv4_default_prefix_length']
        p.ipv6_default_prefix_length = parm['ipv6_default_prefix_length']
        return p



    @classmethod
    def list(self, schema, spec = {}):
        """ List pools.
        """

        # verify schema
        if not isinstance(schema, Schema):
            raise NipapValueError("missing/invalid schema specified")

        xmlrpc = XMLRPCConnection()
        pool_list = xmlrpc.connection.list_pool(
            {
                'schema': { 'id': schema.id },
                'pool': spec,
                'auth': AuthOptions().options
            })
        res = list()
        for pool in pool_list:
            p = Pool.from_dict(pool)
            res.append(p)

        return res



class Prefix(Pynipap):
    """ A prefix.
    """

    family = None
    schema = None
    prefix = None
    display_prefix = None
    description = None
    comment = None
    node = None
    pool = None
    type = None
    indent = None
    country = None
    external_key = None
    order_id = None
    vrf = None
    authoritative_source = None
    alarm_priority = None
    monitor = None
    display = True
    match = False
    children = -2


    @classmethod
    def get(cls, schema, id):
        """ Get the prefix with id 'id'.
        """

        # verify schema
        if not isinstance(schema, Schema):
            raise NipapValueError("missing/invalid schema specified")

        # cached?
        if id in _cache['Prefix']:
            log.debug('cache hit for prefix %d' % id)
            return _cache['Prefix'][id]
        log.debug('cache miss for prefix %d' % id)

        try:
            prefix = Prefix.list(schema, {'id': id})[0]
        except KeyError, e:
            raise NipapNonExistentError('no prefix with ID ' + str(id) + ' found')

        _cache['Prefix'][id] = prefix
        return prefix



    @classmethod
    def find_free(cls):
        """ Finds a free prefix.
        """
        pass



    @classmethod
    def search(cls, schema, query, search_opts):
        """ Search for prefixes.
        """

        # verify schema
        if not isinstance(schema, Schema):
            raise NipapValueError("missing/invalid schema specified")

        xmlrpc = XMLRPCConnection()
        try:
            search_result = xmlrpc.connection.search_prefix(
                {
                    'schema': { 'id': schema.id },
                    'query': query,
                    'search_options': search_opts,
                    'auth': AuthOptions().options
                })
        except xmlrpclib.Fault, f:
            raise _fault_to_exception(f)
        result = dict()
        result['result'] = []
        result['search_options'] = search_result['search_options']
        for prefix in search_result['result']:
            p = Prefix.from_dict(prefix)
            result['result'].append(p)

        return result



    @classmethod
    def smart_search(cls, schema, query_string, search_options):
        """ Perform a smart prefix search.
        """

        # verify schema
        if not isinstance(schema, Schema):
            raise NipapValueError("missing/invalid schema specified")

        xmlrpc = XMLRPCConnection()
        try:
            smart_result = xmlrpc.connection.smart_search_prefix(
                {
                    'schema': { 'id': schema.id },
                    'query_string': query_string,
                    'search_options': search_options,
                    'auth': AuthOptions().options
                })
        except xmlrpclib.Fault, f:
            raise _fault_to_exception(f)
        result = dict()
        result['interpretation'] = smart_result['interpretation']
        result['search_options'] = smart_result['search_options']
        result['result'] = list()
        for prefix in smart_result['result']:
            p = Prefix.from_dict(prefix)
            result['result'].append(p)

        return result



    @classmethod
    def list(cls, schema, spec = {}):
        """ List prefixes.
        """

        # verify schema
        if not isinstance(schema, Schema):
            raise NipapValueError("missing/invalid schema specified")

        xmlrpc = XMLRPCConnection()
        try:
            pref_list = xmlrpc.connection.list_prefix(
                {
                    'schema': { 'id': schema.id },
                    'prefix': spec,
                    'auth': AuthOptions().options
                })
        except xmlrpclib.Fault, f:
            raise _fault_to_exception(f)
        res = list()
        for pref in pref_list:
            p = Prefix.from_dict(pref)
            res.append(p)

        return res



    def save(self, args = {}):
        """ Save prefix to PYNIPAP.
        """

        # verify that the schema variable actually contains a schema
        if not isinstance(self.schema, Schema):
            raise NipapValueError("prefix does not have a valid schema set")

        data = {
            'schema': self.schema.id,
            'description': self.description,
            'comment': self.comment,
            'node': self.node,
            'type': self.type,
            'country': self.country,
            'order_id': self.order_id,
            'vrf': self.vrf,
            'external_key': self.external_key,
            'alarm_priority': self.alarm_priority,
            'monitor': self.monitor
        }

        # Prefix can be none if we are creating a new prefix
        # from a pool or other prefix!
        if self.prefix is not None:
            data['prefix'] = self.prefix

        if self.pool is not None:
            data['pool'] = self.pool.id
        else:
            data['pool'] = None

        # New object, create from scratch
        if self.id is None:

            self._logger.error("save: args = %s" % str(args))

            # format args
            x_args = {}
            if 'from-pool' in args:
                x_args['from-pool'] = { 'id': args['from-pool'].id }
                x_args['family'] = args['family']
            if 'from-prefix' in args:
                x_args['from-prefix'] = args['from-prefix']
            if 'prefix_length' in args:
                x_args['prefix_length'] = args['prefix_length']

            try:
                self.id = self._xmlrpc.connection.add_prefix(
                    {
                        'schema': { 'id': self.schema.id },
                        'attr': data,
                        'args': x_args,
                        'auth': self._auth_opts.options
                    })
            except xmlrpclib.Fault, f:
                raise _fault_to_exception(f)

            # fetch data which is set by NIPAP
            try:
                p = self._xmlrpc.connection.list_prefix(
                    {
                        'schema': { 'id': self.schema.id },
                        'prefix': { 'id': self.id },
                        'auth': self._auth_opts.options
                    })[0]
            except xmlrpclib.Fault, f:
                raise _fault_to_exception(f)
            except IndexError:
                raise NipapNonExistantError('Added prefix not found.')
            self.prefix = p['prefix']
            self.indent = p['indent']
            self.family = p['family']
            self.display_prefix = p['display_prefix']
            self.authoritative_source = p['authoritative_source']
            self.alarm_priority = p['alarm_priority']
            self.monitor = p['monitor']

        # Old object, edit
        else:
            # remove keys which we are not allowed to edit
            del(data['schema'])

            try:
                # save
                self._xmlrpc.connection.edit_prefix(
                    {
                        'schema': { 'id': self.schema.id },
                        'prefix': { 'id': self.id },
                        'attr': data,
                        'auth': self._auth_opts.options
                    })

            except xmlrpclib.Fault, f:
                raise _fault_to_exception(f)

        # update cache
        _cache['Prefix'][self.id] = self



    def remove(self):
        """ Remove the prefix.
        """

        try:
            self._xmlrpc.connection.remove_prefix(
                {
                    'schema': { 'id': self.schema.id },
                    'prefix': { 'id': self.id },
                    'auth': self._auth_opts.options
                })
        except xmlrpclib.Fault, f:
            raise _fault_to_exception(f)
        if self.id in _cache['Prefix']:
            del(_cache['Prefix'][self.id])



    @classmethod
    def from_dict(cls, pref):
        """ Create a Prefix object from a dict.

            Suitable for creating Prefix objects from XML-RPC input.
        """

        p = Prefix()
        p.id = pref['id']
        p.family = pref['family']
        p.schema = Schema.get(pref['schema'])
        p.prefix = pref['prefix']
        p.display_prefix = pref['display_prefix']
        p.description = pref['description']
        p.comment = pref['comment']
        p.node = pref['node']
        if pref['pool'] is None: # Pool is not mandatory
            p.pool = None
        else:
            p.pool = Pool.get(p.schema, pref['pool'])
        p.type = pref['type']
        p.indent = pref['indent']
        p.country = pref['country']
        p.order_id = pref['order_id']
        p.vrf = pref['vrf']
        p.external_key = pref['external_key']
        p.authoritative_source = pref['authoritative_source']
        p.alarm_priority = pref['alarm_priority']
        p.monitor = pref['monitor']
        if 'match' in pref:
            p.match = pref['match']
        if 'display' in pref:
            p.display = pref['display']
        if 'children' in pref:
            p.children = pref['children']

        return p



#
# Define exceptions
#

class NipapError(Exception):
    """ A generic NIPAP model exception.

        All errors thrown from the NIPAP model extends this exception.
    """
    pass



class NipapNonExistentError(NipapError):
    """ Thrown when something can not be found.

        For example when a given ID can not be found in the NIPAP database.
    """


class NipapInputError(NipapError):
    """ Something wrong with the input we received

        A general case.
    """
    pass



class NipapMissingInputError(NipapInputError):
    """ Missing input

        Most input is passed in dicts, this could mean a missing key in a dict.
    """
    pass



class NipapExtraneousInputError(NipapInputError):
    """ Extraneous input

        Most input is passed in dicts, this could mean an unknown key in a dict.
    """
    pass



class NipapNoSuchOperatorError(NipapInputError):
    """ A non existent operator was specified.
    """
    pass



class NipapValueError(NipapError):
    """ Something wrong with a value we have

        For example, trying to send an integer when an IP address is expected.
    """
    pass



class NipapDuplicateError(NipapError):
    """ A duplicate entry was encountered
    """
    pass


#
# GLOBAL STUFF
#

# Simple object cache
# TODO: fix some kind of timeout
_cache = {
    'Pool': {},
    'Prefix': {},
    'Schema': {}
}

# Map from XML-RPC Fault codes to Exception classes
_fault_to_exception_map = {
    1000: NipapError,
    1100: NipapInputError,
    1110: NipapMissingInputError,
    1120: NipapExtraneousInputError,
    1200: NipapValueError,
    1300: NipapNonExistentError,
    1400: NipapDuplicateError
}

log = logging.getLogger("Pynipap")



def _fault_to_exception(f):
    """ Converts XML-RPC Fault objects to Pynipap-exceptions.

        TODO: Is this one neccesary? Can be done inline...
    """

    e = _fault_to_exception_map.get(f.faultCode)
    if e is None:
        e = NipapError
    return e(f.faultString)
