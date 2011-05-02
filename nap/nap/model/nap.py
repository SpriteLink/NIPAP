import xmlrpclib

class XMLRPCConnection:
    """ Handles a shared XML-RPC connection. 
    """

    __shared_state = {}

    connection = None
    _logger = None
    cache = dict()
    cache_time = time.time()

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
            if url == 'default':
                url = 'http://tone.tele2.net:1338'
            self.connection = xmlrpclib.ServerProxy(url, allow_none=True)
            self._logger = logging.getLogger(self.__class__.__name__)
