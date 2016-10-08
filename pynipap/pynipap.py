"""
    pynipap - a Python NIPAP client library
    =======================================

    pynipap is a Python client library for the NIPAP IP address planning
    system. It is structured as a simple ORM.
    To make it easy to maintain it's quite "thin", passing many arguments
    straight through to the backend. Thus, also the pynipap-specific
    documentation is quite thin. For in-depth information please look at the
    main :py:mod:`NIPAP API documentation <nipap.backend>`.

    There are four ORM-classes:

    * :class:`VRF`
    * :class:`Pool`
    * :class:`Prefix`
    * :class:`Tag`

    Each of these maps to the NIPAP objects with the same name. See the main
    :py:mod:`NIPAP API documentation <nipap.backend>` for an overview of the
    different object types and what they are used for.

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
    * :class:`NipapAuthError`
    * :class:`NipapAuthenticationError`
    * :class:`NipapAuthorizationError`

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

        pynipap.xmlrpc_uri = "http://user:pass@127.0.0.1:1337/XMLRPC"

    If you want to access the API externally, from another host, update the
    corresponding lines in the nipap.conf file. Here you can also change the port. ::
        
        listen = 0.0.0.0              ; IP address to listen on.
        port = 1337             ; XML-RPC listen port (change requires restart)

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
        print(vrf.name)

    To list all objects each object has a :func:`list`-function. ::

        # list all pools
        pools = Pool.list()

        # print the name of the pools
        for p in pools:
            print(p.name)

    Each of the list functions can also take a `spec`-dict as a second
    argument. With the spec you can perform a simple search operation by
    specifying object attribute values. ::

        # List pools with a default type of 'assignment'
        pools = Pool.list({ 'default_type': 'assignment' })

    Performing searches
    ^^^^^^^^^^^^^^^^^^^
    Searches are easiest when using the object's :func:`smart_search`-method::

        #Returns a dict which includes search metadata and 
        #a 'result' : [array, of, prefix, objects]
        search_result = Prefix.smart_search('127.0.0.0/8')
        prefix_objects = search_result['result']
        prefix_objects[0].description
        prefix_objects[0].prefix

    You can also send query filters. ::

        #Find the prefix for Vlan 901
        vlan = 901
        vlan_query = { 'val1': 'vlan', 'operator': 'equals', 'val2': vlan }
        vlan_901 = Prefix.smart_search('', { }, vlan_query)['result'][0]
        vlan_901.vlan
    
    The following operators can be used. ::

        * 'and'
        * 'or'
        * 'equals_any'
        * '='
        * 'equals'
        * '<'
        * 'less'
        * '<='
        * 'less_or_equal'
        * '>'
        * 'greater'
        * '>='
        * 'greater_or_equal'
        * 'is'
        * 'is_not'
        * '!='
        * 'not_equals'
        * 'like': '
        * 'regex_match'
        * 'regex_not_match'
        * '>>':
        * 'contains'
        * '>>='
        * 'contains_equals'
        * '<<'
        * 'contained_within'
        * '<<='
        * 'contained_within_equals'

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
import sys
import logging
if sys.version_info[0] < 3:
    import xmlrpclib
    int = long
else:
    import xmlrpc.client as xmlrpclib

__version__		= "0.29.5"
__author__		= "Kristian Larsson, Lukas Garberg"
__author_email__= "kll@tele2.net, lukas@spritelink.net"
__copyright__	= "Copyright 2011, Kristian Larsson, Lukas Garberg"
__license__		= "MIT"
__status__		= "Development"
__url__			= "http://SpriteLink.github.com/NIPAP"


# This variable holds the URI to the nipap XML-RPC service which will be used.
# It must be set before the Pynipap can be used!
xmlrpc_uri = None

# Caching of objects is enabled per default but can be disabled for certain
# scenarios. Since we don't have any cache expiration time it can be useful to
# disable for long running applications.
CACHE = True

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

        # creating new instance
        self.connection = xmlrpclib.ServerProxy(xmlrpc_uri, allow_none=True,
                use_datetime=True)

        self._logger = logging.getLogger(self.__class__.__name__)



class Pynipap:
    """ A base class for the pynipap model classes.

        All Pynipap classes which maps to data in NIPAP (:py:class:`VRF`,
        :py:class:`Pool`, :py:class:`Prefix`) extends this class.
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
            return False

        return self.id == other.id



    def __init__(self, id=None):
        """ Creates logger and XML-RPC-connection.
        """

        self._logger = logging.getLogger(self.__class__.__name__)
        self._auth_opts = AuthOptions()
        self.id = id



class Tag(Pynipap):
    """ A Tag.
    """

    name = None
    """ The Tag name
    """

    @classmethod
    def from_dict(cls, tag=None):
        """ Create new Tag-object from dict.

            Suitable for creating objects from XML-RPC data.
            All available keys must exist.
        """

        if tag is None:
            tag = {}

        l = Tag()
        l.name = tag['name']
        return l



    @classmethod
    def search(cls, query, search_opts=None):
        """ Search tags.

            For more information, see the backend function
            :py:func:`nipap.backend.Nipap.search_tag`.
        """

        if search_opts is None:
            search_opts = {}

        xmlrpc = XMLRPCConnection()
        try:
            search_result = xmlrpc.connection.search_tag(
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
        for xml_tag in search_result['result']:
            result['result'].append(Tag.from_dict(xml_tag))

        return result



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
    num_prefixes_v4 = None
    """ Number of IPv4 prefixes in this VRF
    """
    num_prefixes_v6 = None
    """ Number of IPv6 prefixes in this VRF
    """
    total_addresses_v4 = None
    """ Total number of IPv4 addresses in this VRF
    """
    total_addresses_v6 = None
    """ Total number of IPv6 addresses in this VRF
    """
    used_addresses_v4 = None
    """ Number of used IPv4 addresses in this VRF
    """
    used_addresses_v6 = None
    """ Number of used IPv6 addresses in this VRF
    """
    free_addresses_v4 = None
    """ Number of free IPv4 addresses in this VRF
    """
    free_addresses_v6 = None
    """ Number of free IPv6 addresses in this VRF
    """


    def __init__(self):
        Pynipap.__init__(self)
        self.tags = {}
        self.avps = {}


    @classmethod
    def list(cls, vrf=None):
        """ List VRFs.

            Maps to the function :py:func:`nipap.backend.Nipap.list_vrf` in the
            backend. Please see the documentation for the backend function for
            information regarding input arguments and return values.
        """

        if vrf is None:
            vrf = {}

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
    def from_dict(cls, parm, vrf = None):
        """ Create new VRF-object from dict.

            Suitable for creating objects from XML-RPC data.
            All available keys must exist.
        """

        if vrf is None:
            vrf = VRF()

        vrf.id = parm['id']
        vrf.rt = parm['rt']
        vrf.name = parm['name']
        vrf.description = parm['description']

        vrf.tags = {}
        for tag_name in parm['tags']:
            tag = Tag.from_dict({'name': tag_name })
            vrf.tags[tag_name] = tag
        vrf.avps = parm['avps']

        vrf.num_prefixes_v4 = int(parm['num_prefixes_v4'])
        vrf.num_prefixes_v6 = int(parm['num_prefixes_v6'])
        vrf.total_addresses_v4 = int(parm['total_addresses_v4'])
        vrf.total_addresses_v6 = int(parm['total_addresses_v6'])
        vrf.used_addresses_v4 = int(parm['used_addresses_v4'])
        vrf.used_addresses_v6 = int(parm['used_addresses_v6'])
        vrf.free_addresses_v4 = int(parm['free_addresses_v4'])
        vrf.free_addresses_v6 = int(parm['free_addresses_v6'])

        return vrf



    @classmethod
    def get(cls, id):
        """ Get the VRF with id 'id'.
        """

        # cached?
        if CACHE:
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
    def search(cls, query, search_opts=None):
        """ Search VRFs.

            Maps to the function :py:func:`nipap.backend.Nipap.search_vrf` in
            the backend. Please see the documentation for the backend function
            for information regarding input arguments and return values.
        """

        if search_opts is None:
            search_opts = {}

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
    def smart_search(cls, query_string, search_options=None, extra_query = None):
        """ Perform a smart VRF search.

            Maps to the function
            :py:func:`nipap.backend.Nipap.smart_search_vrf` in the backend.
            Please see the documentation for the backend function for
            information regarding input arguments and return values.
        """

        if search_options is None:
            search_options = {}

        xmlrpc = XMLRPCConnection()
        try:
            smart_result = xmlrpc.connection.smart_search_vrf(
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
        result['error'] = smart_result['error']
        if 'error_message' in smart_result:
            result['error_message'] = smart_result['error_message']
        result['result'] = list()
        for v in smart_result['result']:
            result['result'].append(VRF.from_dict(v))

        return result



    def save(self):
        """ Save changes made to object to NIPAP.

            If the object represents a new VRF unknown to NIPAP (attribute `id`
            is `None`) this function maps to the function
            :py:func:`nipap.backend.Nipap.add_vrf` in the backend, used to
            create a new VRF. Otherwise it maps to the function
            :py:func:`nipap.backend.Nipap.edit_vrf` in the backend, used to
            modify the VRF. Please see the documentation for the backend
            functions for information regarding input arguments and return
            values.
        """

        xmlrpc = XMLRPCConnection()
        data = {
            'rt': self.rt,
            'name': self.name,
            'description': self.description,
            'tags': [],
            'avps': self.avps
        }
        for tag_name in self.tags:
            data['tags'].append(tag_name)

        if self.id is None:
            # New object, create
            try:
                vrf = xmlrpc.connection.add_vrf(
                    {
                        'attr': data,
                        'auth': self._auth_opts.options
                    })
            except xmlrpclib.Fault as xml_fault:
                raise _fault_to_exception(xml_fault)

        else:
            # Old object, edit
            try:
                vrfs = xmlrpc.connection.edit_vrf(
                    {
                        'vrf': { 'id': self.id },
                        'attr': data,
                        'auth': self._auth_opts.options
                    })
            except xmlrpclib.Fault as xml_fault:
                raise _fault_to_exception(xml_fault)

            if len(vrfs) != 1:
                raise NipapError('VRF edit returned %d entries, should be 1.' % len(vrfs))
            vrf = vrfs[0]

        # Refresh object data with attributes from add/edit operation
        VRF.from_dict(vrf, self)

        _cache['VRF'][self.id] = self



    def remove(self):
        """ Remove VRF.

            Maps to the function :py:func:`nipap.backend.Nipap.remove_vrf` in
            the backend. Please see the documentation for the backend function
            for information regarding input arguments and return values.
        """

        xmlrpc = XMLRPCConnection()
        try:
            xmlrpc.connection.remove_vrf(
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
    vrf = None
    member_prefixes_v4 = None
    member_prefixes_v6 = None
    used_prefixes_v4 = None
    used_prefixes_v6 = None
    free_prefixes_v4 = None
    free_prefixes_v6 = None
    total_prefixes_v4 = None
    total_prefixes_v6 = None
    total_addresses_v4 = None
    total_addresses_v6 = None
    used_addresses_v4 = None
    used_addresses_v6 = None
    free_addresses_v4 = None
    free_addresses_v6 = None


    def __init__(self):
        Pynipap.__init__(self)
        self.tags = {}
        self.avps = {}


    def save(self):
        """ Save changes made to pool to NIPAP.

            If the object represents a new pool unknown to NIPAP (attribute
            `id` is `None`) this function maps to the function
            :py:func:`nipap.backend.Nipap.add_pool` in the backend, used to
            create a new pool. Otherwise it maps to the function
            :py:func:`nipap.backend.Nipap.edit_pool` in the backend, used to
            modify the pool. Please see the documentation for the backend
            functions for information regarding input arguments and return
            values.
        """

        xmlrpc = XMLRPCConnection()
        data = {
            'name': self.name,
            'description': self.description,
            'default_type': self.default_type,
            'ipv4_default_prefix_length': self.ipv4_default_prefix_length,
            'ipv6_default_prefix_length': self.ipv6_default_prefix_length,
            'tags': [],
            'avps': self.avps
        }
        for tag_name in self.tags:
            data['tags'].append(tag_name)

        if self.id is None:
            # New object, create
            try:
                pool = xmlrpc.connection.add_pool(
                    {
                        'attr': data,
                        'auth': self._auth_opts.options
                    })
            except xmlrpclib.Fault as xml_fault:
                raise _fault_to_exception(xml_fault)

        else:
            # Old object, edit
            try:
                pools = xmlrpc.connection.edit_pool(
                    {
                        'pool': { 'id': self.id },
                        'attr': data,
                        'auth': self._auth_opts.options
                    })
            except xmlrpclib.Fault as xml_fault:
                raise _fault_to_exception(xml_fault)

            if len(pools) != 1:
                raise NipapError('Pool edit returned %d entries, should be 1.' % len(pools))
            pool = pools[0]

        # Refresh object data with attributes from add/edit operation
        Pool.from_dict(pool, self)

        _cache['Pool'][self.id] = self



    def remove(self):
        """ Remove pool.

            Maps to the function :py:func:`nipap.backend.Nipap.remove_pool` in
            the backend. Please see the documentation for the backend function
            for information regarding input arguments and return values.
        """

        xmlrpc = XMLRPCConnection()
        try:
            xmlrpc.connection.remove_pool(
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
        if CACHE:
            if id in _cache['Pool']:
                log.debug('cache hit for pool %d' % id)
                return _cache['Pool'][id]
            log.debug('cache miss for pool %d' % id)

        try:
            pool = Pool.list({'id': id})[0]
        except (IndexError, KeyError):
            raise NipapNonExistentError('no pool with ID ' + str(id) + ' found')

        _cache['Pool'][id] = pool
        return pool



    @classmethod
    def search(cls, query, search_opts=None):
        """ Search pools.

            Maps to the function :py:func:`nipap.backend.Nipap.search_pool` in
            the backend. Please see the documentation for the backend function
            for information regarding input arguments and return values.
        """

        if search_opts is None:
            search_opts = {}

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
    def smart_search(cls, query_string, search_options=None, extra_query = None):
        """ Perform a smart pool search.

            Maps to the function
            :py:func:`nipap.backend.Nipap.smart_search_pool` in the backend.
            Please see the documentation for the backend function for
            information regarding input arguments and return values.
        """

        if search_options is None:
            search_options = {}

        xmlrpc = XMLRPCConnection()
        try:
            smart_result = xmlrpc.connection.smart_search_pool(
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
        result['error'] = smart_result['error']
        if 'error_message' in smart_result:
            result['error_message'] = smart_result['error_message']
        result['result'] = list()
        for pool in smart_result['result']:
            p = Pool.from_dict(pool)
            result['result'].append(p)

        return result



    @classmethod
    def from_dict(cls, parm, pool = None):
        """ Create new Pool-object from dict.

            Suitable for creating objects from XML-RPC data.
            All available keys must exist.
        """

        if pool is None:
            pool = Pool()

        pool.id = parm['id']
        pool.name = parm['name']
        pool.description = parm['description']
        pool.default_type = parm['default_type']
        pool.ipv4_default_prefix_length = parm['ipv4_default_prefix_length']
        pool.ipv6_default_prefix_length = parm['ipv6_default_prefix_length']
        for val in ('member_prefixes_v4', 'member_prefixes_v6',
                'used_prefixes_v4', 'used_prefixes_v6', 'free_prefixes_v4',
                'free_prefixes_v6', 'total_prefixes_v4', 'total_prefixes_v6',
                'total_addresses_v4', 'total_addresses_v6', 'used_addresses_v4',
                'used_addresses_v6', 'free_addresses_v4', 'free_addresses_v6'):
            if parm[val] is not None:
                setattr(pool, val, int(parm[val]))

        pool.tags = {}
        for tag_name in parm['tags']:
            tag = Tag.from_dict({'name': tag_name })
            pool.tags[tag_name] = tag

        pool.avps = parm['avps']

        # store VRF object in pool.vrf
        if parm['vrf_id'] is not None:
            pool.vrf = VRF.get(parm['vrf_id'])

        return pool



    @classmethod
    def list(self, spec=None):
        """ List pools.

            Maps to the function :py:func:`nipap.backend.Nipap.list_pool` in
            the backend. Please see the documentation for the backend function
            for information regarding input arguments and return values.
        """

        if spec is None:
            spec = {}

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
    customer_id = None
    authoritative_source = None
    alarm_priority = None
    monitor = None
    display = True
    match = False
    children = -2
    vlan = None
    added = None
    last_modified = None
    total_addresses = None
    used_addreses = None
    free_addreses = None
    status = None
    expires = None


    def __init__(self):
        Pynipap.__init__(self)
        self.inherited_tags = {}
        self.tags = {}
        self.avps = {}



    @classmethod
    def get(cls, id):
        """ Get the prefix with id 'id'.
        """

        # cached?
        if CACHE:
            if id in _cache['Prefix']:
                log.debug('cache hit for prefix %d' % id)
                return _cache['Prefix'][id]
            log.debug('cache miss for prefix %d' % id)

        try:
            prefix = Prefix.list({'id': id})[0]
        except IndexError:
            raise NipapNonExistentError('no prefix with ID ' + str(id) + ' found')

        _cache['Prefix'][id] = prefix
        return prefix



    @classmethod
    def find_free(cls, vrf, args):
        """ Finds a free prefix.

            Maps to the function
            :py:func:`nipap.backend.Nipap.find_free_prefix` in the backend.
            Please see the documentation for the backend function for
            information regarding input arguments and return values.
        """

        xmlrpc = XMLRPCConnection()
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
        try:
            find_res = xmlrpc.connection.find_free_prefix(q)
        except xmlrpclib.Fault as xml_fault:
            raise _fault_to_exception(xml_fault)
        pass

        return find_res



    @classmethod
    def search(cls, query, search_opts=None):
        """ Search for prefixes.

            Maps to the function :py:func:`nipap.backend.Nipap.search_prefix`
            in the backend. Please see the documentation for the backend
            function for information regarding input arguments and return
            values.
        """

        if search_opts is None:
            search_opts = {}

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
    def smart_search(cls, query_string, search_options=None, extra_query = None):
        """ Perform a smart prefix search.

            Maps to the function
            :py:func:`nipap.backend.Nipap.smart_search_prefix` in the backend.
            Please see the documentation for the backend function for
            information regarding input arguments and return values.
        """

        if search_options is None:
            search_options = {}

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
        result['error'] = smart_result['error']
        if 'error_message' in smart_result:
            result['error_message'] = smart_result['error_message']
        result['result'] = list()
        for prefix in smart_result['result']:
            p = Prefix.from_dict(prefix)
            result['result'].append(p)

        return result



    @classmethod
    def list(cls, spec=None):
        """ List prefixes.

            Maps to the function :py:func:`nipap.backend.Nipap.list_prefix` in
            the backend. Please see the documentation for the backend function
            for information regarding input arguments and return values.
        """

        if spec is None:
            spec = {}

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



    def save(self, args=None):
        """ Save prefix to NIPAP.

            If the object represents a new prefix unknown to NIPAP (attribute
            `id` is `None`) this function maps to the function
            :py:func:`nipap.backend.Nipap.add_prefix` in the backend, used to
            create a new prefix. Otherwise it maps to the function
            :py:func:`nipap.backend.Nipap.edit_prefix` in the backend, used to
            modify the VRF. Please see the documentation for the backend
            functions for information regarding input arguments and return
            values.
        """

        if args is None:
            args = {}

        xmlrpc = XMLRPCConnection()
        data = {
            'description': self.description,
            'comment': self.comment,
            'tags': [],
            'node': self.node,
            'type': self.type,
            'country': self.country,
            'order_id': self.order_id,
            'customer_id': self.customer_id,
            'external_key': self.external_key,
            'alarm_priority': self.alarm_priority,
            'monitor': self.monitor,
            'vlan': self.vlan,
            'avps': self.avps,
            'expires': self.expires
        }

        if self.status is not None:
            data['status'] = self.status

        for tag_name in self.tags:
            data['tags'].append(tag_name)

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
            if 'family' in args:
                x_args['family'] = args['family']
            if 'from-prefix' in args:
                x_args['from-prefix'] = args['from-prefix']
            if 'prefix_length' in args:
                x_args['prefix_length'] = args['prefix_length']

            try:
                prefix = xmlrpc.connection.add_prefix(
                    {
                        'attr': data,
                        'args': x_args,
                        'auth': self._auth_opts.options
                    })
            except xmlrpclib.Fault as xml_fault:
                raise _fault_to_exception(xml_fault)

        # Old object, edit
        else:

            # Add authoritative source to data
            data['authoritative_source'] = self.authoritative_source

            try:
                # save
                prefixes = xmlrpc.connection.edit_prefix(
                    {
                        'prefix': { 'id': self.id },
                        'attr': data,
                        'auth': self._auth_opts.options
                    })

            except xmlrpclib.Fault as xml_fault:
                raise _fault_to_exception(xml_fault)

            if len(prefixes) != 1:
                raise NipapError('Prefix edit returned %d entries, should be 1.' % len(prefixes))
            prefix = prefixes[0]

        # Refresh object data with attributes from add/edit operation
        Prefix.from_dict(prefix, self)

        # update cache
        _cache['Prefix'][self.id] = self
        if self.pool is not None:
            if self.pool.id in _cache['Pool']:
                del _cache['Pool'][self.pool.id]



    def remove(self, recursive = False):
        """ Remove the prefix.

            Maps to the function :py:func:`nipap.backend.Nipap.remove_prefix`
            in the backend. Please see the documentation for the backend
            function for information regarding input arguments and return
            values.
        """

        xmlrpc = XMLRPCConnection()
        try:
            xmlrpc.connection.remove_prefix(
                {
                    'prefix': { 'id': self.id },
                    'recursive': recursive,
                    'auth': self._auth_opts.options
                })
        except xmlrpclib.Fault as xml_fault:
            raise _fault_to_exception(xml_fault)

        # update cache
        if self.id in _cache['Prefix']:
            del(_cache['Prefix'][self.id])
        if self.pool is not None:
            if self.pool.id in _cache['Pool']:
                del _cache['Pool'][self.pool.id]



    @classmethod
    def from_dict(cls, pref, prefix = None):
        """ Create a Prefix object from a dict.

            Suitable for creating Prefix objects from XML-RPC input.
        """

        if prefix is None:
            prefix = Prefix()

        prefix.id = pref['id']
        if pref['vrf_id'] is not None: # VRF is not mandatory
            prefix.vrf = VRF.get(pref['vrf_id'])
        prefix.family = pref['family']
        prefix.prefix = pref['prefix']
        prefix.display_prefix = pref['display_prefix']
        prefix.description = pref['description']
        prefix.comment = pref['comment']
        prefix.node = pref['node']
        if pref['pool_id'] is not None: # Pool is not mandatory
            prefix.pool = Pool.get(pref['pool_id'])
        prefix.type = pref['type']
        prefix.indent = pref['indent']
        prefix.country = pref['country']
        prefix.order_id = pref['order_id']
        prefix.customer_id = pref['customer_id']
        prefix.external_key = pref['external_key']
        prefix.authoritative_source = pref['authoritative_source']
        prefix.alarm_priority = pref['alarm_priority']
        prefix.monitor = pref['monitor']
        prefix.vlan = pref['vlan']
        prefix.added = pref['added']
        prefix.last_modified = pref['last_modified']
        prefix.total_addresses = int(pref['total_addresses'])
        prefix.used_addresses = int(pref['used_addresses'])
        prefix.free_addresses = int(pref['free_addresses'])
        prefix.status = pref['status']
        prefix.avps = pref['avps']
        prefix.expires = pref['expires']

        prefix.inherited_tags = {}
        for tag_name in pref['inherited_tags']:
            tag = Tag.from_dict({'name': tag_name })
            prefix.inherited_tags[tag_name] = tag

        prefix.tags = {}
        for tag_name in pref['tags']:
            tag = Tag.from_dict({'name': tag_name })
            prefix.tags[tag_name] = tag

        if 'match' in pref:
            prefix.match = pref['match']
        if 'display' in pref:
            prefix.display = pref['display']
        if 'children' in pref:
            prefix.children = pref['children']

        return prefix



def nipapd_version():
    """ Get version of nipapd we're connected to.

        Maps to the function :py:func:`nipap.xmlrpc.NipapXMLRPC.version` in the
        XML-RPC API. Please see the documentation for the XML-RPC function for
        information regarding the return value.
    """

    xmlrpc = XMLRPCConnection()
    try:
        return xmlrpc.connection.version(
            {
                'auth': AuthOptions().options
            })
    except xmlrpclib.Fault as xml_fault:
        raise _fault_to_exception(xml_fault)



def nipap_db_version():
    """ Get schema version of database we're connected to.

        Maps to the function :py:func:`nipap.backend.Nipap._get_db_version` in
        the backend. Please see the documentation for the backend function for
        information regarding the return value.
    """

    xmlrpc = XMLRPCConnection()
    try:
        return xmlrpc.connection.db_version(
            {
                'auth': AuthOptions().options
            })
    except xmlrpclib.Fault as xml_fault:
        raise _fault_to_exception(xml_fault)



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



class NipapAuthError(NipapError):
    """ General NIPAP AAA error
    """
    pass



class NipapAuthenticationError(NipapAuthError):
    """ Authentication failed.
    """
    pass



class NipapAuthorizationError(NipapAuthError):
    """ Authorization failed.
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
    1400: NipapDuplicateError,
    1500: NipapAuthError,
    1510: NipapAuthenticationError,
    1520: NipapAuthorizationError
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
