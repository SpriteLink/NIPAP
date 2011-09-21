""" A base authentication & authorization module.

    Includes the base class BaseAuth.
"""

import logging

class BaseAuth:
    """ A base authentication class.
        
        All authentication modules should extend this class.
    """

    _logger = None

    _username = None
    _password = None
    _auth_options = None


    def __init__(self, username, password, auth_options):
        """ Constructor.
        """
        self.username = username
        self.password = password
        self.auth_options = auth_options
        self._logger = logging.getLogger(self.__class__.__name__)

    def authenticated(self):
        """ Verify authentication.

            Returns True/False dependant on whether the authentication
            succeeded or not.
        """
    
        return False



    def authorized(self):
        """ Verify authorization.

            Check if a user is auhtorized to perform a specific operation.
        """
        return False



class LocalAuth(BaseAuth):
    """ An authentication and authorization class for local auth.
    """

    def authenticated(self):
        """ Verify authentication.
        """
        return self.username == 'a' and self.password == 'ost'



class AuthError(Exception):
    """ General auth exception.
    """
    pass


class AuthenticationFailed(AuthError):
    """ Authentication failed.
    """
    pass


class AuthorizationFailed(AuthError):
    """ Authorization failed.
    """
    pass
