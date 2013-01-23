"""
    pynipap - a Python NIPAP client library
    =======================================

    pynipap is a Python client library for the NIPAP IP address planning
    system. It is structured as a simple ORM.

    There are three ORM-classes:

    * :class:`VRF`
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
    pynipap has been designed to be simple to use.

    Preparations
    ^^^^^^^^^^^^
    Make sure that pynipap is accessible in your `sys.path`, you can test it by
    starting a python shell and running::

        import pynipap

    If that works, you are good to go!

    To simplify your code slightly, you can import the individual classes into
    your main namespace::

        import pynipap
        from pynipap import VRF, Pool, Prefix

    Before you can access NIPAP you need to specify the URL to the NIPAP
    XML-RPC service and the authentication options to use for your connection.
    NIPAP has a authentication system which is somewhat involved, see the main
    NIPAP documentation.

    The URL, including the user credentials, is set in the pynipap module
    variable `xmlrpc_uri` as so::

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
    (:py:class:`VRF`, :class:`Pool`, :class:`Prefix`) or a list of
    instances. The :func:`search` and :func:`smart_search` functions also
    embeds the lists in dicts which contain search meta data.

    The easiest way to get data out of NIPAP is to use the :func:`get`-method,
    given that you know the ID of the object you want to fetch::

        # Fetch VRF with ID 1 and print its name
        vrf = VRF.get(1)
        print vrf.name

    To list all objects each object has a :func:`list`-function. ::

        # list all pools
        pools = Pool.list()

        # print the name of the pools
        for p in pools:
            print p.name

    Each of the list functions can also take a `spec`-dict as a second
    argument. With the spec you can perform a simple search operation by
    specifying object attribute values. ::

        # List pools with a default type of 'assignment'
        pools = Pool.list({ 'default_type': 'assignment' })

    Performing searches
    ^^^^^^^^^^^^^^^^^^^
    Commin' up, commin' up.

    Saving changes
    ^^^^^^^^^^^^^^

    Changes made to objects are not automatically saved. To save the changes,
    simply run the object's :func:`save`-method::

        vrf.name = "Spam spam spam"
        vrf.save()

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

__version__		= "0.14.0"
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

            The argument 'options' must be a dict containing authentication
            options.
        """

        self.__dict__ = self.__shared_state

        if len(self.__shared_state) == 0 and options is None:
            raise NipapMissingInputError("authentication options not set")

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

        All Pynipap classes which maps to data in NIPAP (:py:class:VRF,
        :py:class:Pool, :py:class:Prefix) extends this class.
    """

    _xmlrpc = None
    """ XML-RPC connection.
    """
    _logger = None
    """ Logging instance for this object.
    """

    id = None
    """ Internal database ID of object.
    """

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



class VRF(Pynipap):
    """ A VRF.
    """

    rt = None
    """ The VRF RT, as a string (x:y or x.x.x.x:y).
    """
    name = None
    """ The name of the VRF, as a string.
    """
    description = None
    """ VRF description, as a string.
    """


    @classmethod
    def list(cls, vrf = {}):
        """ List VRFs.
        """

        xmlrpc = XMLRPCConnection()
        try:
            vrf_list = xmlrpc.connection.list_vrf(
                {
                    'vrf': vrf,
                    'auth': AuthOptions().options
                })
        except xmlrpclib.Fault as xml_fault:
            raise _fault_to_exception(xml_fault)

        res = list()
        for v in vrf_list:
            res.append(VRF.from_dict(v))

        return res


    @classmethod
    def from_dict(cls, parm):
        """ Create new VRF-object from dict.

            Suitable for creating objects from XML-RPC data.
            All available keys must exist.
        """

        v = VRF()
        v.id = parm['id']
        v.rt = parm['rt']
        v.name = parm['name']
        v.description = parm['description']
        return v



    @classmethod
    def get(cls, id):
        """ Get the VRF with id 'id'.
        """

        # cached?
        if id in _cache['VRF']:
            log.debug('cache hit for VRF %d' % id)
            return _cache['VRF'][id]
        log.debug('cache miss for VRF %d' % id)

        try:
            vrf = VRF.list({ 'id': id })[0]
        except IndexError:
            raise NipapNonExistentError('no VRF with ID ' + str(id) + ' found')

        _cache['VRF'][id] = vrf
        return vrf



    @classmethod
    def search(cls, query, search_opts={}):
        """ Search VRFs.
        """

        xmlrpc = XMLRPCConnection()
        try:
            search_result = xmlrpc.connection.search_vrf(
                {
                    'query': query,
                    'search_options': search_opts,
                    'auth': AuthOptions().options
                })
        except xmlrpclib.Fault as xml_fault:
            raise _fault_to_exception(xml_fault)
        result = dict()
        result['result'] = []
        result['search_options'] = search_result['search_options']
        for v in search_result['result']:
            result['result'].append(VRF.from_dict(v))

        return result



    @classmethod
    def smart_search(cls, query_string, search_options={}):
        """ Perform a smart VRF search.
        """

        xmlrpc = XMLRPCConnection()
        try:
            smart_result = xmlrpc.connection.smart_search_vrf(
                {
                    'query_string': query_string,
                    'search_options': search_options,
                    'auth': AuthOptions().options
                })
        except xmlrpclib.Fault as xml_fault:
            raise _fault_to_exception(xml_fault)
        result = dict()
        result['interpretation'] = smart_result['interpretation']
        result['search_options'] = smart_result['search_options']
        result['result'] = list()
        for v in smart_result['result']:
            result['result'].append(VRF.from_dict(v))

        return result



    def save(self):
        """ Save changes made to object to NIPAP.
        """

        data = {
            'rt': self.rt,
            'name': self.name,
            'description': self.description
        }

        if self.id is None:
            # New object, create
            try:
                self.id = self._xmlrpc.connection.add_vrf(
                    {
                        'attr': data,
                        'auth': self._auth_opts.options
                    })
            except xmlrpclib.Fault as xml_fault:
                raise _fault_to_exception(xml_fault)

        else:
            # Old object, edit
            try:
                self._xmlrpc.connection.edit_vrf(
                    {
                        'vrf': { 'id': self.id },
                        'attr': data,
                        'auth': self._auth_opts.options
                    })
            except xmlrpclib.Fault as xml_fault:
                raise _fault_to_exception(xml_fault)

        _cache['VRF'][self.id] = self



    def remove(self):
        """ Remove VRF.
        """

        try:
            self._xmlrpc.connection.remove_vrf(
                {
                    'vrf': { 'id': self.id },
                    'auth': self._auth_opts.options
                })
        except xmlrpclib.Fault as xml_fault:
            raise _fault_to_exception(xml_fault)
        if self.id in _cache['VRF']:
            del(_cache['VRF'][self.id])



class Pool(Pynipap):
    """ An address pool.
    """

    name = None
    description = None
    default_type = None
    ipv4_default_prefix_length = None
    ipv6_default_prefix_length = None


    def save(self):
        """ Save changes made to pool to NIPAP.
        """

        data = {
            'name': self.name,
            'description': self.description,
            'default_type': self.default_type,
            'ipv4_default_prefix_length': self.ipv4_default_prefix_length,
            'ipv6_default_prefix_length': self.ipv6_default_prefix_length
        }

        if self.id is None:
            # New object, create
            try:
                self.id = self._xmlrpc.connection.add_pool(
                    {
                        'attr': data,
                        'auth': self._auth_opts.options
                    })
            except xmlrpclib.Fault as xml_fault:
                raise _fault_to_exception(xml_fault)

        else:
            # Old object, edit
            try:
                self._xmlrpc.connection.edit_pool(
                    {
                        'pool': { 'id': self.id },
                        'attr': data,
                        'auth': self._auth_opts.options
                    })
            except xmlrpclib.Fault as xml_fault:
                raise _fault_to_exception(xml_fault)

        _cache['Pool'][self.id] = self



    def remove(self):
        """ Remove pool.
        """

        try:
            self._xmlrpc.connection.remove_pool(
                {
                    'pool': { 'id': self.id },
                    'auth': self._auth_opts.options
                })
        except xmlrpclib.Fault as xml_fault:
            raise _fault_to_exception(xml_fault)
        if self.id in _cache['Pool']:
            del(_cache['Pool'][self.id])



    @classmethod
    def get(cls, id):
        """ Get the pool with id 'id'.
        """

        # cached?
        if id in _cache['Pool']:
            log.debug('cache hit for pool %d' % id)
            return _cache['Pool'][id]
        log.debug('cache miss for pool %d' % id)

        try:
            pool = Pool.list({'id': id})[0]
        except KeyError:
            raise NipapNonExistentError('no pool with ID ' + str(id) + ' found')

        _cache['Pool'][id] = pool
        return pool



    @classmethod
    def search(cls, query, search_opts={}):
        """ Search pools.
        """

        xmlrpc = XMLRPCConnection()
        try:
            search_result = xmlrpc.connection.search_pool(
                {
                    'query': query,
                    'search_options': search_opts,
                    'auth': AuthOptions().options
                })
        except xmlrpclib.Fault as xml_fault:
            raise _fault_to_exception(xml_fault)
        result = dict()
        result['result'] = []
        result['search_options'] = search_result['search_options']
        for pool in search_result['result']:
            p = Pool.from_dict(pool)
            result['result'].append(p)

        return result



    @classmethod
    def smart_search(cls, query_string, search_options={}):
        """ Perform a smart pool search.
        """

        xmlrpc = XMLRPCConnection()
        try:
            smart_result = xmlrpc.connection.smart_search_pool(
                {
                    'query_string': query_string,
                    'search_options': search_options,
                    'auth': AuthOptions().options
                })
        except xmlrpclib.Fault as xml_fault:
            raise _fault_to_exception(xml_fault)
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
        p.name = parm['name']
        p.description = parm['description']
        p.default_type = parm['default_type']
        p.ipv4_default_prefix_length = parm['ipv4_default_prefix_length']
        p.ipv6_default_prefix_length = parm['ipv6_default_prefix_length']
        return p



    @classmethod
    def list(self, spec = {}):
        """ List pools.
        """

        xmlrpc = XMLRPCConnection()
        try:
            pool_list = xmlrpc.connection.list_pool(
                {
                    'pool': spec,
                    'auth': AuthOptions().options
                })
        except xmlrpclib.Fault as xml_fault:
            raise _fault_to_exception(xml_fault)
        res = list()
        for pool in pool_list:
            p = Pool.from_dict(pool)
            res.append(p)

        return res



class Prefix(Pynipap):
    """ A prefix.
    """

    family = None
    vrf = None
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
    authoritative_source = None
    alarm_priority = None
    monitor = None
    display = True
    match = False
    children = -2


    @classmethod
    def get(cls, id):
        """ Get the prefix with id 'id'.
        """

        # cached?
        if id in _cache['Prefix']:
            log.debug('cache hit for prefix %d' % id)
            return _cache['Prefix'][id]
        log.debug('cache miss for prefix %d' % id)

        try:
            prefix = Prefix.list({'id': id})[0]
        except KeyError:
            raise NipapNonExistentError('no prefix with ID ' + str(id) + ' found')

        _cache['Prefix'][id] = prefix
        return prefix



    @classmethod
    def find_free(cls, vrf, args):
        """ Finds a free prefix.
        """

        q = {
            'args': args,
            'auth': AuthOptions().options
        }

        # sanity checks
        if isinstance(vrf, VRF):
            q['vrf'] = { 'id': vrf.id }
        elif vrf is None:
            q['vrf'] = None
        else:
            raise NipapValueError('vrf parameter must be instance of VRF class')

        # run XML-RPC query
        xmlrpc = XMLRPCConnection()
        try:
            find_res = xmlrpc.connection.find_free_prefix(q)
        except xmlrpclib.Fault as xml_fault:
            raise _fault_to_exception(xml_fault)
        pass

        return find_res



    @classmethod
    def search(cls, query, search_opts):
        """ Search for prefixes.
        """

        xmlrpc = XMLRPCConnection()
        try:
            search_result = xmlrpc.connection.search_prefix(
                {
                    'query': query,
                    'search_options': search_opts,
                    'auth': AuthOptions().options
                })
        except xmlrpclib.Fault as xml_fault:
            raise _fault_to_exception(xml_fault)
        result = dict()
        result['result'] = []
        result['search_options'] = search_result['search_options']
        for prefix in search_result['result']:
            p = Prefix.from_dict(prefix)
            result['result'].append(p)

        return result



    @classmethod
    def smart_search(cls, query_string, search_options, extra_query = None):
        """ Perform a smart prefix search.
        """

        xmlrpc = XMLRPCConnection()
        try:
            smart_result = xmlrpc.connection.smart_search_prefix(
                {
                    'query_string': query_string,
                    'search_options': search_options,
                    'auth': AuthOptions().options,
                    'extra_query': extra_query
                })
        except xmlrpclib.Fault as xml_fault:
            raise _fault_to_exception(xml_fault)
        result = dict()
        result['interpretation'] = smart_result['interpretation']
        result['search_options'] = smart_result['search_options']
        result['result'] = list()
        for prefix in smart_result['result']:
            p = Prefix.from_dict(prefix)
            result['result'].append(p)

        return result



    @classmethod
    def list(cls, spec = {}):
        """ List prefixes.
        """

        xmlrpc = XMLRPCConnection()
        try:
            pref_list = xmlrpc.connection.list_prefix(
                {
                    'prefix': spec,
                    'auth': AuthOptions().options
                })
        except xmlrpclib.Fault as xml_fault:
            raise _fault_to_exception(xml_fault)
        res = list()
        for pref in pref_list:
            p = Prefix.from_dict(pref)
            res.append(p)

        return res



    def save(self, args = {}):
        """ Save prefix to NIPAP.
        """

        data = {
            'description': self.description,
            'comment': self.comment,
            'node': self.node,
            'type': self.type,
            'country': self.country,
            'order_id': self.order_id,
            'external_key': self.external_key,
            'alarm_priority': self.alarm_priority,
            'monitor': self.monitor
        }

        if self.vrf is not None:
            if not isinstance(self.vrf, VRF):
                raise NipapValueError("'vrf' attribute not instance of VRF class.")
            data['vrf_id'] = self.vrf.id

        # Prefix can be none if we are creating a new prefix
        # from a pool or other prefix!
        if self.prefix is not None:
            data['prefix'] = self.prefix

        if self.pool is None:
            data['pool_id'] = None

        else:
            if not isinstance(self.pool, Pool):
                raise NipapValueError("'pool' attribute not instance of Pool class.")
            data['pool_id'] = self.pool.id

        # New object, create from scratch
        if self.id is None:

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
                        'attr': data,
                        'args': x_args,
                        'auth': self._auth_opts.options
                    })
            except xmlrpclib.Fault as xml_fault:
                raise _fault_to_exception(xml_fault)

            # fetch data which is set by NIPAP
            try:
                p = self._xmlrpc.connection.list_prefix(
                    {
                        'prefix': { 'id': self.id },
                        'auth': self._auth_opts.options
                    })[0]
            except xmlrpclib.Fault as xml_fault:
                raise _fault_to_exception(xml_fault)
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

            # Add authoritative source to data
            data['authoritative_source'] = self.authoritative_source

            try:
                # save
                self._xmlrpc.connection.edit_prefix(
                    {
                        'prefix': { 'id': self.id },
                        'attr': data,
                        'auth': self._auth_opts.options
                    })

            except xmlrpclib.Fault as xml_fault:
                raise _fault_to_exception(xml_fault)

        # update cache
        _cache['Prefix'][self.id] = self



    def remove(self, recursive = False):
        """ Remove the prefix.
        """

        try:
            self._xmlrpc.connection.remove_prefix(
                {
                    'prefix': { 'id': self.id },
                    'recursive': recursive,
                    'auth': self._auth_opts.options
                })
        except xmlrpclib.Fault as xml_fault:
            raise _fault_to_exception(xml_fault)
        if self.id in _cache['Prefix']:
            del(_cache['Prefix'][self.id])



    @classmethod
    def from_dict(cls, pref):
        """ Create a Prefix object from a dict.

            Suitable for creating Prefix objects from XML-RPC input.
        """

        p = Prefix()
        p.id = pref['id']
        if pref['vrf_id'] is not None: # VRF is not mandatory
            p.vrf = VRF.get(pref['vrf_id'])
        p.family = pref['family']
        p.prefix = pref['prefix']
        p.display_prefix = pref['display_prefix']
        p.description = pref['description']
        p.comment = pref['comment']
        p.node = pref['node']
        if pref['pool_id'] is not None: # Pool is not mandatory
            p.pool = Pool.get(pref['pool_id'])
        p.type = pref['type']
        p.indent = pref['indent']
        p.country = pref['country']
        p.order_id = pref['order_id']
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
    'VRF': {}
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
