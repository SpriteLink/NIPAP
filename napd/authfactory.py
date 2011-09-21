""" An authentication & authorization module factory.
"""

# How do we perform this dymanically, depending on what auth modules are
# configured?
from auth import LocalAuth

class AuthFactory:
    
    @classmethod
    def get_auth(cls, username, password, auth_options):
        """ Returns an authentication object.
    
            Depending on what is placed after @ in the username, returns a subclass
            of the BaseAuth class.
        """
    
        user_authbackend = username.rsplit('@', 1);
    
        # If no auth backend was specified, use default
        if len(user_authbackend) == 1:
            return LocalAuth(user_authbackend[0], password, auth_options)
    
        # static => LocalAuth
        if user_authbackend[1] == 'static':
            return LocalAuth(user_authbackend[0], password, auth_options)
