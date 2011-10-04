import ConfigParser

class NipapConfig(ConfigParser.ConfigParser):
    """ Makes configuration data available.

        Implemented as a class with a shared state; once an instance has been
        created, new instances with the same state can be obtained by calling
        the custructor again.
    """

    __shared_state = {}
    _config = None

    def __init__(self, cfg_path=None, default={}):
        """ Takes config file path and command line arguments.
        """

        self.__dict__ = self.__shared_state

        if len(self.__shared_state) == 0:
            # First time - create new instance!
            if cfg_path is None:
                raise NipapConfigError("missing configuration file path")
                
            ConfigParser.ConfigParser.__init__(self, default)

            try:
                cfg_fp = open(cfg_path, 'r')
                self.readfp(cfg_fp)
            except IOError, e:
                raise NipapConfigError(str(e))



class NipapConfigError(Exception):
    pass
