import configparser

DEFAULT = {
    'syslog': 'false',
    'debug': 'false',
    'foreground': 'false',
    'forks': 0,
    'pid_file': '',
    'listen': '127.0.0.1',
    'port': '1337',
    'ssl_port': '',
    'ssl_cert_file': '',
    'ssl_key_file': '',
    'db_host': 'localhost',
    'db_name': 'nipap',
    'db_port': '',
    'db_user': 'nipap',
    'db_pass': 'papin',
    'db_sslmode': 'require',
    'auth_cache_timeout': '3600',
    'user': '',
    'group': ''
}



class NipapConfig(configparser.ConfigParser):
    """ Makes configuration data available.

        Implemented as a class with a shared state; once an instance has been
        created, new instances with the same state can be obtained by calling
        the constructor again.
    """

    __shared_state = {}
    _config = None
    _cfg_path = None

    def __init__(self, cfg_path=None):
        """ Takes config file path and command line arguments.
        """

        self.__dict__ = self.__shared_state

        if len(self.__shared_state) == 0:
            # First time - create new instance!
            self._cfg_path = cfg_path

            configparser.ConfigParser.__init__(self, DEFAULT, inline_comment_prefixes=";#")

            self.read_config_file()

    def read_config_file(self):
        """ Read the configuration file
        """

        # don't try to parse config file if we don't have one set
        if not self._cfg_path:
            return

        try:
            cfg_fp = open(self._cfg_path, 'r')
            self.read_file(cfg_fp)
        except IOError as exc:
            raise NipapConfigError(str(exc))


class NipapConfigError(Exception):
    pass
