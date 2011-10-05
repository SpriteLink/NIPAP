import xmlrpclib
import logging
import sys
import os

from nipapconfig import NipapConfig

__version__		= "0.5.0"
__author__		= "Kristian Larsson, Lukas Garberg"
__copyright__	= "Copyright 2011, Kristian Larsson, Lukas Garberg"
__license__		= "MIT"
__status__		= "Development"
__url__			= "http://github.com/plajjan/NIPAP"

class AuthOptions:
    """ A global-ish authentication option container.

        WHAT ARE THE IMPLICATIONS OF THIS CLASS?! IS ISOLATION GUARANTEED?!
        NO.

        VERY SEVERE ISSUE.
        TODO: fix.
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


    def __init__(self, url = None):
        """ Create XML-RPC connection to url.

            If an earlier created instance exists, url
            does not need to be passed.
        """

        if url is None:
            cfg = NipapConfig()
            url = cfg.get('www', 'xmlrpc_uri')


        # Currently not used due to threading safety issues
        # after the introduction of the config object above, the code below
        # does not work at all anymore ;)
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
        self._auth_opts = AuthOptions()
        self.id = id



class Schema(NapModel):
    """ A schema.
    """

    name = None
    description = None
    vrf = None


    @classmethod
    def list(cls, spec=None):
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
            raise NapNonExistentError('no schema with ID ' + str(id) + ' found')

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
        """ Save changes made to object to Nap.
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
    def search(cls, schema, query, search_opts={}):
        """ Search pools.
        """

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
            p = Pool.from_dict(schema)
            result['result'].append(p)

        return result



    @classmethod
    def smart_search(cls, schema, query_string, search_options={}):
        """ Perform a smart pool search.
        """

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
    order_id = None
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
    def list(cls, schema, spec):
        """ List prefixes.
        """

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
        """ Save prefix to Nap.
        """

        data = {
            'schema': self.schema.id,
            'description': self.description,
            'comment': self.comment,
            'node': self.node,
            'type': self.type,
            'country': self.country,
            'order_id': self.order_id,
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

            # fetch data which is set by Nap
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
                self._xmlrpc.connection.edit_prefix(
                    {
                        'schema': { 'id': self.schema.id },
                        'prefix': { 'id': self.id },
                        'attr': data,
                        'auth': self._auth_opts.options
                    })
            except xmlrpclib.Fault, f:
                raise _fault_to_exception(f)



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

log = logging.getLogger("NapModel")



def _fault_to_exception(f):
    """ Converts XML-RPC Fault objects to NapModel-exceptions.

        TODO: Is this one neccesary? Can be done inline...
    """

    e = _fault_to_exception_map.get(f.faultCode)
    if e is None:
        e = NapError
    return e(f.faultString)
