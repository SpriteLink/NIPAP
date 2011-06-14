import xmlrpclib
import logging

_cache = {
    'Pool': {},
    'Prefix': {},
    'Schema': {}
}

class XMLRPCConnection:
    """ Handles a shared XML-RPC connection. 
    """

    __shared_state = {}

    connection = None
    _logger = None


    def __init__(self, url=None):
        """ Create XML-RPC connection to url. 

            If an earlier created instance exists, url
            does not need to be passed. 
        """

        self.__dict__ = self.__shared_state

        if len(self.__shared_state) == 0 and url is None:
            raise Exception("Missing URL.")

        if len(self.__shared_state) == 0:

            # creating new instance
            self.connection = xmlrpclib.ServerProxy(url, allow_none=True)
            self._logger = logging.getLogger(self.__class__.__name__)



class NapModel:
    """ A base class for NAP model.
    """

    _xmlrpc = None
    _logger = None
    id = None

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
            self.id = self._xmlrpc.connection.add_schema(data)

        else:
            # Old object, edit
            self._xmlrpc.connection.edit_schema({'id': self.id}, data)



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
            'schema': self.schema.id,
            'description': self.description,
            'default_type': self.default_type,
            'ipv4_default_prefix_length': self.ipv4_default_prefix_length,
            'ipv6_default_prefix_length': self.ipv6_default_prefix_length
        }

        if self.id is None:
            # New object, create
            self.id = self._xmlrpc.connection.add_pool(data)

        else:
            # Old object, edit
            self._xmlrpc.connection.edit_pool({'id': self.id}, data)



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
        p['id'] = parm['id']
        p['schema'] = Schema.get(parm['schema'])
        p['name'] = parm['name']
        p['description'] = parm['description']
        p['default_type'] = parm['default_type']
        p['ipv4_default_prefix_length'] = parm['ipv4_default_prefix_length']
        p['ipv6_default_prefix_length'] = parm['ipv6_default_prefix_length']
        return p



    @classmethod
    def list(self, schema, spec):
        """ List pools.
        """

        pool_list = xmlrpc.connection.list_pool({ 'id': schema.id }, spec)
        res = list()
        for pref in pref_list:
            p = Pool.from_dict(pref)
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
    

    @classmethod
    def find_free(cls):
        """ Finds a free prefix.
        """
        pass



    @classmethod
    def search(cls, schema, query):
        """ Search for prefixes.
        """

        pref_list = xmlrpc.connection.search_prefix(query_string)
        res = list()
        for pref in pref_list:
            p = Prefix.from_dict(pref)
            res.append(p)

        return res



    @classmethod
    def smart_search(cls, schema, query_string, search_opt_parent, search_opt_child):
        """ Perform a smart prefix search.
        """

        pref_list = xmlrpc.connection.smart_search_prefix({ 'id': schema.id }, query_string)
        res = dict()
        res['interpretation'] = pref_list['interpretation']
        res['result'] = list()
        for pref in pref_list['result']:
            p = Prefix.from_dict(pref)
            res['result'].append(p)

        return res



    @classmethod
    def list(cls, schema, spec):
        """ List prefixes.
        """

        pref_list = xmlrpc.connection.list_prefix({ 'id': schema.id }, spec)
        res = list()
        for pref in pref_list:
            p = Prefix.from_dict(pref)
            res.append(p)

        return res



    def save(self):
        """ Save prefix to Nap.
        """

        data = {
            'family': self.family,
            'schema': self.schema.id,
            'prefix': self.prefix,
            'description': self.description,
            'comment': self.comment,
            'node': self.node,
            'pool': self.pool.id,
            'type': self.type,
            'indent': self.indent,
            'country': self.country,
            'span_order': self.span_order,
            'authoritative_source': self.authoritative_source,
            'alarm_priority': self.alarm_priority
        }

        if self.id is None:
            # New object, create
            self.id = self._xmlrpc.connection.add_prefix({'id': self.schema.id}, data)

        else:
            # Old object, edit
            self._xmlrpc.connection.edit_prefix({'id': self.schema.id}, {'id': self.id}, data)



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

        return p



# Create global XML-RPC connection for static methods...
xmlrpc = XMLRPCConnection("http://127.0.0.1:1337")
log = logging.getLogger("NapModel")

#
# Define exceptions
#

class NapModelError(Exception):
    """ A generic NAP model exception.

        All errors thrown from the NAP model extends this exception.
    """
    pass



class NapNonExistentError(NapModelError):
    """ Thrown when something can not be found.

        For example when a given ID can not be found in the NAP database.
    """
