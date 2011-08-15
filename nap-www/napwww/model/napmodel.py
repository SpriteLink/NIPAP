import xmlrpclib
import logging

class XMLRPCConnection:
    """ Handles a shared XML-RPC connection.
    """

    __shared_state = {}

    connection = None
    _logger = None


    def __init__(self, url = "http://127.0.0.1:1337"):
        """ Create XML-RPC connection to url.

            If an earlier created instance exists, url
            does not need to be passed.
        """

        # Currently not used due to threading safety issues
        #self.__dict__ = self.__shared_state

        #if len(self.__shared_state) == 0 and url is None:
        #    raise Exception("Missing URL.")

        #if len(self.__shared_state) == 0:

        # creating new instance
        self.connection = xmlrpclib.ServerProxy(url, allow_none=True)
        self._logger = logging.getLogger(self.__class__.__name__)



class NapModel:
    """ A base class for NAP model.
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
        self.id = id



class Schema(NapModel):
    """ A schema.
    """

    name = None
    description = None



    @classmethod
    def list(cls, spec=None):
        """ List schemas.
        """

        xmlrpc = XMLRPCConnection()
        schema_list = xmlrpc.connection.list_schema(spec)

        res = list()
        for schema in schema_list:
            s = Schema()
            s.id = schema['id']
            s.name = schema['name']
            s.description = schema['description']
            res.append(s)

        return res



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
            raise NapNonExistentError('no schema with ID ' + str(id) + ' found')

        _cache['Schema'][id] = schema
        return schema



    def save(self):
        """ Save changes made to object to Nap.
        """

        data = {
            'name': self.name,
            'description': self.description
        }

        if self.id is None:
            # New object, create
            try:
                self.id = self._xmlrpc.connection.add_schema(data)
            except xmlrpclib.Fault, f:
                raise _fault_to_exception(f)

        else:
            # Old object, edit
            try:
                self._xmlrpc.connection.edit_schema({'id': self.id}, data)
            except xmlrpclib.Fault, f:
                raise _fault_to_exception(f)

        _cache['Schema'][self.id] = self



    def remove(self):
        """ Remove schema.
        """

        try:
            self._xmlrpc.connection.remove_schema({'id': self.id})
        except xmlrpclib.Fault, f:
            raise _fault_to_exception(f)
        if self.id in _cache['Schema']:
            del(_cache['Schema'][self.id])



class Pool(NapModel):
    """ An address pool.
    """

    name = None
    schema = None
    description = None
    default_type = None
    ipv4_default_prefix_length = None
    ipv6_default_prefix_length = None


    def save(self):
        """ Save changes made to pool to Nap.
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
            data['schema'] = self.schema.id,
            try:
                self.id = self._xmlrpc.connection.add_pool({'id': self.schema.id}, data)
            except xmlrpclib.Fault, f:
                raise _fault_to_exception(f)

        else:
            # Old object, edit
            try:
                self._xmlrpc.connection.edit_pool({'id': self.schema.id}, {'id': self.id}, data)
            except xmlrpclib.Fault, f:
                raise _fault_to_exception(f)

        _cache['Pool'][self.id] = self



    def remove(self):
        """ Remove pool.
        """

        try:
            self._xmlrpc.connection.remove_pool({'id': self.schema.id}, {'id': self.id})
        except xmlrpclib.Fault, f:
            raise _fault_to_exception(f)
        if self.id in _cache['Pool']:
            del(_cache['Pool'][self.id])



    @classmethod
    def get(cls, schema, id):
        """ Get the pool with id 'id'.
        """

        # cached?
        if id in _cache['Pool']:
            log.debug('cache hit for pool %d' % id)
            return _cache['Pool'][id]
        log.debug('cache miss for pool %d' % id)

        try:
            pool = Pool.list(schema, {'id': id})[0]
        except KeyError, e:
            raise NapNonExistentError('no pool with ID ' + str(id) + ' found')

        _cache['Pool'][id] = pool
        return pool



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

        xmlrpc = XMLRPCConnection()
        pool_list = xmlrpc.connection.list_pool({ 'id': schema.id }, spec)
        res = list()
        for pool in pool_list:
            p = Pool.from_dict(pool)
            res.append(p)

        return res



class Prefix(NapModel):
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
    span_order = None
    authoritative_source = None
    alarm_priority = None
    display = True
    match = False


    @classmethod
    def get(cls, schema, id):
        """ Get the prefix with id 'id'.
        """

        # cached?
        if id in _cache['Prefix']:
            log.debug('cache hit for prefix %d' % id)
            return _cache['Prefix'][id]
        log.debug('cache miss for prefix %d' % id)

        try:
            prefix = Prefix.list(schema, {'id': id})[0]
        except KeyError, e:
            raise NapNonExistentError('no prefix with ID ' + str(id) + ' found')

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

        xmlrpc = XMLRPCConnection()
        search_result = xmlrpc.connection.search_prefix({'id': schema.id}, query, search_opts)
        result = dict()
        result['result'] = []
        result['search_options'] = search_result['search_options']
        for prefix in result['prefix_list']:
            p = Prefix.from_dict(prefix)
            result['result'].append(p)

        return result



    @classmethod
    def smart_search(cls, schema, query_string, search_options):
        """ Perform a smart prefix search.
        """

        xmlrpc = XMLRPCConnection()
        try:
            smart_result = xmlrpc.connection.smart_search_prefix({ 'id': schema.id },
                query_string, search_options)
        except xmlrpclib.Fault, f:
            raise _fault_to_exception(f)
        result = dict()
        result['interpretation'] = smart_result['interpretation']
        result['search_options'] = smart_result['search_options']
        result['prefix_list'] = list()
        for prefix in smart_result['prefix_list']:
            p = Prefix.from_dict(prefix)
            result['prefix_list'].append(p)

        return result



    @classmethod
    def list(cls, schema, spec):
        """ List prefixes.
        """

        xmlrpc = XMLRPCConnection()
        try:
            pref_list = xmlrpc.connection.list_prefix({ 'id': schema.id }, spec)
        except xmlrpclib.Fault, f:
            raise _fault_to_exception(f)
        res = list()
        for pref in pref_list:
            p = Prefix.from_dict(pref)
            res.append(p)

        return res



    def save(self, args = {}):
        """ Save prefix to Nap.
        """

        data = {
            'schema': self.schema.id,
            'description': self.description,
            'comment': self.comment,
            'node': self.node,
            'type': self.type,
            'country': self.country,
            'span_order': self.span_order,
            'authoritative_source': self.authoritative_source,
            'alarm_priority': self.alarm_priority
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
                self.id = self._xmlrpc.connection.add_prefix({'id': self.schema.id}, data, x_args)
            except xmlrpclib.Fault, f:
                raise _fault_to_exception(f)

            # fetch data which is set by Nap
            try:
                p = self._xmlrpc.connection.list_prefix({'id': self.schema.id}, {'id': self.id})[0]
            except xmlrpclib.Fault, f:
                raise _fault_to_exception(f)
            except IndexError:
                raise NapNonExistantError('Added prefix not found.')
            self.prefix = p['prefix']
            self.indent = p['indent']
            self.family = p['family']
            self.display_prefix = p['display_prefix']

        # Old object, edit
        else:
            # remove keys which we are not allowed to edit
            del(data['schema'])
            del(data['type'])

            try:
                self._xmlrpc.connection.edit_prefix({'id': self.schema.id}, {'id': self.id}, data)
            except xmlrpclib.Fault, f:
                raise _fault_to_exception(f)



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
        p.span_order = pref['span_order']
        p.authoritative_source = pref['authoritative_source']
        p.alarm_priority = pref['alarm_priority']
        if 'match' in pref:
            p.match = pref['match']
        if 'display' in pref:
            p.display = pref['display']

        return p



#
# Define exceptions
#

class NapError(Exception):
    """ A generic NAP model exception.

        All errors thrown from the NAP model extends this exception.
    """
    pass



class NapNonExistentError(NapError):
    """ Thrown when something can not be found.

        For example when a given ID can not be found in the NAP database.
    """


class NapInputError(NapError):
    """ Something wrong with the input we received

        A general case.
    """
    pass



class NapMissingInputError(NapInputError):
    """ Missing input

        Most input is passed in dicts, this could mean a missing key in a dict.
    """
    pass



class NapExtraneousInputError(NapInputError):
    """ Extraneous input

        Most input is passed in dicts, this could mean an unknown key in a dict.
    """
    pass



class NapNoSuchOperatorError(NapInputError):
    """ A non existent operator was specified.
    """
    pass



class NapValueError(NapError):
    """ Something wrong with a value we have

        For example, trying to send an integer when an IP address is expected.
    """
    pass



class NapDuplicateError(NapError):
    """ A duplicate entry was encountered
    """
    pass


#
# GLOBAL STUFF
#

# Simple object cache
# TODO: fix somekind of timeout
_cache = {
    'Pool': {},
    'Prefix': {},
    'Schema': {}
}

# Map from XML-RPC Fault codes to Exception classes
_fault_to_exception_map = {
    1000: NapError,
    1100: NapInputError,
    1110: NapMissingInputError,
    1120: NapExtraneousInputError,
    1200: NapValueError,
    1300: NapNonExistentError,
    1400: NapDuplicateError
}

# Create global XML-RPC connection and logger for static methods...
xmlrpc = XMLRPCConnection()
log = logging.getLogger("NapModel")



def _fault_to_exception(f):
    """ Converts XML-RPC Fault objects to NapModel-exceptions.

        TODO: Is this one neccesary? Can be done inline...
    """

    e = _fault_to_exception_map.get(f.faultCode)
    if e is None:
        e = NapError
    return e(f.faultString)
