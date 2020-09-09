import configparser


class NipapConfig(configparser.ConfigParser):
    """ Makes configuration data available.

        Implemented as a class with a shared state; once an instance has been
        created, new instances with the same state can be obtained by calling
        the constructor again.
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

            configparser.ConfigParser.__init__(self, default, inline_comment_prefixes=";#")

            self.read_file()

    def read_file(self):
        """ Read the configuration file
        """

        # don't try to parse config file if we don't have one set
        if not self._cfg_path:
            return

        try:
            self.read([self._cfg_path])
        except IOError as exc:
            raise NipapConfigError(str(exc))


class NipapConfigError(Exception):
    pass
