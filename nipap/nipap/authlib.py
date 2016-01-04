""" Authentication library
    ======================

    A base authentication & authorization module.

    Includes the base class BaseAuth.

    Authentication and authorization in NIPAP
    -----------------------------------------
    NIPAP offers basic authentication with two different backends, a simple
    two-level authorization model and a trust-system for simplifying system
    integration.

    Readonly users are only authorized to run queries which do not modify any
    data in the database. No further granularity of access control is offered at
    this point.

    Trusted users can perform operations which will be logged as performed by
    another user. This feature is meant for system integration, for example to
    be used by a NIPAP client which have its own means of authentication users;
    say for example a web application supporting the NTLM single sign-on
    feature. By letting the web application use a trusted account to
    authenticate against the NIPAP service, it can specify the username of the
    end-user, so that audit logs will be written with the correct information.
    Without the trusted-bit, all queries performed by end-users through this
    system would look like they were performed by the system itself.

    The NIPAP auth system also has a concept of authoritative source. The
    authoritative source is a string which simply defines what system is the
    authoritative source of data for a prefix. Well-behaved clients SHOULD
    present a warning to the user when trying to alter a prefix with an
    authoritative source different than the system itself, as other system might
    depend on the information being unchanged. This is however, by no means
    enforced by the NIPAP service.

    Authentication backends
    -----------------------
    Two authentication backends are shipped with NIPAP:

    * LdapAuth - authenticates users against an LDAP server
    * SqliteAuth - authenticates users against a local SQLite-database

    The authentication classes presented here are used both in the NIPAP web UI
    and in the XML-RPC backend. So far only the SqliteAuth backend supports
    trusted and readonly users.

    What authentication backend to use can be specified by suffixing the
    username with @`backend`, where `backend` is set in the configuration file.
    If not defined, a (configurable) default backend is used.

    Authentication options
    ----------------------
    With each NIPAP query authentication options can be specified. The
    authentication options are passed as a dict with the following keys taken
    into account:

    * :attr:`authoritative_source` - Authoritative source for the query.
    * :attr:`username` - Username to impersonate, requires authentication as \
        trusted user.
    * :attr:`full_name` - Full name of impersonated user.
    * :attr:`readonly` - True for read-only users

    Classes
    -------
"""

import logging
from datetime import datetime, timedelta
import hashlib

from nipapconfig import NipapConfig

# Used by auth modules
import sqlite3
import string
import random

try:
    import ldap
except ImportError:
    ldap = None


class AuthFactory:
    """ An factory for authentication backends.
    """

    _logger = None
    _config = None
    _auth_cache = {}
    _backends = {}


    def __init__(self):
        """ Constructor.
        """

        # Initialize stuff.
        self._config = NipapConfig()
        self._logger = logging.getLogger(self.__class__.__name__)
        self._init_backends()



    def _init_backends(self):
        """ Initialize auth backends.
        """

        # fetch auth backends from config file
        self._backends = {}
        for section in self._config.sections():

            # does the section define an auth backend?
            section_components = section.rsplit('.', 1)
            if section_components[0] == 'auth.backends':
                auth_backend = section_components[1]
                self._backends[auth_backend] = eval(self._config.get(section, 'type'))

        self._logger.debug("Registered auth backends %s" % str(self._backends))



    def reload(self):
        """ Reload AuthFactory.
        """

        self._auth_cache = {}
        self._init_backends()



    def get_auth(self, username, password, authoritative_source, auth_options=None):
        """ Returns an authentication object.
    
            Examines the auth backend given after the '@' in the username and
            returns a suitable instance of a subclass of the BaseAuth class.

            * `username` [string]
                Username to authenticate as.
            * `password` [string]
                Password to authenticate with.
            * `authoritative_source` [string]
                Authoritative source of the query.
            * `auth_options` [dict]
                A dict which, if authenticated as a trusted user, can override
                `username` and `authoritative_source`.
        """

        if auth_options is None:
            auth_options = {}

        # validate arguments
        if (authoritative_source is None):
            raise AuthError("Missing authoritative_source.")

        # remove invalid cache entries
        rem = list()
        for key in self._auth_cache:
            if self._auth_cache[key]['valid_until'] < datetime.utcnow():
                rem.append(key)
        for key in rem:
            del(self._auth_cache[key])

        user_authbackend = username.rsplit('@', 1)
    
        # Find out what auth backend to use.
        # If no auth backend was specified in username, use default
        backend = ""
        if len(user_authbackend) == 1:
            backend = self._config.get('auth', 'default_backend')
            self._logger.debug("Using default auth backend %s" % backend)
        else:
            backend = user_authbackend[1]
    
        # do we have a cached instance?
        auth_str = ( str(username) + str(password) + str(authoritative_source)
            + str(auth_options) )
        if auth_str in self._auth_cache:
            self._logger.debug('found cached auth object for user %s' % username)
            return self._auth_cache[auth_str]['auth_object']

        # Create auth object
        try:
            auth = self._backends[backend](backend, user_authbackend[0], password, authoritative_source, auth_options)
        except KeyError:
            raise AuthError("Invalid auth backend '%s' specified" %
                str(backend))

        # save auth object to cache
        self._auth_cache[auth_str] = {
            'valid_until': datetime.utcnow() + timedelta(seconds=self._config.getint('auth', 'auth_cache_timeout')),
            'auth_object': auth
        }

        return auth



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
    readonly = None

    _logger = None
    _auth_options = None
    _cfg = None


    def __init__(self, username, password, authoritative_source, auth_backend, auth_options=None):
        """ Constructor.

            Note that the instance variables not are set by the constructor but
            by the :func:`authenticate` method. Therefore, run the
            :func:`authenticate`-method before trying to access those
            variables!

            * `username` [string]
                Username to authenticate as.
            * `password` [string]
                Password to authenticate with.
            * `authoritative_source` [string]
                Authoritative source of the query.
            * `auth_backend` [string]
                Name of authentication backend.
            * `auth_options` [dict]
                A dict which, if authenticated as a trusted user, can override
                `username` and `authoritative_source`.
        """

        if auth_options is None:
            auth_options = {}

        self._logger = logging.getLogger(self.__class__.__name__)
        self._cfg = NipapConfig()

        self.username = username
        self.password = password
        self.auth_backend = auth_backend
        self.authoritative_source = authoritative_source

        self._auth_options = auth_options



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

    _ldap_uri = None
    _ldap_basedn = None
    _ldap_binddn_fmt = None
    _ldap_search = None
    _ldap_search_binddn = None
    _ldap_search_password = None
    _ldap_rw_group = None
    _ldap_ro_group = None
    _ldap_conn = None
    _ldap_search_conn = None
    _authenticated = None

    def __init__(self, name, username, password, authoritative_source, auth_options=None):
        """ Constructor.

            Note that the instance variables not are set by the constructor but
            by the :func:`authenticate` method. Therefore, run the
            :func:`authenticate`-method before trying to access those
            variables!

            * `name` [string]
                Name of auth backend.
            * `username` [string]
                Username to authenticate as.
            * `password` [string]
                Password to authenticate with.
            * `authoritative_source` [string]
                Authoritative source of the query.
            * `auth_options` [dict]
                A dict which, if authenticated as a trusted user, can override
                `username` and `authoritative_source`.
        """

        if auth_options is None:
            auth_options = {}

        BaseAuth.__init__(self, username, password, authoritative_source, name, auth_options)
        base_auth_backend = 'auth.backends.' + self.auth_backend
        self._ldap_uri = self._cfg.get(base_auth_backend, 'uri')
        self._ldap_basedn = self._cfg.get(base_auth_backend, 'basedn')
        self._ldap_binddn_fmt = self._cfg.get(base_auth_backend, 'binddn_fmt')
        self._ldap_search = self._cfg.get(base_auth_backend, 'search')
        self._ldap_tls = False

        if self._cfg.has_option(base_auth_backend, 'tls'):
            self._ldap_tls = self._cfg.getboolean(base_auth_backend, 'tls')

        self._ldap_ro_group = None
        self._ldap_rw_group = None
        if self._cfg.has_option(base_auth_backend, 'ro_group'):
            self._ldap_ro_group = self._cfg.get(base_auth_backend, 'ro_group')
        if self._cfg.has_option(base_auth_backend, 'rw_group'):
            self._ldap_rw_group = self._cfg.get(base_auth_backend, 'rw_group')

        self._logger.debug('Creating LdapAuth instance')

        if not ldap:
            self._logger.error('Unable to load Python ldap module, please verify it is installed')
            raise AuthError('Unable to authenticate')

        self._logger.debug('LDAP URI: ' + self._ldap_uri)
        self._ldap_conn = ldap.initialize(self._ldap_uri)

        # Shall we use a separate connection for search?
        if self._cfg.has_option(base_auth_backend, 'search_binddn'):
            self._ldap_search_binddn = self._cfg.get(base_auth_backend, 'search_binddn')
            self._ldap_search_password = self._cfg.get(base_auth_backend, 'search_password')
            self._ldap_search_conn = ldap.initialize(self._ldap_uri)

        if self._ldap_tls:
            try:
                self._ldap_conn.start_tls_s()
                if self._ldap_search_conn is not None:
                    self._ldap_search_conn.start_tls_s()
            except (ldap.CONNECT_ERROR, ldap.SERVER_DOWN) as exc:
                self._logger.error('Attempted to start TLS with ldap server but failed.')
                self._logger.exception(exc)
                raise AuthError('Unable to establish secure connection to ldap server')


    def authenticate(self):
        """ Verify authentication.

            Returns True/False dependant on whether the authentication
            succeeded or not.
        """

        # if authentication has been performed, return last result
        if self._authenticated is not None:
            return self._authenticated

        try:
            self._ldap_conn.simple_bind_s(self._ldap_binddn_fmt.format(ldap.dn.escape_dn_chars(self.username)), self.password)
        except ldap.SERVER_DOWN as exc:
            raise AuthError('Could not connect to LDAP server')
        except (ldap.INVALID_CREDENTIALS, ldap.INVALID_DN_SYNTAX,
                ldap.UNWILLING_TO_PERFORM) as exc:
            # Auth failed
            self._logger.debug('erroneous password for user %s' % self.username)
            self._authenticated = False
            return self._authenticated


        # auth succeeded
        self.authenticated_as = self.username
        self.trusted = False
        self.readonly = False

        try:
            # Create separate connection for search?
            if self._ldap_search_conn is not None:
                self._ldap_search_conn.simple_bind(self._ldap_search_binddn, self._ldap_search_password)
                search_conn = self._ldap_search_conn
            else:
                search_conn = self._ldap_conn

            res = search_conn.search_s(self._ldap_basedn, ldap.SCOPE_SUBTREE, self._ldap_search.format(ldap.dn.escape_dn_chars(self.username)), ['cn','memberOf'])
            self.full_name = res[0][1]['cn'][0]
            # check for ro_group membership if ro_group is configured
            if self._ldap_ro_group:
                if self._ldap_ro_group in res[0][1].get('memberOf', []):
                    self.readonly = True
            # check for rw_group membership if rw_group is configured
            if self._ldap_rw_group:
                if self._ldap_rw_group in res[0][1].get('memberOf', []):
                    self.readonly = False
                else:
                    # if ro_group is configured, and the user is a member of
                    # neither the ro_group nor the rw_group, fail authentication.
                    if self._ldap_ro_group:
                        if self._ldap_ro_group not in res[0][1].get('memberOf', []):
                            self._authenticated = False
                            return self._authenticated
                    else:
                        self.readonly = True

        except ldap.LDAPError as exc:
            raise AuthError(exc)
        except KeyError:
            raise AuthError('LDAP attribute missing')
        except IndexError:
            self.full_name = ''
            # authentication fails if either ro_group or rw_group are configured
            # and the user is not found.
            if self._ldap_rw_group or self._ldap_ro_group:
                self._authenticated = False
                return self._authenticated

        self._authenticated = True

        self._logger.debug('successfully authenticated as %s, username %s, full_name %s, readonly %s' % (self.authenticated_as, self.username, self.full_name, str(self.readonly)))
        return self._authenticated



class SqliteAuth(BaseAuth):
    """ An authentication and authorization class for local auth.
    """

    _db_conn = None
    _db_curs = None
    _authenticated = None

    def __init__(self, name, username, password, authoritative_source, auth_options=None):
        """ Constructor.

            Note that the instance variables not are set by the constructor but
            by the :func:`authenticate` method. Therefore, run the
            :func:`authenticate`-method before trying to access those
            variables!

            * `name` [string]
                Name of auth backend.
            * `username` [string]
                Username to authenticate as.
            * `password` [string]
                Password to authenticate with.
            * `authoritative_source` [string]
                Authoritative source of the query.
            * `auth_options` [dict]
                A dict which, if authenticated as a trusted user, can override
                `username` and `authoritative_source`.

            If the user database and tables are not found, they are created.
        """

        if auth_options is None:
            auth_options = {}

        BaseAuth.__init__(self, username, password, authoritative_source, name, auth_options)

        self._logger.debug('Creating SqliteAuth instance')

        # connect to database
        try:
            self._db_conn = sqlite3.connect(self._cfg.get('auth.backends.' + self.auth_backend, 'db_path'), check_same_thread = False)
            self._db_conn.row_factory = sqlite3.Row
            self._db_curs = self._db_conn.cursor()

        except sqlite3.Error as exc:
            self._logger.error('Could not open user database: %s' % str(exc))
            raise AuthError(str(exc))



    def _latest_db_version(self):
        """ Check if database is of the latest version

            Fairly stupid functions that simply checks for existence of columns.
        """
        # make sure that user table exists
        sql_verify_table = '''SELECT * FROM sqlite_master
            WHERE type = 'table' AND name = 'user' '''
        self._db_curs.execute(sql_verify_table)
        if len(self._db_curs.fetchall()) < 1:
            raise AuthSqliteError("No 'user' table.")

        for column in ('username', 'pwd_salt', 'pwd_hash', 'full_name',
                'trusted', 'readonly'):
            sql = "SELECT %s FROM user" % column
            try:
                self._db_curs.execute(sql)
            except:
                return False

        return True



    def _create_database(self):
        """ Set up database

            Creates tables required for the authentication module.
        """

        self._logger.info('creating user database')
        sql = '''CREATE TABLE IF NOT EXISTS user (
            username NOT NULL PRIMARY KEY,
            pwd_salt NOT NULL,
            pwd_hash NOT NULL,
            full_name,
            trusted NOT NULL DEFAULT 0,
            readonly NOT NULL DEFAULT 0
        )'''
        self._db_curs.execute(sql)
        self._db_conn.commit()



    def _upgrade_database(self):
        """ Upgrade database to latest version

            This is a fairly primitive function that won't look at how the
            database looks like but just blindly run commands.
        """
        self._logger.info('upgrading user database')
        # add readonly column
        try:
            sql = '''ALTER TABLE user ADD COLUMN readonly NOT NULL DEFAULT 0'''
            self._db_curs.execute(sql)
        except:
            pass
        self._db_conn.commit()



    def authenticate(self):
        """ Verify authentication.

            Returns True/False dependant on whether the authentication
            succeeded or not.
        """

        # if authentication has been performed, return last result
        if self._authenticated is not None:
            return self._authenticated

        self._logger.debug('Trying to authenticate as user \'%s\'' % self.username)

        user = self.get_user(self.username)
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
        self.readonly = bool(user['readonly'])

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

            if 'readonly' in self._auth_options:
                self.readonly = self._auth_options['readonly']

        else:
            self.full_name = user['full_name']

        self._logger.debug('successfully authenticated as %s, username %s, full_name %s, readonly %s' % (self.authenticated_as, self.username, self.full_name, str(self.readonly)))
        return self._authenticated



    def get_user(self, username):
        """ Fetch the user from the database

            The function will return None if the user is not found
        """

        sql = '''SELECT * FROM user WHERE username = ?'''
        self._db_curs.execute(sql, (username, ))
        user = self._db_curs.fetchone()
        return user



    def add_user(self, username, password, full_name=None, trusted=False, readonly=False):
        """ Add user to SQLite database.

            * `username` [string]
                Username of new user.
            * `password` [string]
                Password of new user.
            * `full_name` [string]
                Full name of new user.
            * `trusted` [boolean]
                Whether the new user should be trusted or not.
            * `readonly` [boolean]
                Whether the new user can only read or not
        """

        # generate salt
        char_set = string.ascii_letters + string.digits
        salt = ''.join(random.choice(char_set) for x in range(8))


        sql = '''INSERT INTO user
            (username, pwd_salt, pwd_hash, full_name, trusted, readonly)
            VALUES
            (?, ?, ?, ?, ?, ?)'''
        try:
            self._db_curs.execute(sql, (username, salt,
                self._gen_hash(password, salt), full_name, trusted or False,
                                        readonly or False))
            self._db_conn.commit()
        except (sqlite3.OperationalError, sqlite3.IntegrityError) as error:
            raise AuthError(error)



    def remove_user(self, username):
        """ Remove user from the SQLite database.

            * `username` [string]
                Username of user to remove.
        """

        sql = '''DELETE FROM user WHERE username = ?'''
        try:
            self._db_curs.execute(sql, (username, ))
            self._db_conn.commit()
        except (sqlite3.OperationalError, sqlite3.IntegrityError) as error:
            raise AuthError(error)
        return self._db_curs.rowcount



    def modify_user(self, username, data):
        """ Modify user in SQLite database.

            Since username is used as primary key and we only have a single
            argument for it we can't modify the username right now.
        """
        sql = "UPDATE user SET "
        sql += ', '.join("%s = ?" % k for k in sorted(data))
        sql += " WHERE username = ?"

        vals = []
        for k in sorted(data):
            vals.append(data[k])
        vals.append(username)

        try:
            self._db_curs.execute(sql, vals)
            self._db_conn.commit()
        except (sqlite3.OperationalError, sqlite3.IntegrityError) as error:
            raise AuthError(error)



    def list_users(self):
        """ List all users.
        """
        sql = "SELECT * FROM user ORDER BY username"
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
    error_code = 1500


class AuthenticationFailed(AuthError):
    """ Authentication failed.
    """
    error_code = 1510


class AuthorizationFailed(AuthError):
    """ Authorization failed.
    """
    error_code = 1520


class AuthSqliteError(AuthError):
    """ Problem with the Sqlite database
    """
