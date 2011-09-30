""" A base authentication & authorization module.

    Includes the base class BaseAuth.
"""

import logging

# Used by SqliteAuth
import sqlite3
import ldap
import string
import hashlib
import random



class AuthFactory:
    """ An factory for authentication backends.
    """
    
    @classmethod
    def get_auth(cls, username, password, authoritative_source, auth_options={}):
        """ Returns an authentication object.
    
            Examines the auth backend given after the '@' in the username and
            returns a suitable instance of a subclass of the BaseAuth class.
        """
    
        user_authbackend = username.rsplit('@', 1);
    
        # TODO: make default backend and mapping of suffix to backend configurable
        # If no auth backend was specified, use default
        if len(user_authbackend) == 1:
            return LdapAuth(user_authbackend[0], password, authoritative_source, auth_options)
    
        # local => SqliteAuth
        if user_authbackend[1] == 'local':
            return SqliteAuth(user_authbackend[0], password, authoritative_source, auth_options)
        else:
            raise AuthError('Invalid auth backend %s specified' %
                str(user_authbackend[1]))



class BaseAuth:
    """ A base authentication class.
        
        All authentication modules should extend this class.
    """

    username = None
    password = None
    authenticated_as = None
    full_name = None
    authoritative_source = None
    auth_backend = None
    trusted = None

    _logger = None
    _auth_options = None


    def __init__(self, username, password, authoritative_source, auth_backend, auth_options={}):
        """ Constructor.
        """

        self.username = username
        self.password = password
        self.auth_backend = auth_backend
        self.authoritative_source = authoritative_source

        self._auth_options = auth_options
        self._logger = logging.getLogger(self.__class__.__name__)



    def authenticate(self):
        """ Verify authentication.

            Returns True/False dependant on whether the authentication
            succeeded or not.
        """
    
        return False



    def authorize(self):
        """ Verify authorization.

            Check if a user is authorized to perform a specific operation.
        """
        return False



class LdapAuth(BaseAuth):
    """ An authentication and authorization class for LDAP auth.
    """

    # TODO: clean away fuxxhaxx
    import temphaxx

    _ldap_uri = temphaxx.uri
    _ldap_basedn = temphaxx.basedn
    _ldap_conn = None
    _authenticated = None

    def __init__(self, username, password, authoritative_source, auth_options={}):
        """ Constructor.
        """

        BaseAuth.__init__(self, username, password, authoritative_source, 'ldap', auth_options)

        self._logger.debug('creating instance')

        self._logger.debug('LDAP URI: ' + self._ldap_uri)
        self._ldap_conn = ldap.initialize(self._ldap_uri)

        # run authentication method to populate instance variables
        self.authenticate()



    def authenticate(self):
        """ Verify authentication.
        """

        # if authentication has been performed, return last result
        if self._authenticated is not None:
            return self._authenticated

        try:
            self._ldap_conn.simple_bind_s('uid=' + self.username + ',' + self._ldap_basedn, self.password)
        except ldap.SERVER_DOWN, exc:
            self._logger.error('Could not connect to LDAP server: %s' % str(exc[0]['info']))
            raise AuthError(str(exc[0]['info']))
        except ldap.INVALID_CREDENTIALS, exc:
            # Auth failed
            self._logger.debug('erroneous password for user %s' % self.username)
            self._authenticated = False
            return self._authenticated


        # auth succeeded
        self.authenticated_as = self.username
        self._authenticated = True
        self.trusted = False

        try:
            res = self.search_s(self._ldap_basedn, ldap.SCOPE_SUBTREE, 'uid=' + self.username, ['cn']);
            self.full_name = res[0][1]['cn'][0]
        except:
            self.full_name = ''

        self._logger.debug('successfully authenticated as %s, username %s' % (self.authenticated_as, self.username))
        return self._authenticated



class SqliteAuth(BaseAuth):
    """ An authentication and authorization class for local auth.
    """

    _db_path = '/tmp/nap_auth.db'
    _db_conn = None
    _db_curs = None
    _authenticated = None

    def __init__(self, username, password, authoritative_source, auth_options={}):
        """ Constructor.

            Verifies that the auth database exists.
        """

        BaseAuth.__init__(self, username, password, authoritative_source, 'local', auth_options)

        self._logger.debug('creating instance')

        # make sure that user table exists
        sql_verify_table = '''SELECT * FROM sqlite_master
            WHERE type = 'table' AND name = 'user' '''

        # connect to database
        try:
            self._db_conn = sqlite3.connect(self._db_path, check_same_thread = False)
            self._db_conn.row_factory = sqlite3.Row
            self._db_curs = self._db_conn.cursor()
            self._db_curs.execute(sql_verify_table)

            if len(self._db_curs.fetchall()) < 1:
                self._logger.info('user database does not exist')
                self._setup_database()

        except sqlite3.Error, e:
            self._logger.error('Could not open user database: %s' % str(e))
            raise AuthError(str(e))


        # run authentication method to populate instance variables
        self.authenticate()



    def _setup_database(self):
        """ Set up database

            Creates tables required for the authentication module.
        """

        self._logger.info('creating user database')
        sql = '''CREATE TABLE IF NOT EXISTS user (
            username NOT NULL PRIMARY KEY,
            pwd_salt NOT NULL,
            pwd_hash NOT NULL,
            full_name,
            trusted NOT NULL DEFAULT 0
        )'''
        self._db_curs.execute(sql)
        self._db_conn.commit()



    def authenticate(self):
        """ Verify authentication.
        """

        # if authentication has been performed, return last result
        if self._authenticated is not None:
            return self._authenticated

        sql = '''SELECT * FROM user WHERE username = ?'''
        self._db_curs.execute(sql, (self.username, ))
        user = self._db_curs.fetchone()

        # Was user found?
        if user is None:
            self._logger.debug('unknown user %s' % self.username)
            self._authenticated = False
            return self._authenticated

        # verify password
        if self._gen_hash(self.password, user['pwd_salt']) != user['pwd_hash']:
            # Auth failed
            self._logger.debug('erroneous password for user %s' % self.username)
            self._authenticated = False
            return self._authenticated

        # auth succeeded
        self.authenticated_as = self.username
        self._authenticated = True
        self.trusted = bool(user['trusted'])

        if self.trusted:
            # user can impersonate other users
            # this also means that a system and full_name can be specified
            if 'username' in self._auth_options:
                self.username = self._auth_options['username']

            # TODO: b0rk out if full_name is supplied and username not?
            if 'full_name' in self._auth_options:
                self.full_name = self._auth_options['full_name']

            if 'authoritative_source' in self._auth_options:
                self.authoritative_source = self._auth_options['authoritative_source']

        else:
            self.full_name = user['full_name']

        self._logger.debug('successfully authenticated as %s, username %s, full_name %s' % (self.authenticated_as, self.username, self.full_name))
        return self._authenticated



    def add_user(self, username, password, full_name=None, trusted=False):
        """ Add user to SQLite database.
        """

        # generate salt
        char_set = string.ascii_letters + string.digits
        salt = ''.join(random.choice(char_set) for x in range(8))


        sql = '''INSERT INTO user
            (username, pwd_salt, pwd_hash, full_name, trusted)
            VALUES
            (?, ?, ?, ?, ?)'''
        self._db_curs.execute(sql, (username, salt,
                self._gen_hash(password, salt), full_name, trusted))
        self._db_conn.commit()



    def remove_user(self, username):
        """ Remove user from the SQLite database.
        """

        sql = '''DELETE FROM user WHERE username = ?'''
        self._db_curs.execute(sql, (username, ))
        self._db_conn.commit()
        return self._db_curs.rowcount



    def list_users(self):
        """ List all users.
        """
        sql = "SELECT * FROM user ORDER BY username";
        self._db_curs.execute(sql)
        users = list()
        for row in self._db_curs:
            users.append(dict(row))
        return users



    def _gen_hash(self, password, salt):
        """ Generate password hash.
        """

        # generate hash
        h = hashlib.sha1()
        h.update(salt)
        h.update(password)
        return h.hexdigest()



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
