import xmlrpclib
import logging

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
    def search(cls, query):
        """ Search for prefixes.
        """

        pref_list = xmlrpc.connection.search_prefix(query_string)
        res = list()
        for pref in pref_list:
            p = Prefix.from_dict(pref)
            res.append(p)

        return res


    @classmethod
    def smart_search(cls, query_string, schema_spec):
        """ Perform a smart prefix search.
        """

        pref_list = xmlrpc.connection.smart_search_prefix(query_string, schema_spec)
        res = dict()
        res['interpretation'] = pref_list['interpretation']
        res['result'] = list()
        for pref in pref_list['result']:
            p = Prefix.from_dict(pref)
            res['result'].append(p)

        return res



    @classmethod
    def list(cls, spec):
        """ List prefixes.
        """

        pref_list = xmlrpc.connection.list_prefix(spec)
        res = list()
        for pref in pref_list:
            p = Prefix.from_dict(pref)
            res.append(p)

        return res



    def _fetch(self):
        """ Fetch info from database.
        """
        pass



    def save(self):
        """ Save prefix to Nap.
        """
        pass



    @classmethod
    def from_dict(cls, pref):
        """ Create a Prefix object from a dict.
           
            Suitable for creating Prefix objects from XML-RPC input.
        """

        p = Prefix()
        p.id = pref['id']
        p.family = pref['family']
        p.schema = Schema() # TODO: get right object
        p.prefix = pref['prefix']
        p.display_prefix = pref['display_prefix']
        p.description = pref['description']
        p.comment = pref['comment']
        p.node = pref['node'] # TODO: Nils-object? :)
        p.pool = Pool() # TODO: get right object
        p.type = pref['type']
        p.indent = pref['indent']
        p.country = pref['country']
        p.span_order = pref['span_order']
        p.authoritative_source = pref['authoritative_source']
        p.alarm_priority = pref['alarm_priority']

        return p



# Create global XML-RPC connection for static methods...
xmlrpc = XMLRPCConnection("http://127.0.0.1:1337")
