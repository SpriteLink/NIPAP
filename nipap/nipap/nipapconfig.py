import ConfigParser


class NipapConfig(ConfigParser.SafeConfigParser):
    """ Makes configuration data available.

        Implemented as a class with a shared state; once an instance has been
        created, new instances with the same state can be obtained by calling
        the custructor again.
    """

    __shared_state = {}
    _config = None
    _cfg_path = None

    def __init__(self, cfg_path=None, default=None):
        """ Takes config file path and command line arguments.
        """

        self.__dict__ = self.__shared_state

        if default is None:
            default = {}

        if len(self.__shared_state) == 0:
            # First time - create new instance!
            self._cfg_path = cfg_path

            ConfigParser.SafeConfigParser.__init__(self, default)

            self.read_file()



    def read_file(self):
        """ Read the configuration file
        """

        # don't try to parse config file if we don't have one set
        if not self._cfg_path:
            return

        try:
            cfg_fp = open(self._cfg_path, 'r')
            self.readfp(cfg_fp)
        except IOError as exc:
            raise NipapConfigError(str(exc))



class NipapConfigError(Exception):
    pass
