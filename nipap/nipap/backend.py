""" NIPAP API
    =========

    This module contains the Nipap class which provides most of the backend
    logic in NIPAP apart from that contained within the PostgreSQL database.

    NIPAP contains four types of objects: ASNs, VRFs, prefixes and pools.

    VRF
    ------
    A VRF represents a Virtual Routing and Forwarding instance. By default, one
    VRF which represents the global routing table (VRF "default") is defined. This
    VRF always has the ID 0.

    VRF attributes
    ^^^^^^^^^^^^^^
    * :attr:`id` - ID number of the VRF.
    * :attr:`vrf` - The VRF RDs administrator and assigned number subfields
        (eg. 65000:123).
    * :attr:`name` - A short name, such as 'VPN Customer A'.
    * :attr:`description` - A longer description of what the VRF is used for.
    * :attr:`tags` - Tag keywords for simple searching and filtering of VRFs.
    * :attr:`avps` - Attribute-Value Pairs. This field can be used to add
        various extra attributes that a user wishes to store together with a
        VRF.

    VRF functions
    ^^^^^^^^^^^^^
    * :func:`~Nipap.list_vrf` - Return a list of VRFs.
    * :func:`~Nipap.add_vrf` - Create a new VRF.
    * :func:`~Nipap.edit_vrf` - Edit a VRF.
    * :func:`~Nipap.remove_vrf` - Remove a VRF.
    * :func:`~Nipap.search_vrf` - Search VRFs based on a formatted dict.
    * :func:`~Nipap.smart_search_vrf` - Search VRFs based on a query string.


    Prefix
    ------
    A prefix object defines an IP address prefix. Prefixes can be one of three
    different types; reservation, assignment or host.
    Reservation; a prefix which is reserved for future use.
    Assignment; addresses assigned to a specific purpose.
    Host; prefix of max length within an assigment, assigned to an end host.

    Prefix attributes
    ^^^^^^^^^^^^^^^^^
    * :attr:`id` - ID number of the prefix.
    * :attr:`prefix` - The IP prefix itself.
    * :attr:`display_prefix` - A more user-friendly version of the prefix.
    * :attr:`family` - Address family (integer 4 or 6). Set by NIPAP.
    * :attr:`vrf_id` - ID of the VRF which the prefix belongs to.
    * :attr:`vrf_rt` - RT of the VRF which the prefix belongs to.
    * :attr:`vrf_name` - Name of VRF which the prefix belongs to.
    * :attr:`description` - A short description of the prefix.
    * :attr:`comment` - A longer text describing the prefix and its use.
    * :attr:`node` - Name of the node on which the address is configured.
    * :attr:`pool_id` - ID of pool, if the prefix belongs to a pool.
    * :attr:`pool_name` - Name of pool, if the prefix belongs to a pool.
    * :attr:`type` - Prefix type, string 'reservation', 'assignment' or 'host'.
    * :attr:`status` - Status, string 'assigned', 'reserved' or 'quarantine'.
    * :attr:`indent` - Depth in prefix tree. Set by NIPAP.
    * :attr:`country` - Two letter country code where the prefix resides.
    * :attr:`order_id` - Order identifier.
    * :attr:`customer_id` - Customer identifier.
    * :attr:`vlan` - VLAN identifier, 0-4096.
    * :attr:`tags` - Tag keywords for simple searching and filtering of prefixes.
    * :attr:`avps` - Attribute-Value Pairs. This field can be used to add
        various extra attributes that a user wishes to store together with a
        prefix.
    * :attr:`expires` - Set a date and time for when the prefix assignment
        expires. Multiple formats are supported for specifying time, for
        absolute time ISO8601 style dates can be used and None or the text
        strings 'never' or 'infinity' is treated as positive infinity and means
        the assignment never expires. It is also possible to specify relative
        time and a fuzzy parser is used to interpret strings such as "tomorrow"
        or "2 years" into an absolute time.
    * :attr:`external_key` - A field for use by external systems which needs to
        store references to its own dataset.
    * :attr:`authoritative_source` - String identifying which system last
        modified the prefix.
    * :attr:`alarm_priority` - String 'warning', 'low', 'medium', 'high' or
        'critical'.
    * :attr:`monitor` - A boolean specifying whether the prefix should be
        monitored or not.
    * :attr:`display` - Only set by the :func:`~Nipap.search_prefix` and
        :func:`~Nipap.smart_search_prefix` functions, see their documentation for
        explanation.

    Prefix functions
    ^^^^^^^^^^^^^^^^
    * :func:`~Nipap.list_prefix` - Return a list of prefixes.
    * :func:`~Nipap.add_prefix` - Add a prefix, more or less automatically.
    * :func:`~Nipap.edit_prefix` - Edit a prefix.
    * :func:`~Nipap.remove_prefix` - Remove a prefix.
    * :func:`~Nipap.search_prefix` - Search prefixes based on a formatted dict.
    * :func:`~Nipap.smart_search_prefix` - Search prefixes based on a string.


    Pool
    ----
    A pool is used to group together a number of prefixes for the purpose of
    assigning new prefixes from that pool. :func:`~Nipap.add_prefix` can for
    example be asked to return a new prefix from a pool. All prefixes that are
    members of the pool will be examined for free space and a new prefix, of the
    specified prefix-length, will be returned to the user.

    Pool attributes
    ^^^^^^^^^^^^^^^
    * :attr:`id` - ID number of the pool.
    * :attr:`name` - A short name.
    * :attr:`description` - A longer description of the pool.
    * :attr:`default_type` - Default prefix type (see prefix types above.
    * :attr:`ipv4_default_prefix_length` - Default prefix length of IPv4 prefixes.
    * :attr:`ipv6_default_prefix_length` - Default prefix length of IPv6 prefixes.
    * :attr:`tags` - Tag keywords for simple searching and filtering of pools.
    * :attr:`avps` - Attribute-Value Pairs. This field can be used to add
        various extra attributes that a user wishes to store together with a
        pool.

    Pool functions
    ^^^^^^^^^^^^^^
    * :func:`~Nipap.list_pool` - Return a list of pools.
    * :func:`~Nipap.add_pool` - Add a pool.
    * :func:`~Nipap.edit_pool` - Edit a pool.
    * :func:`~Nipap.remove_pool` - Remove a pool.
    * :func:`~Nipap.search_pool` - Search pools based on a formatted dict.
    * :func:`~Nipap.smart_search_pool` - Search pools based on a string.

    ASN
    ---
    An ASN object represents an Autonomous System Number (ASN).

    ASN attributes
    ^^^^^^^^^^^^^^
    * :attr:`asn` - AS number.
    * :attr:`name` - A name of the AS number.

    ASN functions
    ^^^^^^^^^^^^^
    * :func:`~Nipap.list_asn` - Return a list of ASNs.
    * :func:`~Nipap.add_asn` - Add an ASN.
    * :func:`~Nipap.edit_asn` - Edit an ASN.
    * :func:`~Nipap.remove_asn` - Remove an ASN.
    * :func:`~Nipap.search_asn` - Search ASNs based on a formatted dict.
    * :func:`~Nipap.smart_search_asn` - Search ASNs based on a string.


    The 'spec'
    ----------
    Central to the use of the NIPAP API is the spec -- the specifier. It is used
    by many functions to in a more dynamic way specify what element(s) you want
    to select. Mainly it came to be due to the use of two attributes which can
    be thought of as primary keys for an object, such as a pool's :attr:`id` and
    :attr:`name` attribute. They are however implemented so that you can use
    more or less any attribute in the spec, to be able to for example get all
    prefixes of family 6 with type reservation.

    The spec is a dict formatted as::

        vrf_spec = {
            'id': 512
        }

    But can also be elaborated somehwat for certain objects, as::

        prefix_spec = {
            'family': 6,
            'type': 'reservation'
        }

    If multiple keys are given, they will be ANDed together.

    Authorization & accounting
    --------------------------
    With each query an object extending the BaseAuth class should be passed.
    This object is used in the Nipap class to perform authorization (not yet
    implemented) and accounting. Authentication should be performed at an
    earlier stage and is NOT done in the Nipap class.

    Each command which alters data stored in NIPAP is logged. There are
    currently no API functions for extracting this data, but this will change
    in the future.

    Classes
    -------
"""
from functools import wraps
import dateutil.parser
import datetime
import exceptions
import logging
import psycopg2
import psycopg2.extras
import pytz
import shlex
import socket
import time
import re
import IPy

import authlib

# support multiple versions of parsedatetime
try:
    import parsedatetime
    pdt = parsedatetime.Calendar(parsedatetime.Constants(usePyICU=False))
except:
    import parsedatetime.parsedatetime
    import parsedatetime.parsedatetime_consts as pdc
    pdt = parsedatetime.parsedatetime.Calendar(pdc.Constants())

_operation_map = {
    'and': 'AND',
    'or': 'OR',
    'equals_any': '= ANY',
    'equals': '=',
    'less': '<',
    'less_or_equal': '<=',
    'greater': '>',
    'greater_or_equal': '>=',
    'is': 'IS',
    'is_not': 'IS NOT',
    'not_equals': '!=',
    'like': 'LIKE',
    'regex_match': '~*',
    'regex_not_match': '!~*',
    'contains': '>>',
    'contains_equals': '>>=',
    'contained_within': '<<',
    'contained_within_equals': '<<='
    }
""" Maps operators in a prefix query to SQL operators.
"""



def requires_rw(f):
    """ Adds readwrite authorization

        This will check if the user is a readonly user and if so reject the
        query. Apply this decorator to readwrite functions.
    """
    @wraps(f)

    def decorated(*args, **kwargs):
        auth = args[1]
        if auth.readonly:
            logger = logging.getLogger()
            logger.info("read-only user '%s' is not authorized to run function '%s'" % (auth.username, f.__name__))
            raise authlib.AuthorizationFailed("read-only user '%s' is not authorized to run function '%s'" % (auth.username, f.__name__))
        return f(*args, **kwargs)

    return decorated





class Inet(object):
    """ This works around a bug in psycopg2 version somewhere before 2.4.  The
        __init__ function in the original class is broken and so this is merely
        a copy with the bug fixed.

        Wrap a string to allow for correct SQL-quoting of inet values.

        Note that this adapter does NOT check the passed value to make sure it
        really is an inet-compatible address but DOES call adapt() on it to make
        sure it is impossible to execute an SQL-injection by passing an evil
        value to the initializer.
    """
    def __init__(self, addr):
        self.addr = addr

    def prepare(self, conn):
        self._conn = conn

    def getquoted(self):
        obj = adapt(self.addr)
        if hasattr(obj, 'prepare'):
            obj.prepare(self._conn)
        return obj.getquoted()+"::inet"

    def __str__(self):
        return str(self.addr)


def _parse_expires(expires):
    """ Parse the 'expires' attribute, guessing what format it is in and
        returning a datetime
    """
    # none is used to signify positive infinity
    if expires is None or expires in ('never', 'infinity'):
        return 'infinity'

    try:
        return dateutil.parser.parse(str(expires))
    except ValueError as exc:
        pass

    try:
        # use parsedatetime for "human readable" time specs
        exp = pdt.parse(expires)[0]
        # and convert to datetime
        return datetime.datetime.fromtimestamp(time.mktime(exp))
    except ValueError as exc:
        pass

    raise NipapValueError("Invalid date specification for expires")


class Nipap:
    """ Main NIPAP class.

        The main NIPAP class containing all API methods. When creating an
        instance, a database connection object is created which is used during
        the instance's lifetime.
    """

    _logger = None
    _con_pg = None
    _curs_pg =  None

    def __init__(self):
        """ Constructor.

            Creates database connections n' stuff, yo.
        """

        self._logger = logging.getLogger(self.__class__.__name__)
        self._logger.debug("Initialising NIPAP")

        from nipapconfig import NipapConfig
        self._cfg = NipapConfig()

        self._connect_db()


    #
    # Miscellaneous help functions
    #

    def _register_inet(self, oid=None, conn_or_curs=None):
        """ Create the INET type and an Inet adapter."""
        from psycopg2 import extensions as _ext
        if not oid:
            oid = 869
        _ext.INET = _ext.new_type((oid, ), "INET",
                lambda data, cursor: data and Inet(data) or None)
        _ext.register_type(_ext.INET, self._con_pg)
        return _ext.INET



    def _is_ipv4(self, ip):
        """ Return true if given arg is a valid IPv4 address
        """
        try:
            p = IPy.IP(ip)
        except ValueError:
            return False

        if p.version() == 4:
            return True
        return False



    def _is_ipv6(self, ip):
        """ Return true if given arg is a valid IPv6 address
        """
        try:
            p = IPy.IP(ip)
        except ValueError:
            return False

        if p.version() == 6:
            return True
        return False



    def _get_afi(self, ip):
        """ Return address-family (4 or 6) for IP or None if invalid address
        """

        parts = unicode(ip).split("/")
        if len(parts) == 1:
            # just an address
            if self._is_ipv4(ip):
                return 4
            elif self._is_ipv6(ip):
                return 6
            else:
                return None
        elif len(parts) == 2:
            # a prefix!
            try:
                pl = int(parts[1])
            except ValueError:
                # if casting parts[1] to int failes, this is not a prefix..
                return None

            if self._is_ipv4(parts[0]):
                if pl >= 0 and pl <= 32:
                    # prefix mask must be between 0 and 32
                    return 4
                # otherwise error
                return None
            elif self._is_ipv6(parts[0]):
                if pl >= 0 and pl <= 128:
                    # prefix mask must be between 0 and 128
                    return 6
                # otherwise error
                return None
            else:
                return None
        else:
            # more than two parts.. this is neither an address or a prefix
            return None



    #
    # SQL related functions
    #

    def _connect_db(self):
        """ Open database connection
        """

        # Get database configuration
        db_args = {}
        db_args['host'] = self._cfg.get('nipapd', 'db_host')
        db_args['database'] = self._cfg.get('nipapd', 'db_name')
        db_args['user'] = self._cfg.get('nipapd', 'db_user')
        db_args['password'] = self._cfg.get('nipapd', 'db_pass')
        db_args['sslmode'] = self._cfg.get('nipapd', 'db_sslmode')
        # delete keys that are None, for example if we want to connect over a
        # UNIX socket, the 'host' argument should not be passed into the DSN
        if db_args['host'] is not None and db_args['host'] == '':
            db_args['host'] = None
        for key in db_args.copy():
            if db_args[key] is None:
                del(db_args[key])

        # Create database connection
        try:
            self._con_pg = psycopg2.connect(**db_args)
            self._con_pg.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            self._curs_pg = self._con_pg.cursor(cursor_factory=psycopg2.extras.DictCursor)
            self._register_inet()
            psycopg2.extras.register_hstore(self._con_pg, globally=True, unicode=True)
        except psycopg2.Error as exc:
            self._logger.error("pgsql: %s" % exc)
            raise NipapError("Backend unable to connect to database")
        except psycopg2.Warning as warn:
            self._logger.warning('pgsql: %s' % warn)



    def _execute(self, sql, opt=None, callno = 0):
        """ Execute query, catch and log errors.
        """

        self._logger.debug("SQL: " + sql + "  params: " + str(opt))
        try:
            self._curs_pg.execute(sql, opt)
        except psycopg2.InternalError as exc:
            self._con_pg.rollback()

            # NOTE: psycopg2 is unable to differentiate between exceptions
            # thrown by stored procedures and certain other database internal
            # exceptions, thus we do not know if the exception in question is
            # raised from our stored procedure or from some other error. In
            # addition, postgresql is unable to pass any error code for the
            # exception and so the only thing which we can look at is the actual
            # text string.
            #
            # Exceptions raised by our stored procedures will all start with an
            # error code followed by a colon, which separates the error code
            # from the text string that follows next. If the error text does not
            # follow this format it is likely not one of "our" exceptions and so
            # we throw (and log) a more general exception.

            # determine if it's "one of our" exceptions or something else
            if len(str(exc).split(":")) < 2:
                raise NipapError(exc)
            code = str(exc).split(":", 1)[0]
            try:
                int(code)
            except:
                raise NipapError(exc)

            text = str(exc).splitlines()[0].split(":", 1)[1]

            if code == '1200':
                raise NipapValueError(text)

            estr = "Internal database error: %s" % exc
            self._logger.error(estr)
            raise NipapError(str(exc))

        except psycopg2.IntegrityError as exc:
            self._con_pg.rollback()

            # this is a duplicate key error
            if exc.pgcode == "23505":
                # figure out which column it is and retrieve the database
                # description for that column
                m = re.match(r'.*"([^"]+)"', exc.pgerror)
                if m is None:
                    raise NipapDuplicateError("Objects primary keys already exist")
                cursor = self._con_pg.cursor()
                cursor.execute("""  SELECT
                                        obj_description(oid)
                                    FROM pg_class
                                    WHERE relname = %(relname)s""",
                                { 'relname': m.group(1) })
                column_desc = '<unknown>'
                for desc in cursor:
                    column_desc = str(desc[0])

                # figure out the value for the duplicate value
                column_value = None
                try:
                    m = re.match(r'.*=\(([^)]+)\) already exists.', exc.pgerror.splitlines()[1])
                    if m is not None:
                        column_value = m.group(1)
                except:
                    pass
                else:
                    raise NipapDuplicateError("Duplicate value for '" +
                        str(column_desc) + "', the value '" +
                        str(column_value) + "' is already in use.")

                raise NipapDuplicateError("Duplicate value for '" +
                    str(column_desc) +
                    "', the value you have inputted is already in use.")

            raise NipapError(str(exc))

        except psycopg2.DataError as exc:
            self._con_pg.rollback()

            m = re.search('invalid cidr value: "([^"]+)"', exc.pgerror)
            if m is not None:
                strict_prefix = str(IPy.IP(m.group(1), make_net = True))
                estr = "Invalid prefix (%s); bits set to right of mask. Network address for current mask: %s" % (m.group(1), strict_prefix)
                raise NipapValueError(estr)

            m = re.search('invalid input syntax for type (cidr|inet): "([^"]+)"', exc.pgerror)
            if m is not None:
                estr = "Invalid syntax for prefix (%s)" % m.group(2)
                raise NipapValueError(estr)

            raise NipapValueError(str(exc))

        except psycopg2.Error as exc:
            try:
                self._con_pg.rollback()
            except psycopg2.Error:
                pass

            estr = "Unable to execute query: %s" % exc
            self._logger.error(estr)

            # abort if we've already tried to reconnect
            if callno > 0:
                self._logger.error(estr)
                raise NipapError(estr)

            # reconnect to database and retry query
            self._logger.info("Reconnecting to database...")
            self._connect_db()

            return self._execute(sql, opt, callno + 1)

        except psycopg2.Warning as warn:
            self._logger.warning(str(warn))



    def _lastrowid(self):
        """ Get ID of last inserted column.
        """

        # TODO: hmm, we can do this by doing fetchone() on our cursor
        self._execute("SELECT lastval() AS last")
        for row in self._curs_pg:
            return row['last']



    def _sql_expand_insert(self, spec, key_prefix = '', col_prefix = ''):
        """ Expand a dict so it fits in a INSERT clause
        """
        col = list(spec)
        sql = '('
        sql += ', '.join(col_prefix + key for key in col)
        sql += ') VALUES ('
        sql += ', '.join('%(' + key_prefix + key + ')s' for key in col)
        sql += ')'
        params = {}
        for key in spec:
            params[key_prefix + key] = spec[key]

        return sql, params



    def _sql_expand_update(self, spec, key_prefix = '', col_prefix = ''):
        """ Expand a dict so it fits in a INSERT clause
        """
        sql = ', '.join(col_prefix + key + ' = %(' + key_prefix + key + ')s' for key in spec)
        params = {}
        for key in spec:
            params[key_prefix + key] = spec[key]

        return sql, params



    def _sql_expand_where(self, spec, key_prefix = '', col_prefix = ''):
        """ Expand a dict so it fits in a WHERE clause

            Logical operator is AND.
        """

        sql = ' AND '.join(col_prefix + key +
            ( ' IS ' if spec[key] is None else ' = ' ) +
            '%(' + key_prefix + key + ')s' for key in spec)
        params = {}
        for key in spec:
            params[key_prefix + key] = spec[key]

        return sql, params



    # TODO: make this more generic and use for testing of spec too?
    def _check_attr(self, attr, req_attr, allowed_attr):
        """
        """
        if type(attr) is not dict:
            raise NipapInputError("invalid input type, must be dict")

        for a in req_attr:
            if not a in attr:
                raise NipapMissingInputError("missing attribute %s" % a)
        for a in attr:
            if a not in allowed_attr:
                raise NipapExtraneousInputError("extraneous attribute %s" % a)



    def _get_updated_rows(self, auth, function):
        """ Get rows updated by last update query

            * `function` [function]
                Function to use for searching (one of the search_* functions).

            Helper function used to fetch all rows which was updated by the
            latest UPDATE ... RETURNING id query.
        """

        # Get dicts for all rows which were edited by building a query for
        # search_*. Each row returned from UPDATE ... RETURNING id gives us one
        # query part (qp) which then are combined to one big query for the
        # search_* API call.
        qps = []
        for row in self._curs_pg:
            qps.append(
                {
                    'operator': 'equals',
                    'val1': 'id',
                    'val2': row['id']
                }
            )

        # We can have zero modified rows. Deal with it.
        if len(qps) > 0:
            q = qps[0]

            for qp in qps[1:]:
                q = {
                    'operator': 'or',
                    'val1': q,
                    'val2': qp
                }

        updated = function(auth, q, { 'max_result': 10000 })['result']

        return updated



    def _get_query_parts(self, query_str, search_options=None):
        """ Split a query string into its parts
        """

        if search_options is None:
            search_options = {}

        if query_str is None:
            raise NipapValueError("'query_string' must not be None")

        # find query parts
        query_str_parts = []
        try:
            for part in shlex.split(query_str.encode('utf-8')):
                query_str_parts.append({ 'string': part.decode('utf-8') })
        except ValueError as exc:
            if str(exc) == 'No closing quotation':
                raise NipapValueError(str(exc))
            raise exc

        # Handle empty search.
        # We need something to iterate over, but shlex.split() returns
        # zero-element list for an empty string, so we have to append one
        # manually
        if len(query_str_parts) == 0:
            query_str_parts.append({ 'string': '' })

        return query_str_parts



    def _get_db_version(self):
        """ Get the schema version of the nipap psql db.
        """

        dbname = self._cfg.get('nipapd', 'db_name')
        self._execute("SELECT description FROM pg_shdescription JOIN pg_database ON objoid = pg_database.oid WHERE datname = '%s'" % dbname)
        comment = self._curs_pg.fetchone()
        if comment is None:
            raise NipapError("Could not find comment of psql database %s" % dbname)

        db_version = None
        m = re.match('NIPAP database - schema version: ([0-9]+)', comment[0])
        if m:
            db_version = int(m.group(1))
        else:
            raise NipapError("Could not match schema version database comment")

        return db_version




    #
    # VRF functions
    #
    def _expand_vrf_spec(self, spec):
        """ Expand VRF specification to SQL.

            id [integer]
                internal database id of VRF

            name [string]
                name of VRF

            A VRF is referenced either by its internal database id or by its
            name. Both are used for exact matching and so no wildcard or
            regular expressions are allowed. Only one key may be used and an
            error will be thrown if both id and name is specified.
        """

        if type(spec) is not dict:
            raise NipapInputError("vrf specification must be a dict")

        allowed_values = ['id', 'name', 'rt']
        for a in spec:
            if a not in allowed_values:
                raise NipapExtraneousInputError("extraneous specification key %s" % a)

        if 'id' in spec:
            if type(spec['id']) not in (int, long):
                raise NipapValueError("VRF specification key 'id' must be an integer.")
        elif 'rt' in spec:
            if type(spec['rt']) != type(''):
                raise NipapValueError("VRF specification key 'rt' must be a string.")
        elif 'name' in spec:
            if type(spec['name']) != type(''):
                raise NipapValueError("VRF specification key 'name' must be a string.")
        if len(spec) > 1:
            raise NipapExtraneousInputError("VRF specification contains too many keys, specify VRF id, vrf or name.")

        where, params = self._sql_expand_where(spec, 'spec_')

        return where, params



    def _expand_vrf_query(self, query, table_name = None):
        """ Expand VRF query dict into a WHERE-clause.

            If you need to prefix each column reference with a table
            name, that can be supplied via the table_name argument.
        """

        where = str()
        opt = list()

        # handle table name, can be None
        if table_name is None:
            col_prefix = ""
        else:
            col_prefix = table_name + "."

        if type(query['val1']) == dict and type(query['val2']) == dict:
            # Sub expression, recurse! This is used for boolean operators: AND OR
            # add parantheses

            sub_where1, opt1 = self._expand_vrf_query(query['val1'], table_name)
            sub_where2, opt2 = self._expand_vrf_query(query['val2'], table_name)
            try:
                where += str(" (%s %s %s) " % (sub_where1, _operation_map[query['operator']], sub_where2) )
            except KeyError:
                raise NipapNoSuchOperatorError("No such operator %s" % str(query['operator']))

            opt += opt1
            opt += opt2

        else:

            # TODO: raise exception if someone passes one dict and one "something else"?

            # val1 is variable, val2 is string.
            vrf_attr = dict()
            vrf_attr['id'] = 'id'
            vrf_attr['rt'] = 'rt'
            vrf_attr['name'] = 'name'
            vrf_attr['description'] = 'description'
            vrf_attr['tags'] = 'tags'

            if query['val1'] not in vrf_attr:
                raise NipapInputError('Search variable \'%s\' unknown' % str(query['val1']))

            # workaround for handling equal matches of NULL-values
            if query['operator'] == 'equals' and query['val2'] is None:
                query['operator'] = 'is'
            elif query['operator'] == 'not_equals' and query['val2'] is None:
                query['operator'] = 'is_not'

            # build where clause
            if query['operator'] not in _operation_map:
                raise NipapNoSuchOperatorError("No such operator %s" % query['operator'])

            where = str(" %s%s %s %%s " %
                ( col_prefix, vrf_attr[query['val1']],
                _operation_map[query['operator']] )
            )

            opt.append(query['val2'])

        return where, opt



    @requires_rw
    def add_vrf(self, auth, attr):
        """ Add a new VRF.

            * `auth` [BaseAuth]
                AAA options.
            * `attr` [vrf_attr]
                The news VRF's attributes.

            Add a VRF based on the values stored in the `attr` dict.

            Returns a dict describing the VRF which was added.
        """

        self._logger.debug("add_vrf called; attr: %s" % str(attr))

        # sanity check - do we have all attributes?
        req_attr = [ 'rt', 'name' ]
        self._check_attr(attr, req_attr, req_attr + [ 'description', 'tags',
            'avps' ])

        insert, params = self._sql_expand_insert(attr)
        sql = "INSERT INTO ip_net_vrf " + insert

        self._execute(sql, params)
        vrf_id = self._lastrowid()
        vrf = self.list_vrf(auth, { 'id': vrf_id })[0]

        # write to audit table
        self.audit_log(auth, 'add', vrf=vrf,
                       message='Added VRF {rt} with attr: {attr}'
                       .format(rt=vrf['rt'], attr=str(vrf)))

        return vrf

    @requires_rw
    def remove_vrf(self, auth, spec):
        """ Remove a VRF.

            * `auth` [BaseAuth]
                AAA options.
            * `spec` [vrf_spec]
                A VRF specification.

            Remove VRF matching the `spec` argument.
        """

        self._logger.debug("remove_vrf called; spec: %s" % str(spec))

        # get list of VRFs to remove before removing them
        vrfs = self.list_vrf(auth, spec)

        # remove prefixes in VRFs
        for vrf in vrfs:
            v4spec = {
                'prefix': '0.0.0.0/0',
                'vrf_id': vrf['id']
            }
            v6spec = {
                'prefix': '::/0',
                'vrf_id': vrf['id']
            }
            self.remove_prefix(auth, spec = v4spec, recursive = True)
            self.remove_prefix(auth, spec = v6spec, recursive = True)

        where, params = self._expand_vrf_spec(spec)
        sql = "DELETE FROM ip_net_vrf WHERE %s" % where
        self._execute(sql, params)
        self.audit_log(auth, 'remove', vrf=vrf,
                       message='Removed vrf {0}'.format(vrf['rt']))

    def list_vrf(self, auth, spec=None):
        """ Return a list of VRFs matching `spec`.

            * `auth` [BaseAuth]
                AAA options.
            * `spec` [vrf_spec]
                A VRF specification. If omitted, all VRFs are returned.

            Returns a list of dicts.
        """

        if spec is None:
            spec = {}

        self._logger.debug("list_vrf called; spec: %s" % str(spec))

        sql = "SELECT * FROM ip_net_vrf"

        params = list()
        # no spec lists all VRFs
        if spec is not None and not {}:
            where, params = self._expand_vrf_spec(spec)
        if len(params) > 0:
            sql += " WHERE " + where

        sql += " ORDER BY vrf_rt_order(rt) NULLS FIRST"

        self._execute(sql, params)

        res = list()
        for row in self._curs_pg:
            res.append(dict(row))

        return res



    def _get_vrf(self, auth, spec, prefix = 'vrf_'):
        """ Get a VRF based on prefix spec

            Shorthand function to reduce code in the functions below, since
            more or less all of them needs to perform the actions that are
            specified here.

            The major difference to :func:`list_vrf` is that we always return
            results - empty results if no VRF is specified in prefix spec.
        """

        # find VRF from attributes vrf, vrf_id or vrf_name
        vrf = []
        if prefix + 'id' in spec:
            # if None, mangle it to being 0, ie our default VRF
            if spec[prefix + 'id'] is None:
                spec[prefix + 'id'] = 0
            vrf = self.list_vrf(auth, { 'id': spec[prefix + 'id'] })
        elif prefix + 'rt' in spec:
            vrf = self.list_vrf(auth, { 'rt': spec[prefix + 'rt'] })
        elif prefix + 'name' in spec:
            vrf = self.list_vrf(auth, { 'name': spec[prefix + 'name'] })
        else:
            # no VRF specified - return VRF "default"
            vrf = self.list_vrf(auth, { 'id': 0 })

        if len(vrf) > 0:
            return vrf[0]

        raise NipapNonExistentError('No matching VRF found.')




    @requires_rw
    def edit_vrf(self, auth, spec, attr):
        """ Update VRFs matching `spec` with attributes `attr`.

            * `auth` [BaseAuth]
                AAA options.
            * `spec` [vrf_spec]
                Attibutes specifying what VRF to edit.
            * `attr` [vrf_attr]
                Dict specifying fields to be updated and their new values.
        """

        self._logger.debug("edit_vrf called; spec: %s attr: %s" %
                (str(spec), str(attr)))

        # sanity check - do we have all attributes?
        req_attr = [ ]
        allowed_attr = [ 'rt', 'name', 'description', 'tags', 'avps' ]
        self._check_attr(attr, req_attr, allowed_attr)

        # get list of VRFs which will be changed before changing them
        vrfs = self.list_vrf(auth, spec)

        where, params1 = self._expand_vrf_spec(spec)
        update, params2 = self._sql_expand_update(attr)
        params = dict(params2.items() + params1.items())

        if len(attr) == 0:
            raise NipapInputError("'attr' must not be empty.")

        sql = "UPDATE ip_net_vrf SET " + update
        sql += " WHERE " + where
        sql += " RETURNING id"

        self._execute(sql, params)
        updated_vrfs = self._get_updated_rows(auth, self.search_vrf)

        # write to audit table
        for v in vrfs:
            self.audit_log(auth, 'edit', vrf=v,
                           message='Edited VRF {vrf} attr: {attr}'
                           .format(vrf=v['rt'], attr=str(attr)))

        return updated_vrfs

    def search_vrf(self, auth, query, search_options=None):
        """ Search VRF list for VRFs matching `query`.

            * `auth` [BaseAuth]
                AAA options.
            * `query` [dict_to_sql]
                How the search should be performed.
            * `search_options` [options_dict]
                Search options, see below.

            Returns a list of dicts.

            The `query` argument passed to this function is designed to be
            able to specify how quite advanced search operations should be
            performed in a generic format. It is internally expanded to a SQL
            WHERE-clause.

            The `query` is a dict with three elements, where one specifies the
            operation to perform and the two other specifies its arguments. The
            arguments can themselves be `query` dicts, to build more complex
            queries.

            The :attr:`operator` key specifies what operator should be used for the
            comparison. Currently the following operators are supported:

            * :data:`and` - Logical AND
            * :data:`or` - Logical OR
            * :data:`equals` - Equality; =
            * :data:`not_equals` - Inequality; !=
            * :data:`like` - SQL LIKE
            * :data:`regex_match` - Regular expression match
            * :data:`regex_not_match` - Regular expression not match

            The :attr:`val1` and :attr:`val2` keys specifies the values which are subjected
            to the comparison. :attr:`val1` can be either any prefix attribute or an
            entire query dict. :attr:`val2` can be either the value you want to
            compare the prefix attribute to, or an entire `query` dict.

            Example 1 - Find the VRF whose VRF match '65000:123'::

                query = {
                    'operator': 'equals',
                    'val1': 'vrf',
                    'val2': '65000:123'
                }

            This will be expanded to the pseudo-SQL query::

                SELECT * FROM vrf WHERE vrf = '65000:123'

            Example 2 - Find vrf whose name or description regex matches 'test'::

                query = {
                    'operator': 'or',
                    'val1': {
                        'operator': 'regex_match',
                        'val1': 'name',
                        'val2': 'test'
                    },
                    'val2': {
                        'operator': 'regex_match',
                        'val1': 'description',
                        'val2': 'test'
                    }
                }

            This will be expanded to the pseudo-SQL query::

                SELECT * FROM vrf WHERE name ~* 'test' OR description ~* 'test'

            The search options can also be used to limit the number of rows
            returned or set an offset for the result.

            The following options are available:
                * :attr:`max_result` - The maximum number of prefixes to return (default :data:`50`).
                * :attr:`offset` - Offset the result list this many prefixes (default :data:`0`).
        """

        if search_options is None:
            search_options = {}

        #
        # sanitize search options and set default if option missing
        #

        # max_result
        if 'max_result' not in search_options:
            search_options['max_result'] = 50
        else:
            try:
                search_options['max_result'] = int(search_options['max_result'])
            except (ValueError, TypeError):
                raise NipapValueError('Invalid value for option' +
                    ''' 'max_result'. Only integer values allowed.''')

        # offset
        if 'offset' not in search_options:
            search_options['offset'] = 0
        else:
            try:
                search_options['offset'] = int(search_options['offset'])
            except (ValueError, TypeError):
                raise NipapValueError('Invalid value for option' +
                    ''' 'offset'. Only integer values allowed.''')

        self._logger.debug('search_vrf called; query: %s search_options: %s' % (str(query), str(search_options)))

        opt = None
        sql = """ SELECT * FROM ip_net_vrf"""

        # add where clause if we have any search terms
        if query != {}:

            where, opt = self._expand_vrf_query(query)
            sql += " WHERE " + where

        sql += " ORDER BY vrf_rt_order(rt) NULLS FIRST LIMIT " + str(search_options['max_result']) + " OFFSET " + str(search_options['offset'])
        self._execute(sql, opt)

        result = list()
        for row in self._curs_pg:
            result.append(dict(row))

        return { 'search_options': search_options, 'result': result }



    def smart_search_vrf(self, auth, query_str, search_options=None, extra_query=None):
        """ Perform a smart search on VRF list.

            * `auth` [BaseAuth]
                AAA options.
            * `query_str` [string]
                Search string
            * `search_options` [options_dict]
                Search options. See :func:`search_vrf`.
            * `extra_query` [dict_to_sql]
                Extra search terms, will be AND:ed together with what is
                extracted from the query string.

            Return a dict with three elements:
                * :attr:`interpretation` - How the query string was interpreted.
                * :attr:`search_options` - Various search_options.
                * :attr:`result` - The search result.

                The :attr:`interpretation` is given as a list of dicts, each
                explaining how a part of the search key was interpreted (ie. what
                VRF attribute the search operation was performed on).

                The :attr:`result` is a list of dicts containing the search result.

            The smart search function tries to convert the query from a text
            string to a `query` dict which is passed to the
            :func:`search_vrf` function.  If multiple search keys are
            detected, they are combined with a logical AND.

            It will basically just take each search term and try to match it
            against the name or description column with regex match or the VRF
            column with an exact match.

            See the :func:`search_vrf` function for an explanation of the
            `search_options` argument.
        """

        if search_options is None:
            search_options = {}

        self._logger.debug("smart_search_vrf query string: %s" % query_str)

        if query_str is None:
            raise NipapValueError("'query_string' must not be None")

        # find query parts
        query_str_parts = []
        try:
            for part in shlex.split(query_str):
                query_str_parts.append({ 'string': part })
        except:
            return {
                'interpretation': [
                    {
                        'string': query_str,
                        'interpretation': 'unclosed quote',
                        'attribute': 'text'
                    }
                ],
                'search_options': search_options,
                'result': []
            }

        # Handle empty search.
        # We need something to iterate over, but shlex.split() returns
        # zero-element list for an empty string, so we have to append one
        # manually
        if len(query_str_parts) == 0:
            query_str_parts.append({ 'string': '' })

        # go through parts and add to query_parts list
        query_parts = list()
        for query_str_part in query_str_parts:

            # tags
            if re.match('#', query_str_part['string']):
                self._logger.debug("Query part '" + query_str_part['string'] + "' interpreted as tag")
                query_str_part['interpretation'] = '(inherited) tag'
                query_str_part['attribute'] = 'tag'

                query_str_part['operator'] = 'equals_any'
                query_parts.append({
                    'operator': 'or',
                    'val1': {
                        'operator': 'equals_any',
                        'val1': 'tags',
                        'val2': query_str_part['string'][1:]
                    },
                    'val2': {
                        'operator': 'equals_any',
                        'val1': 'inherited_tags',
                        'val2': query_str_part['string'][1:]
                    }
                })

            else:
                self._logger.debug("Query part '" + query_str_part['string'] + "' interpreted as text")
                query_str_part['interpretation'] = 'text'
                query_str_part['operator'] = 'regex'
                query_str_part['attribute'] = 'vrf or name or description'
                query_parts.append({
                    'operator': 'or',
                    'val1': {
                        'operator': 'or',
                        'val1': {
                            'operator': 'regex_match',
                            'val1': 'name',
                            'val2': query_str_part['string']
                        },
                        'val2': {
                            'operator': 'regex_match',
                            'val1': 'description',
                            'val2': query_str_part['string']
                        }
                    },
                    'val2': {
                        'operator': 'regex_match',
                        'val1': 'rt',
                        'val2': query_str_part['string']
                    }
                })

        # Sum all query parts to one query
        query = {}
        if len(query_parts) > 0:
            query = query_parts[0]

        if len(query_parts) > 1:
            for query_part in query_parts[1:]:
                query = {
                    'operator': 'and',
                    'val1': query_part,
                    'val2': query
                }

        if extra_query is not None:
            query = {
                'operator': 'and',
                'val1': query,
                'val2': extra_query
            }

        self._logger.debug("smart_search_vrf; query expanded to: %s" % str(query))

        search_result = self.search_vrf(auth, query, search_options)
        search_result['interpretation'] = query_str_parts

        return search_result



    #
    # Pool functions
    #
    def _expand_pool_spec(self, spec):
        """ Expand pool specification to sql.
        """

        if type(spec) is not dict:
            raise NipapInputError("pool specification must be a dict")

        allowed_values = ['id', 'name' ]
        for a in spec:
            if a not in allowed_values:
                raise NipapExtraneousInputError("extraneous specification key %s" % a)

        if 'id' in spec:
            if type(spec['id']) not in (long, int):
                raise NipapValueError("pool specification key 'id' must be an integer")
            if spec != { 'id': spec['id'] }:
                raise NipapExtraneousInputError("pool specification with 'id' should not contain anything else")
        elif 'name' in spec:
            if type(spec['name']) != type(''):
                raise NipapValueError("pool specification key 'name' must be a string")
            if 'id' in spec:
                raise NipapExtraneousInputError("pool specification contain both 'id' and 'name', specify pool id or name")

        where, params = self._sql_expand_where(spec, 'spec_', 'po.')

        return where, params



    def _expand_pool_query(self, query, table_name = None):
        """ Expand pool query dict into a WHERE-clause.

            If you need to prefix each column reference with a table
            name, that can be supplied via the table_name argument.
        """

        where = str()
        opt = list()

        # handle table name, can be None
        if table_name is None:
            col_prefix = ""
        else:
            col_prefix = table_name + "."


        if type(query['val1']) == dict and type(query['val2']) == dict:
            # Sub expression, recurse! This is used for boolean operators: AND OR
            # add parantheses

            sub_where1, opt1 = self._expand_pool_query(query['val1'], table_name)
            sub_where2, opt2 = self._expand_pool_query(query['val2'], table_name)
            try:
                where += str(" (%s %s %s) " % (sub_where1, _operation_map[query['operator']], sub_where2) )
            except KeyError:
                raise NipapNoSuchOperatorError("No such operator %s" % str(query['operator']))

            opt += opt1
            opt += opt2

        else:

            # TODO: raise exception if someone passes one dict and one "something else"?

            # val1 is variable, val2 is string.
            pool_attr = dict()
            pool_attr['id'] = 'po.id'
            pool_attr['name'] = 'po.name'
            pool_attr['description'] = 'po.description'
            pool_attr['default_type'] = 'po.default_type'
            pool_attr['vrf_rt'] = 'vrf.rt'
            pool_attr['tags'] = 'po.tags'

            if query['val1'] not in pool_attr:
                raise NipapInputError('Search variable \'%s\' unknown' % str(query['val1']))

            # workaround for handling equal matches of NULL-values
            if query['operator'] == 'equals' and query['val2'] is None:
                query['operator'] = 'is'
            elif query['operator'] == 'not_equals' and query['val2'] is None:
                query['operator'] = 'is_not'

            # build where clause
            if query['operator'] not in _operation_map:
                raise NipapNoSuchOperatorError("No such operator %s" % query['operator'])

            where = str(" %s%s %s %%s " %
                ( col_prefix, pool_attr[query['val1']],
                _operation_map[query['operator']] )
            )

            opt.append(query['val2'])

        return where, opt



    @requires_rw
    def add_pool(self, auth, attr):
        """ Create a pool according to `attr`.

            * `auth` [BaseAuth]
                AAA options.
            * `attr` [pool_attr]
                A dict containing the attributes the new pool should have.

            Returns a dict describing the pool which was added.
        """

        self._logger.debug("add_pool called; attrs: %s" % str(attr))

        # sanity check - do we have all attributes?
        req_attr = ['name', 'description', 'default_type']
        self._check_pool_attr(attr, req_attr)

        insert, params = self._sql_expand_insert(attr)
        sql = "INSERT INTO ip_net_pool " + insert

        self._execute(sql, params)
        pool_id = self._lastrowid()
        pool = self.list_pool(auth, { 'id': pool_id })[0]

        self.audit_log(auth, 'add', pool=pool,
                       message='Added pool {pool} with attr: {attr}'
                       .format(pool=pool['name'], attr=str(attr)))

        return pool

    @requires_rw
    def remove_pool(self, auth, spec):
        """ Remove a pool.

            * `auth` [BaseAuth]
                AAA options.
            * `spec` [pool_spec]
                Specifies what pool(s) to remove.
        """

        self._logger.debug("remove_pool called; spec: %s" % str(spec))

        # fetch list of pools to remove before they are removed
        pools = self.list_pool(auth, spec)

        where, params = self._expand_pool_spec(spec)
        sql = "DELETE FROM ip_net_pool AS po WHERE %s" % where
        self._execute(sql, params)

        # write to audit table
        for p in pools:
            self.audit_log(auth, 'delete', pool=p,
                           message='Removed pool {0}'.format(p['name']))

    def list_pool(self, auth, spec=None):
        """ Return a list of pools.

            * `auth` [BaseAuth]
                AAA options.
            * `spec` [pool_spec]
                Specifies what pool(s) to list. Of omitted, all will be listed.

            Returns a list of dicts.
        """

        if spec is None:
            spec = {}

        self._logger.debug("list_pool called; spec: %s" % str(spec))

        sql = """SELECT DISTINCT (po.id),
                        po.id,
                        po.name,
                        po.description,
                        po.default_type,
                        po.ipv4_default_prefix_length,
                        po.ipv6_default_prefix_length,
                        po.member_prefixes_v4,
                        po.member_prefixes_v6,
                        po.used_prefixes_v4,
                        po.used_prefixes_v6,
                        po.free_prefixes_v4,
                        po.free_prefixes_v6,
                        po.total_prefixes_v4,
                        po.total_prefixes_v6,
                        po.total_addresses_v4,
                        po.total_addresses_v6,
                        po.used_addresses_v4,
                        po.used_addresses_v6,
                        po.free_addresses_v4,
                        po.free_addresses_v6,
                        po.tags,
                        po.avps,
                        vrf.id AS vrf_id,
                        vrf.rt AS vrf_rt,
                        vrf.name AS vrf_name,
                        (SELECT array_agg(prefix::text) FROM (SELECT prefix FROM ip_net_plan WHERE pool_id=po.id ORDER BY prefix) AS a) AS prefixes
                FROM ip_net_pool AS po
                LEFT OUTER JOIN ip_net_plan AS inp ON (inp.pool_id = po.id)
                LEFT OUTER JOIN ip_net_vrf AS vrf ON (vrf.id = inp.vrf_id)"""
        params = list()

        # expand spec
        where, params = self._expand_pool_spec(spec)
        if len(where) > 0:
            sql += " WHERE " + where

        sql += " ORDER BY name"

        self._execute(sql, params)

        res = list()
        for row in self._curs_pg:
            p = dict(row)

            # Make sure that prefixes is a list, even if there are no prefixes
            if p['prefixes'] == None:
                p['prefixes'] = []
            res.append(p)

        return res


    def _check_pool_attr(self, attr, req_attr=None):
        """ Check pool attributes.
        """

        if req_attr is None:
            req_attr = []

        # check attribute names
        allowed_attr = [
                'name',
                'default_type',
                'description',
                'ipv4_default_prefix_length',
                'ipv6_default_prefix_length',
                'tags',
                'avps'
                ]
        self._check_attr(attr, req_attr, allowed_attr)

        # validate IPv4 prefix length
        if attr.get('ipv4_default_prefix_length') is not None:
            try:
                attr['ipv4_default_prefix_length'] = \
                    int(attr['ipv4_default_prefix_length'])

                if (attr['ipv4_default_prefix_length'] > 32 or
                    attr['ipv4_default_prefix_length'] < 1):
                    raise ValueError()
            except ValueError:
                raise NipapValueError('Default IPv4 prefix length must be an integer between 1 and 32.')

        # validate IPv6 prefix length
        if attr.get('ipv6_default_prefix_length'):
            try:
                attr['ipv6_default_prefix_length'] = \
                    int(attr['ipv6_default_prefix_length'])

                if (attr['ipv6_default_prefix_length'] > 128 or
                    attr['ipv6_default_prefix_length'] < 1):
                    raise ValueError()
            except ValueError:
                raise NipapValueError('Default IPv6 prefix length must be an integer between 1 and 128.')



    def _get_pool(self, auth, spec):
        """ Get a pool.

            Shorthand function to reduce code in the functions below, since
            more or less all of them needs to perform the actions that are
            specified here.

            The major difference to :func:`list_pool` is that an exception
            is raised if no pool matching the spec is found.
        """

        pool = self.list_pool(auth, spec)
        if len(pool) == 0:
            raise NipapInputError("non-existing pool specified")
        return pool[0]



    @requires_rw
    def edit_pool(self, auth, spec, attr):
        """ Update pool given by `spec` with attributes `attr`.

            * `auth` [BaseAuth]
                AAA options.
            * `spec` [pool_spec]
                Specifies what pool to edit.
            * `attr` [pool_attr]
                Attributes to update and their new values.
        """

        self._logger.debug("edit_pool called; spec: %s attr: %s" %
                (str(spec), str(attr)))

        if ('id' not in spec and 'name' not in spec) or ( 'id' in spec and 'name' in spec ):
            raise NipapMissingInputError('''pool spec must contain either 'id' or 'name' ''')

        self._check_pool_attr(attr)

        where, params1 = self._expand_pool_spec(spec)
        update, params2 = self._sql_expand_update(attr)
        params = dict(params2.items() + params1.items())

        pools = self.list_pool(auth, spec)

        sql = "UPDATE ip_net_pool SET " + update
        sql += " FROM ip_net_pool AS po WHERE ip_net_pool.id = po.id AND " + where
        sql += " RETURNING po.id AS id"

        self._execute(sql, params)

        updated_pools = self._get_updated_rows(auth, self.search_pool)

        # write to audit table
        for p in pools:
            self.audit_log(auth, 'edit', pool=p,
                           message='Edited pool {pool} attr: {attr}'
                           .format(pool=p['name'], attr=str(attr)))
        return updated_pools

    def search_pool(self, auth, query, search_options=None):
        """ Search pool list for pools matching `query`.

            * `auth` [BaseAuth]
                AAA options.
            * `query` [dict_to_sql]
                How the search should be performed.
            * `search_options` [options_dict]
                Search options, see below.

            Returns a list of dicts.

            The `query` argument passed to this function is designed to be
            able to specify how quite advanced search operations should be
            performed in a generic format. It is internally expanded to a SQL
            WHERE-clause.

            The `query` is a dict with three elements, where one specifies the
            operation to perform and the two other specifies its arguments. The
            arguments can themselves be `query` dicts, to build more complex
            queries.

            The :attr:`operator` key specifies what operator should be used for the
            comparison. Currently the following operators are supported:

            * :data:`and` - Logical AND
            * :data:`or` - Logical OR
            * :data:`equals` - Equality; =
            * :data:`not_equals` - Inequality; !=
            * :data:`like` - SQL LIKE
            * :data:`regex_match` - Regular expression match
            * :data:`regex_not_match` - Regular expression not match

            The :attr:`val1` and :attr:`val2` keys specifies the values which are subjected
            to the comparison. :attr:`val1` can be either any pool attribute or an
            entire query dict. :attr:`val2` can be either the value you want to
            compare the pool attribute to, or an entire `query` dict.

            Example 1 - Find the pool whose name match 'test'::

                query = {
                    'operator': 'equals',
                    'val1': 'name',
                    'val2': 'test'
                }

            This will be expanded to the pseudo-SQL query::

                SELECT * FROM pool WHERE name = 'test'

            Example 2 - Find pools whose name or description regex matches 'test'::

                query = {
                    'operator': 'or',
                    'val1': {
                        'operator': 'regex_match',
                        'val1': 'name',
                        'val2': 'test'
                    },
                    'val2': {
                        'operator': 'regex_match',
                        'val1': 'description',
                        'val2': 'test'
                    }
                }

            This will be expanded to the pseudo-SQL query::

                SELECT * FROM pool WHERE name ~* 'test' OR description ~* 'test'

            The search options can also be used to limit the number of rows
            returned or set an offset for the result.

            The following options are available:
                * :attr:`max_result` - The maximum number of pools to return (default :data:`50`).
                * :attr:`offset` - Offset the result list this many pools (default :data:`0`).
        """

        if search_options is None:
            search_options = {}

        #
        # sanitize search options and set default if option missing
        #

        # max_result
        if 'max_result' not in search_options:
            search_options['max_result'] = 50
        else:
            try:
                search_options['max_result'] = int(search_options['max_result'])
            except (ValueError, TypeError):
                raise NipapValueError('Invalid value for option' +
                    ''' 'max_result'. Only integer values allowed.''')

        # offset
        if 'offset' not in search_options:
            search_options['offset'] = 0
        else:
            try:
                search_options['offset'] = int(search_options['offset'])
            except (ValueError, TypeError):
                raise NipapValueError('Invalid value for option' +
                    ''' 'offset'. Only integer values allowed.''')

        self._logger.debug('search_pool search_options: %s' % str(search_options))

        where, opt = self._expand_pool_query(query)
        sql = """SELECT DISTINCT (po.id),
                        po.id,
                        po.name,
                        po.description,
                        po.default_type,
                        po.ipv4_default_prefix_length,
                        po.ipv6_default_prefix_length,
                        po.member_prefixes_v4,
                        po.member_prefixes_v6,
                        po.used_prefixes_v4,
                        po.used_prefixes_v6,
                        po.free_prefixes_v4,
                        po.free_prefixes_v6,
                        po.total_prefixes_v4,
                        po.total_prefixes_v6,
                        po.total_addresses_v4,
                        po.total_addresses_v6,
                        po.used_addresses_v4,
                        po.used_addresses_v6,
                        po.free_addresses_v4,
                        po.free_addresses_v6,
                        po.tags,
                        po.avps,
                        vrf.id AS vrf_id,
                        vrf.rt AS vrf_rt,
                        vrf.name AS vrf_name,
                        (SELECT array_agg(prefix::text) FROM (SELECT prefix FROM ip_net_plan WHERE pool_id=po.id ORDER BY prefix) AS a) AS prefixes
                FROM ip_net_pool AS po
                LEFT OUTER JOIN ip_net_plan AS inp ON (inp.pool_id = po.id)
                LEFT OUTER JOIN ip_net_vrf AS vrf ON (vrf.id = inp.vrf_id)
                WHERE """ + where + """ ORDER BY po.name
                LIMIT """ + str(search_options['max_result']) + """ OFFSET """ + str(search_options['offset'])

        self._execute(sql, opt)

        result = list()
        for row in self._curs_pg:
            result.append(dict(row))

        return { 'search_options': search_options, 'result': result }



    def smart_search_pool(self, auth, query_str, search_options=None, extra_query=None):
        """ Perform a smart search on pool list.

            * `auth` [BaseAuth]
                AAA options.
            * `query_str` [string]
                Search string
            * `search_options` [options_dict]
                Search options. See :func:`search_pool`.
            * `extra_query` [dict_to_sql]
                Extra search terms, will be AND:ed together with what is
                extracted from the query string.

            Return a dict with three elements:
                * :attr:`interpretation` - How the query string was interpreted.
                * :attr:`search_options` - Various search_options.
                * :attr:`result` - The search result.

                The :attr:`interpretation` is given as a list of dicts, each
                explaining how a part of the search key was interpreted (ie. what
                pool attribute the search operation was performed on).

                The :attr:`result` is a list of dicts containing the search result.

            The smart search function tries to convert the query from a text
            string to a `query` dict which is passed to the
            :func:`search_pool` function.  If multiple search keys are
            detected, they are combined with a logical AND.

            It will basically just take each search term and try to match it
            against the name or description column with regex match.

            See the :func:`search_pool` function for an explanation of the
            `search_options` argument.
        """

        if search_options is None:
            search_options = {}

        self._logger.debug("smart_search_pool query string: %s" % query_str)

        # find query parts
        try:
            query_str_parts = self._get_query_parts(query_str)
        except NipapValueError:
            return {
                'interpretation': [
                    {
                        'string': query_str,
                        'interpretation': 'unclosed quote',
                        'attribute': 'text'
                    }
                ],
                'search_options': search_options,
                'result': []
            }

        # go through parts and add to query_parts list
        query_parts = list()
        for query_str_part in query_str_parts:

            # tags
            if re.match('#', query_str_part['string']):
                self._logger.debug("Query part '" + query_str_part['string'] + "' interpreted as tag")
                query_str_part['interpretation'] = '(inherited) tag'
                query_str_part['attribute'] = 'tag'

                query_str_part['operator'] = 'equals_any'
                query_parts.append({
                    'operator': 'or',
                    'val1': {
                        'operator': 'equals_any',
                        'val1': 'tags',
                        'val2': query_str_part['string'][1:]
                    },
                    'val2': {
                        'operator': 'equals_any',
                        'val1': 'inherited_tags',
                        'val2': query_str_part['string'][1:]
                    }
                })

            else:
                self._logger.debug("Query part '" + query_str_part['string'] + "' interpreted as text")
                query_str_part['interpretation'] = 'text'
                query_str_part['operator'] = 'regex'
                query_str_part['attribute'] = 'name or description'
                query_parts.append({
                    'operator': 'or',
                    'val1': {
                        'operator': 'regex_match',
                        'val1': 'name',
                        'val2': query_str_part['string']
                    },
                    'val2': {
                        'operator': 'regex_match',
                        'val1': 'description',
                        'val2': query_str_part['string']
                    }
                })

        # Sum all query parts to one query
        query = {}
        if len(query_parts) > 0:
            query = query_parts[0]

        if len(query_parts) > 1:
            for query_part in query_parts[1:]:
                query = {
                    'operator': 'and',
                    'val1': query_part,
                    'val2': query
                }

        if extra_query is not None:
            query = {
                'operator': 'and',
                'val1': query,
                'val2': extra_query
            }

        self._logger.debug("Expanded to: %s" % str(query))

        search_result = self.search_pool(auth, query, search_options)
        search_result['interpretation'] = query_str_parts

        return search_result



    #
    # PREFIX FUNCTIONS
    #
    def _expand_prefix_spec(self, spec, prefix = ''):
        """ Expand prefix specification to SQL.
        """

        # sanity checks
        if type(spec) is not dict:
            raise NipapInputError('invalid prefix specification')

        allowed_keys = [ 'id', 'family', 'type', 'pool_id', 'pool_name',
                'prefix', 'monitor', 'external_key', 'vrf_id',
                'vrf_rt', 'vrf_name' ]
        for key in spec.keys():
            if key not in allowed_keys:
                raise NipapExtraneousInputError("Key '" + key + "' not allowed in prefix spec.")

        where = ""
        params = {}

        # if we have id, no other input is needed
        if 'id' in spec:
            if spec != {'id': spec['id']}:
                raise NipapExtraneousInputError("If 'id' specified, no other keys are allowed.")

        family = None
        if 'family' in spec:
            family = spec['family']
            del(spec['family'])

        # rename prefix columns
        spec2 = {}
        for k in spec:
            spec2[prefix + k] = spec[k]
        spec = spec2

        # handle keys which refer to external keys
        if prefix + 'vrf_id' in spec:
            # "translate" vrf id None to id = 0
            if spec[prefix + 'vrf_id'] is None:
                spec[prefix + 'vrf_id'] = 0

        if prefix + 'vrf_name' in spec:
            spec['vrf.name'] = spec[prefix + 'vrf_name']
            del(spec[prefix + 'vrf_name'])

        if prefix + 'vrf_rt' in spec:
            spec['vrf.rt'] = spec[prefix + 'vrf_rt']
            del(spec[prefix + 'vrf_rt'])

        if prefix + 'pool_name' in spec:
            spec['pool.name'] = spec[prefix + 'pool_name']
            del(spec[prefix + 'pool_name'])

        where, params = self._sql_expand_where(spec)

        # prefix family needs to be handled separately as it's not stored
        # explicitly in the database
        if family:
            params['family'] = family
            if len(params) == 0:
                where = "family(" + prefix + "prefix) = %(family)s"
            else:
                where += " AND family(" + prefix + "prefix) = %(family)s"

        self._logger.debug("_expand_prefix_spec; where: %s params: %s" % (where, str(params)))
        return where, params



    def _expand_prefix_query(self, query, table_name = None):
        """ Expand prefix query dict into a WHERE-clause.

            If you need to prefix each column reference with a table
            name, that can be supplied via the table_name argument.
        """

        where = str()
        opt = list()

        # handle table name, can be None
        if table_name is None:
            col_prefix = ""
        else:
            col_prefix = table_name + "."

        if 'val1' not in query:
            raise NipapMissingInputError("'val1' must be specified")
        if 'val2' not in query:
            raise NipapMissingInputError("'val2' must be specified")

        if type(query['val1']) == dict and type(query['val2']) == dict:
            # Sub expression, recurse! This is used for boolean operators: AND OR
            # add parantheses

            sub_where1, opt1 = self._expand_prefix_query(query['val1'], table_name)
            sub_where2, opt2 = self._expand_prefix_query(query['val2'], table_name)
            try:
                where += str(" (%s %s %s) " % (sub_where1, _operation_map[query['operator']], sub_where2) )
            except KeyError:
                raise NipapNoSuchOperatorError("No such operator %s" % str(query['operator']))

            opt += opt1
            opt += opt2

        else:

            # TODO: raise exception if someone passes one dict and one "something else"?

            # val1 is variable, val2 is string.
            prefix_attr = dict()
            prefix_attr['id'] = 'inp.id'
            prefix_attr['prefix'] = 'inp.prefix'
            prefix_attr['description'] = 'inp.description'
            prefix_attr['pool_id'] = 'pool.id'
            prefix_attr['pool_name'] = 'pool.name'
            prefix_attr['family'] = 'family(inp.prefix)'
            prefix_attr['comment'] = 'inp.comment'
            prefix_attr['type'] = 'inp.type'
            prefix_attr['inherited_tags'] = 'inp.inherited_tags'
            prefix_attr['tags'] = 'inp.tags'
            prefix_attr['node'] = 'inp.node'
            prefix_attr['country'] = 'inp.country'
            prefix_attr['order_id'] = 'inp.order_id'
            prefix_attr['customer_id'] = 'inp.customer_id'
            prefix_attr['vrf_id'] = 'inp.vrf_id'
            prefix_attr['vrf_rt'] = 'vrf.rt'
            prefix_attr['vrf_name'] = 'vrf.name'
            prefix_attr['external_key'] = 'inp.external_key'
            prefix_attr['authoritative_source'] = 'inp.authoritative_source'
            prefix_attr['alarm_priority'] = 'inp.alarm_priority'
            prefix_attr['monitor'] = 'inp.monitor'
            prefix_attr['vlan'] = 'inp.vlan'
            prefix_attr['indent'] = 'inp.indent'
            prefix_attr['added'] = 'inp.added'
            prefix_attr['last_modified'] = 'inp.last_modified'
            prefix_attr['total_addresses'] = 'inp.total_addresses'
            prefix_attr['used_addresses'] = 'inp.used_addresses'
            prefix_attr['free_addresses'] = 'inp.free_addresses'
            prefix_attr['expires'] = 'inp.expires'

            if query['val1'] not in prefix_attr:
                raise NipapInputError('Search variable \'%s\' unknown' % str(query['val1']))

            # build where clause
            if query['operator'] not in _operation_map:
                raise NipapNoSuchOperatorError("No such operator %s" % query['operator'])

            if query['val1'] == 'vrf_id' and query['val2'] == None:
                query['val2'] = 0

            # workaround for handling equal matches of NULL-values
            if query['operator'] == 'equals' and query['val2'] is None:
                query['operator'] = 'is'
            elif query['operator'] == 'not_equals' and query['val2'] is None:
                query['operator'] = 'is_not'

            if query['operator'] in (
                    'contains',
                    'contains_equals',
                    'contained_within',
                    'contained_within_equals'):

                where = " iprange(prefix) %(operator)s %%s " % {
                        'col_prefix': col_prefix,
                        'operator': _operation_map[query['operator']]
                        }

            elif query['operator'] in ('equals_any',):
                where = str(" %%s = ANY (%s%s) " %
                        ( col_prefix, prefix_attr[query['val1']])
                        )

            elif query['operator'] in (
                    'like',
                    'regex_match',
                    'regex_not_match'):
                # we COALESCE column with '' to allow for example a regexp
                # search on '.*' to match columns which are NULL in the
                # database
                where = str(" COALESCE(%s%s, '') %s %%s " %
                        ( col_prefix, prefix_attr[query['val1']],
                        _operation_map[query['operator']] )
                        )

            else:
                where = str(" %s%s %s %%s " %
                        ( col_prefix, prefix_attr[query['val1']],
                        _operation_map[query['operator']] )
                        )

            opt.append(query['val2'])

        return where, opt



    @requires_rw
    def add_prefix(self, auth, attr, args=None):
        """ Add a prefix and return its ID.

            * `auth` [BaseAuth]
                AAA options.
            * `attr` [prefix_attr]
                Prefix attributes.
            * `args` [add_prefix_args]
                Arguments explaining how the prefix should be allocated.

            Returns a dict describing the prefix which was added.

            Prefixes can be added in three ways; manually, from a pool or
            from a prefix.

            Manually
                All prefix data, including the prefix itself is specified in the
                `attr` argument. The `args` argument shall be omitted.

            From a pool
                Most prefixes are expected to be automatically assigned from a pool.
                In this case, the :attr:`prefix` key is omitted from the `attr` argument.
                Also the :attr:`type` key can be omitted and the prefix type will then be
                set to the pools default prefix type. The :func:`find_free_prefix`
                function is used to find available prefixes for this allocation
                method, see its documentation for a description of how the
                `args` argument should be formatted.

            From a prefix
                A prefix can also be selected from another prefix. Also in this case
                the :attr:`prefix` key is omitted from the `attr` argument. See the
                documentation for the :func:`find_free_prefix` for a description of how
                the `args` argument is to be formatted.
        """

        if args is None:
            args = {}

        self._logger.debug("add_prefix called; attr: %s; args: %s" % (str(attr), str(args)))

        # args defined?
        if args is None:
            args = {}

        # attr must be a dict!
        if type(attr) != dict:
            raise NipapInputError("'attr' must be a dict")

        # handle pool attributes - find correct one and remove bad pool keys
        # note how this is not related to from-pool but is merely the pool
        # attributes if this prefix is to be part of a pool
        if 'pool_id' in attr or 'pool_name' in attr:
            if 'pool_id' in attr:
                if attr['pool_id'] is None:
                    pool = {
                        'id': None,
                        'name': None
                    }
                else:
                    pool = self._get_pool(auth, { 'id': attr['pool_id'] })

            else:
                if attr['pool_name'] is None:
                    pool = {
                        'id': None,
                        'name': None
                    }
                else:
                    # resolve pool name to pool id
                    pool = self._get_pool(auth, { 'name': attr['pool_name'] })

                # and delete the pool_name attr
                del(attr['pool_name'])

            attr['pool_id'] = pool['id']

        else:
            pool = {
                'id': None,
                'name': None
            }

        attr['authoritative_source'] = auth.authoritative_source

        # sanity checks for manual prefix vs from-pool vs from-prefix
        if 'prefix' in attr:
            if 'from-pool' in args or 'from-prefix' in args:
                raise NipapExtraneousInputError("specify 'prefix' or 'from-prefix' or 'from-pool'")

        else:
            if ('from-pool' not in args and 'from-prefix' not in args) or ('from-pool' in args and 'from-prefix' in args):
                raise NipapExtraneousInputError("specify 'prefix' or 'from-prefix' or 'from-pool'")

        # VRF handling for manually specified prefix
        if 'prefix' in attr:
            # handle VRF - find the correct one and remove bad VRF keys
            vrf = self._get_vrf(auth, attr)
            if 'vrf_rt' in attr:
                del(attr['vrf_rt'])
            if 'vrf_name' in attr:
                del(attr['vrf_name'])
            attr['vrf_id'] = vrf['id']

        # VRF handling for allocation from pool or parent prefix
        if 'from-pool' in args or 'from-prefix' in args:
            # did we get a VRF from the client?
            if 'vrf_id' in attr or 'vrf_rt' in attr or 'vrf_name' in attr:
                # handle VRF - find the correct one and remove bad VRF keys
                vrf = self._get_vrf(auth, attr)
                if 'vrf_rt' in attr:
                    del(attr['vrf_rt'])
                if 'vrf_name' in attr:
                    del(attr['vrf_name'])
                attr['vrf_id'] = vrf['id']

            if 'from-pool' in args:
                from_pool = self._get_pool(auth, args['from-pool'])

                # make sure there are prefixes in pool, if any prefix is present
                # than the implied-vrf is set, otherwise the pool is empty
                if from_pool['vrf_id'] is None:
                    raise NipapInputError('No prefixes in pool')

                # set default type from pool if missing
                if 'type' not in attr:
                    attr['type'] = from_pool['default_type']

                # set implied VRF of pool if missing
                if 'vrf_id' not in attr:
                    attr['vrf_id'] = from_pool['vrf_id']

                # make sure VRF aligns with pool implied VRF
                if attr['vrf_id'] != from_pool['vrf_id']:
                    raise NipapInputError("VRF must be the same as the pools implied VRF")

                vrf = self._get_vrf(auth, attr)

            if 'from-prefix' in args:
                # handle VRF - find the correct one and remove bad VRF keys
                vrf = self._get_vrf(auth, attr)
                if 'vrf_rt' in attr:
                    del(attr['vrf_rt'])
                if 'vrf_name' in attr:
                    del(attr['vrf_name'])
                attr['vrf_id'] = vrf['id']

            # VRF fiddling
            ffp_vrf = self._get_vrf(auth, attr)

            # get a new prefix
            res = self.find_free_prefix(auth, ffp_vrf, args)
            if res != []:
                attr['prefix'] = res[0]
            else:
                # TODO: Raise other exception?
                raise NipapNonExistentError("no free prefix found")

        # do we have all attributes?
        req_attr = [ 'prefix', 'authoritative_source' ]
        allowed_attr = [ 'authoritative_source', 'prefix', 'description',
                'comment', 'pool_id', 'tags', 'node', 'type', 'country',
                'order_id', 'customer_id', 'vrf_id', 'alarm_priority',
                'monitor', 'external_key', 'vlan', 'status', 'avps', 'expires']
        self._check_attr(attr, req_attr, allowed_attr)
        if ('description' not in attr) and ('node' not in attr):
            raise NipapMissingInputError('Either description or node must be specified.')

        if 'expires' in attr:
            attr['expires'] = _parse_expires(attr['expires'])

        insert, params = self._sql_expand_insert(attr)
        sql = "INSERT INTO ip_net_plan " + insert

        self._execute(sql, params)
        prefix_id = self._lastrowid()
        prefix = self.list_prefix(auth, { 'id': prefix_id })[0]

        # write to audit table
        self.audit_log(auth, 'add', vrf=prefix, prefix=prefix,
                       message='Added prefix {0} with attr: {1}'
                               .format(prefix['prefix'], str(attr)))

        if pool['id'] is not None:
            self.audit_log(auth, 'edit', pool=pool, vrf=prefix, prefix=prefix,
                           message='Pool {pool} expanded with prefix '
                                   '{prefix} in VRF {vrf}'
                                   .format(pool=pool['name'],
                                           prefix=prefix['prefix'],
                                           vrf=str(prefix['vrf_rt'])))

        return prefix

    @requires_rw
    def edit_prefix(self, auth, spec, attr):
        """ Update prefix matching `spec` with attributes `attr`.

            * `auth` [BaseAuth]
                AAA options.
            * `spec` [prefix_spec]
                Specifies the prefix to edit.
            * `attr` [prefix_attr]
                Prefix attributes.

            Note that there are restrictions on when and how a prefix's type
            can be changed; reservations can be changed to assignments and vice
            versa, but only if they contain no child prefixes.
        """

        self._logger.debug("edit_prefix called; spec: %s attr: %s" %
                (str(spec), str(attr)))

        # Handle Pool - find correct one and remove bad pool keys
        pool = None
        if 'pool_id' in attr or 'pool_name' in attr:
            if 'pool_id' in attr:
                if attr['pool_id'] is None:
                    pool = {
                        'id': None,
                        'name': None
                    }
                else:
                    pool = self._get_pool(auth, { 'id': attr['pool_id'] })

            else:
                if attr['pool_name'] is None:
                    pool = {
                        'id': None,
                        'name': None
                    }
                else:
                    # resolve pool name to pool id
                    pool = self._get_pool(auth, { 'name': attr['pool_name'] })
                # and delete the pool_name attr
                del(attr['pool_name'])

            attr['pool_id'] = pool['id']

        else:
            pool = {
                'id': None,
                'name': None
            }

        # Handle VRF - find the correct one and remove bad VRF keys.
        vrf = self._get_vrf(auth, attr)
        if 'vrf_rt' in attr:
            del(attr['vrf_rt'])
        if 'vrf_name' in attr:
            del(attr['vrf_name'])
        attr['vrf_id'] = vrf['id']

        allowed_attr = [
            'authoritative_source', 'prefix', 'description',
            'comment', 'pool_id', 'tags', 'node', 'type', 'country',
            'order_id', 'customer_id', 'vrf_id', 'alarm_priority', 
            'monitor', 'external_key', 'vlan', 'status', 'avps', 'expires' ]

        self._check_attr(attr, [], allowed_attr)

        if 'expires' in attr:
            attr['expires'] = _parse_expires(attr['expires'])

        prefixes = self.list_prefix(auth, spec)
        where, params1 = self._expand_prefix_spec(spec.copy())

        update, params2 = self._sql_expand_update(attr)
        params = dict(params2.items() + params1.items())

        sql = "UPDATE ip_net_plan SET " + update + " WHERE " + where
        sql += " RETURNING id"

        self._execute(sql, params)
        updated_prefixes = self._get_updated_rows(auth, self.search_prefix)

        # write to audit table
        for p in prefixes:
            self.audit_log(auth, 'edit', vrf=p, prefix=p,
                           message='Edited prefix {0} attr: {1}'
                           .format(p['prefix'], str(attr)))

            # Only add to log if something was changed
            if p['pool_id'] != pool['id']:
                # If pool ID set, pool was expanded
                if pool['id'] is not None:
                    self.audit_log(auth, 'edit', pool=pool, vrf=p, prefix=p,
                                   message='Expanded pool {0} with prefix {1}'
                                   .format(pool['name'], p['prefix']))

                # if prefix had pool set previously, prefix was removed from that pool
                if p['pool_id'] is not None:
                    pool2 = self._get_pool(auth, { 'id': p['pool_id'] })
                    self.audit_log(auth, 'remove', vrf=p, prefix=p, pool=pool2,
                                   message='Removed prefix {0} from pool {1}'
                                   .format(p['prefix'], pool2['name']))

        return updated_prefixes

    def find_free_prefix(self, auth, vrf, args):
        """ Finds free prefixes in the sources given in `args`.

            * `auth` [BaseAuth]
                AAA options.
            * `vrf` [vrf]
                Full VRF-dict specifying in which VRF the prefix should be
                unique.
            * `args` [find_free_prefix_args]
                Arguments to the find free prefix function.

            Returns a list of dicts.

            Prefixes can be found in two ways: from a pool of from a prefix.

            From a pool
            The `args` argument is set to a dict with key :attr:`from-pool` set to a
            pool spec. This is the pool from which the prefix will be assigned.
            Also the key :attr:`family` needs to be set to the adress family (integer
            4 or 6) of the requested prefix.  Optionally, also the key
            :attr:`prefix_length` can be added to the `attr` argument, and will then
            override the default prefix length.

            Example::

                args = {
                    'from-pool': { 'name': 'CUSTOMER-' },
                    'family': 6,
                    'prefix_length': 64
                }

            From a prefix
                Instead of specifying a pool, a prefix which will be searched
                for new prefixes can be specified. In `args`, the key
                :attr:`from-prefix` is set to the prefix you want to allocate
                from and the key :attr:`prefix_length` is set to the wanted prefix
                length.

            Example::

                args = {
                    'from-prefix': '192.0.2.0/24'
                    'prefix_length': 27
                }

            The key :attr:`count` can also be set in the `args` argument to specify
            how many prefixes that should be returned. If omitted, the default
            value is 1000.

            The :func:`find_free_prefix` function is used internally by the
            :func:`add_prefix` function to find available prefixes from the given
            sources.
        """

        # input sanity
        if type(args) is not dict:
            raise NipapInputError("invalid input, please provide dict as args")

        # TODO: find good default value for max_num
        # TODO: let max_num be configurable from configuration file
        max_count = 1000
        if 'count' in args:
            if int(args['count']) > max_count:
                raise NipapValueError("count over the maximum result size")
        else:
            args['count'] = 1

        if 'from-pool' in args:
            if 'from-prefix' in args:
                raise NipapInputError("specify 'from-pool' OR 'from-prefix'")
            if 'family' not in args:
                raise NipapMissingInputError("'family' must be specified with 'from-pool' mode")
            try:
                assert int(args['family']) in [ 4, 6 ]
            except (TypeError, AssertionError):
                raise NipapValueError("incorrect family specified, must be 4 or 6")

        elif 'from-prefix' in args:
            if type(args['from-prefix']) is not list:
                raise NipapInputError("from-prefix should be a list")
            if 'from-pool' in args:
                raise NipapInputError("specify 'from-pool' OR 'from-prefix'")
            if 'prefix_length' not in args:
                raise NipapMissingInputError("'prefix_length' must be specified with 'from-prefix'")
            if 'family' in args:
                raise NipapExtraneousInputError("'family' is superfluous when in 'from-prefix' mode")

        # determine prefixes
        prefixes = []
        wpl = 0
        if 'from-pool' in args:
            # extract prefixes from
            pool_result = self.list_pool(auth, args['from-pool'])
            self._logger.debug(args)
            if pool_result == []:
                raise NipapNonExistentError("Non-existent pool specified")
            for p in pool_result[0]['prefixes']:
                if self._get_afi(p) == int(args['family']):
                    prefixes.append(p)
            if len(prefixes) == 0:
                raise NipapInputError('No prefixes of family %s in pool' % str(args['family']))
            if 'prefix_length' not in args:
                if int(args['family']) == 4:
                    wpl = pool_result[0]['ipv4_default_prefix_length']
                else:
                    wpl = pool_result[0]['ipv6_default_prefix_length']

        afi = None
        if 'from-prefix' in args:
            for prefix in args['from-prefix']:
                prefix_afi = self._get_afi(prefix)
                if afi is None:
                    afi = prefix_afi
                elif afi != prefix_afi:
                    raise NipapInputError("mixing of address-family is not allowed for 'from-prefix' arg")
                prefixes.append(prefix)

        if 'prefix_length' in args:
            try:
                wpl = int(args['prefix_length'])
            except ValueError:
                raise NipapValueError("prefix length must be integer")

        # sanity check the wanted prefix length
        if afi == 4:
            if wpl < 0 or wpl > 32:
                raise NipapValueError("the specified wanted prefix length argument must be between 0 and 32 for ipv4")
        elif afi == 6:
            if wpl < 0 or wpl > 128:
                raise NipapValueError("the specified wanted prefix length argument must be between 0 and 128 for ipv6")

        # build SQL
        params = {}
        # TODO: this makes me want to piss my pants
        #       we should really write a patch to psycopg2 or something to
        #       properly adapt an python list of texts with values looking
        #       like prefixes to a postgresql array of inets
        sql_prefix = ' UNION '.join('SELECT %(prefix' + str(prefixes.index(p)) + ')s AS prefix' for p in prefixes)
        for p in prefixes:
            params['prefix' + str(prefixes.index(p))] = str(p)

        damp = 'SELECT array_agg((prefix::text)::inet) FROM (' + sql_prefix + ') AS a'

        sql = """SELECT * FROM find_free_prefix(%(vrf_id)s, (""" + damp + """), %(prefix_length)s, %(max_result)s) AS prefix"""

        v = self._get_vrf(auth, vrf or {}, '')

        params['vrf_id'] = v['id']
        params['prefixes'] = prefixes
        params['prefix_length'] = wpl
        params['max_result'] = args['count']

        self._execute(sql, params)

        res = list()
        for row in self._curs_pg:
            res.append(str(row['prefix']))

        return res



    def list_prefix(self, auth, spec = None):
        """ List prefixes matching the `spec`.

            * `auth` [BaseAuth]
                AAA options.
            * `spec` [prefix_spec]
                Specifies prefixes to list. If omitted, all will be listed.

            Returns a list of dicts.

            This is a quite blunt tool for finding prefixes, mostly useful for
            fetching data about a single prefix. For more capable alternatives,
            see the :func:`search_prefix` or :func:`smart_search_prefix` functions.
        """

        self._logger.debug("list_prefix called; spec: %s" % str(spec))


        if type(spec) is dict:
            where, params = self._expand_prefix_spec(spec.copy(), 'inp.')
        else:
            raise NipapError("invalid prefix specification")

        if where != '':
            where = ' WHERE ' + where

        sql = """SELECT
            inp.id,
            vrf.id AS vrf_id,
            vrf.rt AS vrf_rt,
            vrf.name AS vrf_name,
            family(prefix) AS family,
            inp.prefix,
            inp.display_prefix,
            inp.description,
            COALESCE(inp.inherited_tags, '{}') AS inherited_tags,
            COALESCE(inp.tags, '{}') AS tags,
            inp.node,
            inp.comment,
            pool.id AS pool_id,
            pool.name AS pool_name,
            inp.type,
            inp.indent,
            inp.country,
            inp.order_id,
            inp.customer_id,
            inp.external_key,
            inp.authoritative_source,
            inp.alarm_priority,
            inp.monitor,
            inp.vlan,
            inp.added,
            inp.last_modified,
            inp.total_addresses,
            inp.used_addresses,
            inp.free_addresses,
            inp.status,
            inp.avps,
            inp.expires
            FROM ip_net_plan inp
            JOIN ip_net_vrf vrf ON (inp.vrf_id = vrf.id)
            LEFT JOIN ip_net_pool pool ON (inp.pool_id = pool.id) %s
            ORDER BY vrf.rt NULLS FIRST, prefix""" % where

        self._execute(sql, params)

        res = list()
        for row in self._curs_pg:
            pref = dict(row)
            pref['display_prefix'] = str(pref['display_prefix'])
            res.append(pref)

        return res



    def _db_remove_prefix(self, spec, recursive = False):
        """ Do the underlying database operations to delete a prefix
        """
        if recursive:
            prefix = spec['prefix']
            del spec['prefix']
            where, params = self._expand_prefix_spec(spec)
            spec['prefix'] = prefix
            params['prefix'] = prefix
            where = 'prefix <<= %(prefix)s AND ' + where
        else:
            where, params = self._expand_prefix_spec(spec)

        sql = "DELETE FROM ip_net_plan AS p WHERE %s" % where
        self._execute(sql, params)



    @requires_rw
    def remove_prefix(self, auth, spec, recursive = False):
        """ Remove prefix matching `spec`.

            * `auth` [BaseAuth]
                AAA options.
            * `spec` [prefix_spec]
                Specifies prefixe to remove.
        """

        self._logger.debug("remove_prefix called; spec: %s" % str(spec))

        # sanity check - do we have all attributes?
        if 'id' in spec:
            # recursive requires a prefix, so translate id to prefix
            p = self.list_prefix(auth, spec)[0]
            del spec['id']
            spec['prefix'] = p['prefix']
            spec['vrf_id'] = p['vrf_id']
        elif 'prefix' in spec:
            pass
        else:
            raise NipapMissingInputError('missing prefix or id of prefix')

        prefixes = self.list_prefix(auth, spec)

        if recursive:
            spec['type'] = 'host'
            self._db_remove_prefix(spec, recursive)
            del spec['type']
            self._db_remove_prefix(spec, recursive)
        else:
            self._db_remove_prefix(spec)

        # write to audit table
        for p in prefixes:
            self.audit_log(auth, 'remove', vrf=p, prefix=p,
                           message='Prefix {0} removed'.format(p['prefix']))

            if p['pool_id'] is not None:
                pool = self._get_pool(auth, { 'id': p['pool_id'] })
                self.audit_log(auth, 'remove', vrf=p, pool=pool, prefix=p,
                               message='Prefix {0} removed from pool {1}'
                               .format(p['prefix'], pool['name']))

    def search_prefix(self, auth, query, search_options=None):
        """ Search prefix list for prefixes matching `query`.

            * `auth` [BaseAuth]
                AAA options.
            * `query` [dict_to_sql]
                How the search should be performed.
            * `search_options` [options_dict]
                Search options, see below.

            Returns a list of dicts.

            The `query` argument passed to this function is designed to be
            able to specify how quite advanced search operations should be
            performed in a generic format. It is internally expanded to a SQL
            WHERE-clause.

            The `query` is a dict with three elements, where one specifies the
            operation to perform and the two other specifies its arguments. The
            arguments can themselves be `query` dicts, to build more complex
            queries.

            The :attr:`operator` key specifies what operator should be used for the
            comparison. Currently the following operators are supported:

            * :data:`and` - Logical AND
            * :data:`or` - Logical OR
            * :data:`equals` - Equality; =
            * :data:`not_equals` - Inequality; !=
            * :data:`less` - Less than; <
            * :data:`less_or_equal` - Less than or equal to; <=
            * :data:`greater` - Greater than; >
            * :data:`greater_or_equal` - Greater than or equal to; >=
            * :data:`like` - SQL LIKE
            * :data:`regex_match` - Regular expression match
            * :data:`regex_not_match` - Regular expression not match
            * :data:`contains` - IP prefix contains
            * :data:`contains_equals` - IP prefix contains or is equal to
            * :data:`contained_within` - IP prefix is contained within
            * :data:`contained_within_equals` - IP prefix is contained within or equals

            The :attr:`val1` and :attr:`val2` keys specifies the values which are subjected
            to the comparison. :attr:`val1` can be either any prefix attribute or an
            entire query dict. :attr:`val2` can be either the value you want to
            compare the prefix attribute to, or an entire `query` dict.

            Example 1 - Find the prefixes which contains 192.0.2.0/24::

                query = {
                    'operator': 'contains',
                    'val1': 'prefix',
                    'val2': '192.0.2.0/24'
                }

            This will be expanded to the pseudo-SQL query::

                SELECT * FROM prefix WHERE prefix contains '192.0.2.0/24'

            Example 2 - Find for all assignments in prefix 192.0.2.0/24::

                query = {
                    'operator': 'and',
                    'val1': {
                        'operator': 'equals',
                        'val1': 'type',
                        'val2': 'assignment'
                    },
                    'val2': {
                        'operator': 'contained_within',
                        'val1': 'prefix',
                        'val2': '192.0.2.0/24'
                    }
                }

            This will be expanded to the pseudo-SQL query::

                SELECT * FROM prefix WHERE (type == 'assignment') AND (prefix contained within '192.0.2.0/24')

            The `options` argument provides a way to alter the search result a
            bit to assist in client implementations. Most options regard parent
            and children prefixes, that is the prefixes which contain the
            prefix(es) matching the search terms (parents) or the prefixes
            which are contained by the prefix(es) matching the search terms.
            The search options can also be used to limit the number of rows
            returned.

            The following options are available:
                * :attr:`parents_depth` - How many levels of parents to return. Set to :data:`-1` to include all parents.
                * :attr:`children_depth` - How many levels of children to return. Set to :data:`-1` to include all children.
                * :attr:`include_all_parents` - Include all parents, no matter what depth is specified.
                * :attr:`include_all_children` - Include all children, no matter what depth is specified.
                * :attr:`max_result` - The maximum number of prefixes to return (default :data:`50`).
                * :attr:`offset` - Offset the result list this many prefixes (default :data:`0`).

            The options above gives the possibility to specify how many levels
            of parent and child prefixes to return in addition to the prefixes
            that actually matched the search terms. This is done by setting the
            :attr:`parents_depth` and :attr:`children depth` keys in the
            `search_options` dict to an integer value.  In addition to this it
            is possible to get all all parents and/or children included in the
            result set even though they are outside the limits set with
            :attr:`*_depth`.  The extra prefixes included will have the
            attribute :attr:`display` set to :data:`false` while the other ones
            (the actual search result togther with the ones included due to
            given depth) :attr:`display` set to :data:`true`. This feature is
            usable obtain search results with some context given around them,
            useful for example when displaying prefixes in a tree without the
            need to implement client side IP address logic.
        """

        if search_options is None:
            search_options = {}

        #
        # sanitize search options and set default if option missing
        #

        # include_parents
        if 'include_all_parents' not in search_options:
            search_options['include_all_parents'] = False
        else:
            if search_options['include_all_parents'] not in (True, False):
                raise NipapValueError('Invalid value for option ' +
                    "'include_all_parents'. Only true and false valid. Supplied value :'%s'" % str(search_options['include_all_parents']))

        # include_children
        if 'include_all_children' not in search_options:
            search_options['include_all_children'] = False
        else:
            if search_options['include_all_children'] not in (True, False):
                raise NipapValueError('Invalid value for option ' +
                    "'include_all_children'. Only true and false valid. Supplied value: '%s'" % str(search_options['include_all_children']))

        # parents_depth
        if 'parents_depth' not in search_options:
            search_options['parents_depth'] = 0
        else:
            try:
                search_options['parents_depth'] = int(search_options['parents_depth'])
            except (ValueError, TypeError):
                raise NipapValueError('Invalid value for option' +
                    ''' 'parent_depth'. Only integer values allowed.''')

        # children_depth
        if 'children_depth' not in search_options:
            search_options['children_depth'] = 0
        else:
            try:
                search_options['children_depth'] = int(search_options['children_depth'])
            except (ValueError, TypeError):
                raise NipapValueError('Invalid value for option' +
                    ''' 'children_depth'. Only integer values allowed.''')

        # include_neighbors
        if 'include_neighbors' not in search_options:
            search_options['include_neighbors'] = False
        else:
            if search_options['include_neighbors'] not in (True, False):
                raise NipapValueError('Invalid value for option ' +
                    "'include_neighbors'. Only true and false valid. Supplied value: '%s'" % str(search_options['include_neighbors']))

        # max_result
        if 'max_result' not in search_options:
            search_options['max_result'] = 50
        else:
            try:
                search_options['max_result'] = int(search_options['max_result'])
            except (ValueError, TypeError):
                raise NipapValueError('Invalid value for option' +
                    ''' 'max_result'. Only integer values allowed.''')

        # offset
        if 'offset' not in search_options:
            search_options['offset'] = 0
        else:
            try:
                search_options['offset'] = int(search_options['offset'])
            except (ValueError, TypeError):
                raise NipapValueError('Invalid value for option' +
                    ''' 'offset'. Only integer values allowed.''')

        # parent_prefix
        if 'parent_prefix' not in search_options:
            search_options['parent_prefix'] = None
        else:
            try:
                _ = int(search_options['parent_prefix'])
            except ValueError:
                raise NipapValueError(
                    "Invalid value '%s' for option 'parent_prefix'. Must be the ID of a prefix."
                        % search_options['parent_prefix'])
            try:
                parent_prefix = self.list_prefix(auth, { 'id': search_options['parent_prefix'] })[0]
            except IndexError:
                raise NipapNonExistentError("Parent prefix %s can not be found" % search_options['parent_prefix'])

        self._logger.debug('search_prefix search_options: %s' % str(search_options))

        # translate search options to SQL

        if search_options['include_all_parents'] or search_options['parents_depth'] == -1:
            where_parents = ''
        elif search_options['parents_depth'] >= 0:
            where_parents = 'AND p1.indent BETWEEN p2.indent - %d AND p1.indent' % search_options['parents_depth']
        else:
            raise NipapValueError("Invalid value for option 'parents_depth'. Only integer values > -1 allowed.")

        if search_options['include_all_children'] or search_options['children_depth'] == -1:
            where_children = ''
        elif search_options['children_depth'] >= 0:
            where_children = 'AND p1.indent BETWEEN p2.indent AND p2.indent + %d' % search_options['children_depth']
        else:
            raise NipapValueError("Invalid value for option 'children_depth'. Only integer values > -1 allowed.")

        if search_options['include_neighbors']:
            include_neighbors = 'true'
        else:
            include_neighbors = 'false'

        if search_options['parent_prefix']:
            vrf_id = 0
            if parent_prefix['vrf_id']:
                vrf_id = parent_prefix['vrf_id']
            where_parent_prefix = " WHERE (p1.vrf_id = %s AND iprange(p1.prefix) <<= iprange('%s') AND p1.indent <= %s) " % (vrf_id, parent_prefix['prefix'], parent_prefix['indent'] + 1)
            left_join = 'LEFT OUTER'
        else:
            where_parent_prefix = ''
            left_join = ''

        display = '(p1.prefix << p2.display_prefix OR p2.prefix <<= p1.prefix %s) OR (p2.prefix >>= p1.prefix %s)' % (where_parents, where_children)

        where, opt = self._expand_prefix_query(query)
        sql = """
    SELECT
        id,
        vrf_id,
        vrf_rt,
        vrf_name,
        family,
        display,
        match,
        prefix,
        prefix_length,
        display_prefix::text AS display_prefix,
        description,
        comment,
        inherited_tags,
        tags,
        node,
        pool_id,
        pool_name,
        type,
        status,
        indent,
        country,
        order_id,
        customer_id,
        external_key,
        authoritative_source,
        alarm_priority,
        monitor,
        vlan,
        added,
        last_modified,
        children,
        total_addresses,
        used_addresses,
        free_addresses,
        avps,
        expires
    FROM (
        SELECT DISTINCT ON(vrf_rt_order(vrf.rt), p1.prefix) p1.id,
            p1.prefix,
            p1.display_prefix,
            p1.description,
            p1.comment,
            COALESCE(p1.inherited_tags, '{}') AS inherited_tags,
            COALESCE(p1.tags, '{}') AS tags,
            p1.node,
            pool.id AS pool_id,
            pool.name AS pool_name,
            p1.type,
            p1.indent,
            p1.country,
            p1.order_id,
            p1.customer_id,
            p1.external_key,
            p1.authoritative_source,
            p1.alarm_priority,
            p1.monitor,
            p1.vlan,
            p1.added,
            p1.last_modified,
            p1.children,
            p1.total_addresses,
            p1.used_addresses,
            p1.free_addresses,
            p1.status,
            p1.avps,
            p1.expires,
            vrf.id AS vrf_id,
            vrf.rt AS vrf_rt,
            vrf.name AS vrf_name,
            masklen(p1.prefix) AS prefix_length,
            family(p1.prefix) AS family,
            (""" + display + """) AS display,
            CASE WHEN p1.prefix = p2.prefix THEN true ELSE false END AS match
            FROM ip_net_plan AS p1
            -- possible set LEFT OUTER JOIN, if we are doing a parent_prefix operation
            """ + left_join + """ JOIN ip_net_plan AS p2 ON
            (
                (
                    (p1.vrf_id = p2.vrf_id)
                    AND
                    (
                        -- Join in the parents (p1) of matching prefixes (p2)
                        (iprange(p1.prefix) >>= iprange(p2.prefix) """ + where_parents + """)
                        OR
                        -- Join in the children (p1) of matching prefixes (p2)
                        (iprange(p1.prefix) << iprange(p2.prefix) """ + where_children + """)
                        OR
                        -- Join in all neighbors (p1) of matching prefixes (p2)
                        (true = """ + include_neighbors + """ AND iprange(p1.prefix) << iprange(p2.display_prefix::cidr) AND p1.indent = p2.indent)
                    )
                )
                -- set match conditions for p2
                AND p2.id IN (
                    SELECT inp.id FROM ip_net_plan AS inp JOIN ip_net_vrf AS vrf ON inp.vrf_id = vrf.id LEFT JOIN ip_net_pool AS pool ON inp.pool_id = pool.id
                        WHERE """ + where + """
                    ORDER BY vrf_rt_order(vrf.rt) NULLS FIRST, prefix
                    LIMIT """ + str(int(search_options['max_result']) + int(search_options['offset'])) + """
                )
            )
            JOIN ip_net_vrf AS vrf ON (p1.vrf_id = vrf.id)
            LEFT JOIN ip_net_pool AS pool ON (p1.pool_id = pool.id)
            -- possible set where conditions, if we are doing a parent_prefix operation
            """ + where_parent_prefix + """
            ORDER BY vrf_rt_order(vrf.rt) NULLS FIRST, p1.prefix, CASE WHEN p1.prefix = p2.prefix THEN 0 ELSE 1 END OFFSET """  + str(search_options['offset']) + ") AS a ORDER BY vrf_rt_order(vrf_rt) NULLS FIRST, prefix"


        self._execute(sql, opt)

        result = list()
        for row in self._curs_pg:
            result.append(dict(row))
            # This is a SQL LIMIT clause implemented in Python. It is performed
            # here to avoid a silly planner missestimate in PostgreSQL. For too
            # low values of LIMIT, the planner will prefer plans with very low
            # startup costs which will in turn lead to the slow plan. We avoid
            # the low value (or any value really) of LIMIT by performing the
            # LIMIT in Python. There is still a LIMIT on the inner query which
            # together with the OFFSET, which is still performed in PostgreSQL,
            # yields a rather small result set and thus high speed.
            if len(result) >= int(search_options['max_result']):
                break

        return { 'search_options': search_options, 'result': result }



    def smart_search_prefix(self, auth, query_str, search_options=None, extra_query=None):
        """ Perform a smart search on prefix list.

            * `auth` [BaseAuth]
                AAA options.
            * `query_str` [string]
                Search string
            * `search_options` [options_dict]
                Search options. See :func:`search_prefix`.
            * `extra_query` [dict_to_sql]
                Extra search terms, will be AND:ed together with what is
                extracted from the query string.

            Return a dict with three elements:
                * :attr:`interpretation` - How the query string was interpreted.
                * :attr:`search_options` - Various search_options.
                * :attr:`result` - The search result.

                The :attr:`interpretation` is given as a list of dicts, each
                explaining how a part of the search key was interpreted (ie. what
                prefix attribute the search operation was performed on).

                The :attr:`result` is a list of dicts containing the search result.

            The smart search function tries to convert the query from a text
            string to a `query` dict which is passed to the
            :func:`search_prefix` function.  If multiple search keys are
            detected, they are combined with a logical AND.

            It tries to automatically detect IP addresses and prefixes and put
            these into the `query` dict with "contains_within" operators and so
            forth.

            See the :func:`search_prefix` function for an explanation of the
            `search_options` argument.
        """

        if search_options is None:
            search_options = {}

        self._logger.debug("smart_search_prefix query string: %s" % query_str)

        # find query parts
        try:
            query_str_parts = self._get_query_parts(query_str)
        except NipapValueError:
            return {
                'interpretation': [
                    {
                        'string': query_str,
                        'interpretation': 'unclosed quote',
                        'attribute': 'text'
                    }
                ],
                'search_options': search_options,
                'result': []
            }

        # go through parts and add to query_parts list
        query_parts = list()
        for query_str_part in query_str_parts:

            # tags
            if re.match('#', query_str_part['string']):
                self._logger.debug("Query part '" + query_str_part['string'] + "' interpreted as tag")
                query_str_part['interpretation'] = '(inherited) tag'
                query_str_part['attribute'] = 'tag'

                query_str_part['operator'] = 'equals_any'
                query_parts.append({
                    'operator': 'or',
                    'val1': {
                        'operator': 'equals_any',
                        'val1': 'tags',
                        'val2': query_str_part['string'][1:]
                    },
                    'val2': {
                        'operator': 'equals_any',
                        'val1': 'inherited_tags',
                        'val2': query_str_part['string'][1:]
                    }
                })

            # IPv4 prefix
            elif self._get_afi(query_str_part['string']) == 4 and len(query_str_part['string'].split('/')) == 2:
                self._logger.debug("Query part '" + query_str_part['string'] + "' interpreted as prefix")
                query_str_part['interpretation'] = 'IPv4 prefix'
                query_str_part['attribute'] = 'prefix'

                address, prefix_length = query_str_part['string'].split('/')

                # complete a prefix to it's fully expanded form
                # 10/8 will be expanded into 10.0.0.0/8 which PostgreSQL can
                # parse correctly
                while len(address.split('.')) < 4:
                    address += '.0'

                prefix = address + '/' + prefix_length

                if prefix != query_str_part['string']:
                    query_str_part['expanded'] = prefix

                strict_prefix = str(IPy.IP(query_str_part['string'], make_net = True))
                if prefix != strict_prefix:
                    query_str_part['strict_prefix'] = strict_prefix

                query_str_part['operator'] = 'contained_within_equals'
                query_parts.append({
                    'operator': 'contained_within_equals',
                    'val1': 'prefix',
                    'val2': strict_prefix
                })

            # IPv4 address
            # split on dot to make sure we have all four octets before we do a
            # search
            elif self._get_afi(query_str_part['string']) == 4 and len(query_str_part['string'].split('.')) == 4:
                self._logger.debug("Query part '" + query_str_part['string'] + "' interpreted as prefix")
                query_str_part['interpretation'] = 'IPv4 address'
                query_str_part['operator'] = 'contains_equals'
                query_str_part['attribute'] = 'prefix'
                query_parts.append({
                    'operator': 'contains_equals',
                    'val1': 'prefix',
                    'val2': query_str_part['string']
                })

            # IPv6 prefix
            elif self._get_afi(query_str_part['string']) == 6 and len(query_str_part['string'].split('/')) == 2:
                self._logger.debug("Query part '" + query_str_part['string'] + "' interpreted as IPv6 prefix")
                query_str_part['interpretation'] = 'IPv6 prefix'
                query_str_part['operator'] = 'contained_within_equals'
                query_str_part['attribute'] = 'prefix'

                strict_prefix = str(IPy.IP(query_str_part['string'], make_net = True))
                if query_str_part['string'] != strict_prefix:
                    query_str_part['strict_prefix'] = strict_prefix

                query_parts.append({
                    'operator': 'contained_within_equals',
                    'val1': 'prefix',
                    'val2': strict_prefix
                })

            # IPv6 address
            elif self._get_afi(query_str_part['string']) == 6:
                self._logger.debug("Query part '" + query_str_part['string'] + "' interpreted as IPv6 address")
                query_str_part['interpretation'] = 'IPv6 address'
                query_str_part['operator'] = 'contains_equals'
                query_str_part['attribute'] = 'prefix'
                query_parts.append({
                    'operator': 'contains_equals',
                    'val1': 'prefix',
                    'val2': query_str_part['string']
                })

            # Description or comment
            # TODO: add an equal search for VRF here
            else:
                self._logger.debug("Query part '" + query_str_part['string'] + "' interpreted as desc/comment")
                query_str_part['interpretation'] = 'text'
                query_str_part['operator'] = 'regex'
                query_str_part['attribute'] = 'description or comment or node or order_id or customer_id'
                query_parts.append({
                    'operator': 'or',
                    'val1': {
                        'operator': 'or',
                        'val1': {
                            'operator': 'or',
                            'val1': {
                                'operator': 'or',
                                'val1': {
                                    'operator': 'regex_match',
                                    'val1': 'comment',
                                    'val2': query_str_part['string']
                                    },
                                'val2': {
                                    'operator': 'regex_match',
                                    'val1': 'description',
                                    'val2': query_str_part['string']
                                    }
                                },
                            'val2': {
                                'operator': 'regex_match',
                                'val1': 'node',
                                'val2': query_str_part['string']
                                }
                            },
                        'val2': {
                            'operator': 'regex_match',
                            'val1': 'order_id',
                            'val2': query_str_part['string']
                            },
                        },
                    'val2': {
                        'operator': 'regex_match',
                        'val1': 'customer_id',
                        'val2': query_str_part['string']
                        }
                    })

        # Sum all query parts to one query
        query = {}
        if len(query_parts) > 0:
            query = query_parts[0]

        if len(query_parts) > 1:
            for query_part in query_parts[1:]:
                query = {
                    'operator': 'and',
                    'val1': query_part,
                    'val2': query
                }

        if extra_query is not None:
            query = {
                'operator': 'and',
                'val1': query,
                'val2': extra_query
            }

        self._logger.debug("Expanded to: %s" % str(query))

        search_result = self.search_prefix(auth, query, search_options)
        search_result['interpretation'] = query_str_parts

        return search_result


    #
    # ASN functions
    #

    def _expand_asn_query(self, query, table_name = None):
        """ Expand ASN query dict into a WHERE-clause.

            If you need to prefix each column reference with a table
            name, that can be supplied via the table_name argument.
        """

        where = str()
        opt = list()

        # handle table name, can be None
        if table_name is None:
            col_prefix = ""
        else:
            col_prefix = table_name + "."

        if type(query['val1']) == dict and type(query['val2']) == dict:
            # Sub expression, recurse! This is used for boolean operators: AND OR
            # add parantheses

            sub_where1, opt1 = self._expand_asn_query(query['val1'], table_name)
            sub_where2, opt2 = self._expand_asn_query(query['val2'], table_name)
            try:
                where += str(" (%s %s %s) " % (sub_where1, _operation_map[query['operator']], sub_where2) )
            except KeyError:
                raise NipapNoSuchOperatorError("No such operator %s" % str(query['operator']))

            opt += opt1
            opt += opt2

        else:

            # TODO: raise exception if someone passes one dict and one "something else"?

            # val1 is variable, val2 is string.
            asn_attr = dict()
            asn_attr['asn'] = 'asn'
            asn_attr['name'] = 'name'

            if query['val1'] not in asn_attr:
                raise NipapInputError('Search variable \'%s\' unknown' % str(query['val1']))

            # workaround for handling equal matches of NULL-values
            if query['operator'] == 'equals' and query['val2'] is None:
                query['operator'] = 'is'
            elif query['operator'] == 'not_equals' and query['val2'] is None:
                query['operator'] = 'is_not'

            # build where clause
            if query['operator'] not in _operation_map:
                raise NipapNoSuchOperatorError("No such operator %s" % query['operator'])

            where = str(" %s%s %s %%s " %
                ( col_prefix, asn_attr[query['val1']],
                _operation_map[query['operator']] )
            )

            opt.append(query['val2'])

        return where, opt



    def _expand_asn_spec(self, spec):
        """ Expand ASN specification to SQL.

            asn [integer]
                Automonous System Number

            name [string]
                name of ASN
        """

        if type(spec) is not dict:
            raise NipapInputError("asn specification must be a dict")

        allowed_values = ['asn', 'name']
        for a in spec:
            if a not in allowed_values:
                raise NipapExtraneousInputError("extraneous specification key %s" % a)

        if 'asn' in spec:
            if type(spec['asn']) not in (int, long):
                raise NipapValueError("asn specification key 'asn' must be an integer")
            if 'name' in spec:
                raise NipapExtraneousInputError("asn specification contain both 'asn' and 'name', specify asn or name")
        elif 'name' in spec:
            if type(spec['name']) != type(''):
                raise NipapValueError("asn specification key 'name' must be a string")
            if 'asn' in spec:
                raise NipapExtraneousInputError("asn specification contain both 'asn' and 'name', specify asn or name")

        where, params = self._sql_expand_where(spec, 'spec_')

        return where, params



    def list_asn(self, auth, asn=None):
        """ List AS numbers
        """

        if asn is None:
            asn = {}

        self._logger.debug("list_asn called; asn: %s" % str(asn))

        sql = "SELECT * FROM ip_net_asn"
        params = list()

        where, params = self._expand_asn_spec(asn)
        if len(params) > 0:
            sql += " WHERE " + where

        sql += " ORDER BY asn ASC"

        self._execute(sql, params)

        res = list()
        for row in self._curs_pg:
            res.append(dict(row))

        return res



    @requires_rw
    def add_asn(self, auth, attr):
        """ Add AS number to NIPAP.

            * `auth` [BaseAuth]
                AAA options.
            * `attr` [asn_attr]
                ASN attributes.

            Returns a dict describing the ASN which was added.
        """

        self._logger.debug("add_asn called; attr: %s" % str(attr))

        # sanity check - do we have all attributes?
        req_attr = [ 'asn', ]
        allowed_attr = [ 'asn', 'name' ]
        self._check_attr(attr, req_attr, allowed_attr)

        insert, params = self._sql_expand_insert(attr)
        sql = "INSERT INTO ip_net_asn " + insert
        self._execute(sql, params)

        asn = self.list_asn(auth, { 'asn': attr['asn'] })[0]

        # write to audit table
        self.audit_log(auth, 'add',
                       message='Added ASN {0} with attr: {1}'
                       .format(attr['asn'], str(attr)))

        return asn



    @requires_rw
    def edit_asn(self, auth, asn, attr):
        """ Edit AS number

            * `auth` [BaseAuth] AAA options.
            * `asn` [integer] AS number to edit.
            * `attr` [asn_attr] New AS attributes.
        """

        self._logger.debug("edit_asn called; asn: %s attr: %s" %
                (str(asn), str(attr)))

        # sanity check - do we have all attributes?
        req_attr = [ ]
        allowed_attr = [ 'name', ]
        self._check_attr(attr, req_attr, allowed_attr)

        asns = self.list_asn(auth, asn)

        where, params1 = self._expand_asn_spec(asn)
        update, params2 = self._sql_expand_update(attr)
        params = dict(params2.items() + params1.items())

        sql = "UPDATE ip_net_asn SET " + update + " WHERE " + where
        sql += " RETURNING *"

        self._execute(sql, params)
        updated_asns = []
        for row in self._curs_pg:
            updated_asns.append(dict(row))

        # write to audit table
        for a in asns:
            self.audit_log(auth, 'edit',
                           'Edited ASN {0} attr: {1}'
                           .format(str(a['asn']), str(attr)))

        return updated_asns

    @requires_rw
    def remove_asn(self, auth, asn):
        """ Remove AS number
        """

        self._logger.debug("remove_asn called; asn: %s" % str(asn))

        # get list of ASNs to remove before removing them
        asns = self.list_asn(auth, asn)

        # remove
        where, params = self._expand_asn_spec(asn)
        sql = "DELETE FROM ip_net_asn WHERE " + where
        self._execute(sql, params)

        # write to audit table
        for a in asns:
            self.audit_log(auth, 'remove',
                           'Removed ASN {0}'.format(str(a['asn'])))

    def search_asn(self, auth, query, search_options=None):
        """ Search ASNs for entries matching 'query'

            * `auth` [BaseAuth]
                AAA options.
            * `query` [dict_to_sql]
                How the search should be performed.
            * `search_options` [options_dict]
                Search options, see below.

            Returns a list of dicts.

            The `query` argument passed to this function is designed to be
            able to specify how quite advanced search operations should be
            performed in a generic format. It is internally expanded to a SQL
            WHERE-clause.

            The `query` is a dict with three elements, where one specifies the
            operation to perform and the two other specifies its arguments. The
            arguments can themselves be `query` dicts, to build more complex
            queries.

            The :attr:`operator` key specifies what operator should be used for the
            comparison. Currently the following operators are supported:

            * :data:`and` - Logical AND
            * :data:`or` - Logical OR
            * :data:`equals` - Equality; =
            * :data:`not_equals` - Inequality; !=
            * :data:`like` - SQL LIKE
            * :data:`regex_match` - Regular expression match
            * :data:`regex_not_match` - Regular expression not match

            The :attr:`val1` and :attr:`val2` keys specifies the values which are subjected
            to the comparison. :attr:`val1` can be either any prefix attribute or an
            entire query dict. :attr:`val2` can be either the value you want to
            compare the prefix attribute to, or an entire `query` dict.

            The search options can also be used to limit the number of rows
            returned or set an offset for the result.

            The following options are available:
                * :attr:`max_result` - The maximum number of prefixes to return (default :data:`50`).
                * :attr:`offset` - Offset the result list this many prefixes (default :data:`0`).
        """

        if search_options is None:
            search_options = {}

        #
        # sanitize search options and set default if option missing
        #

        # max_result
        if 'max_result' not in search_options:
            search_options['max_result'] = 50
        else:
            try:
                search_options['max_result'] = int(search_options['max_result'])
            except (ValueError, TypeError):
                raise NipapValueError('Invalid value for option' +
                    ''' 'max_result'. Only integer values allowed.''')

        # offset
        if 'offset' not in search_options:
            search_options['offset'] = 0
        else:
            try:
                search_options['offset'] = int(search_options['offset'])
            except (ValueError, TypeError):
                raise NipapValueError('Invalid value for option' +
                    ''' 'offset'. Only integer values allowed.''')

        self._logger.debug('search_asn search_options: %s' % str(search_options))

        opt = None
        sql = """ SELECT * FROM ip_net_asn """

        # add where clause if we have any search terms
        if query != {}:

            where, opt = self._expand_asn_query(query)
            sql += " WHERE " + where

        sql += " ORDER BY asn LIMIT " + str(search_options['max_result'])
        self._execute(sql, opt)

        result = list()
        for row in self._curs_pg:
            result.append(dict(row))

        return { 'search_options': search_options, 'result': result }



    def smart_search_asn(self, auth, query_str, search_options=None, extra_query=None):
        """ Perform a smart search operation among AS numbers

            * `auth` [BaseAuth]
                AAA options.
            * `query_str` [string]
                Search string
            * `search_options` [options_dict]
                Search options. See :func:`search_asn`.
            * `extra_query` [dict_to_sql]
                Extra search terms, will be AND:ed together with what is
                extracted from the query string.

            Return a dict with three elements:
                * :attr:`interpretation` - How the query string was interpreted.
                * :attr:`search_options` - Various search_options.
                * :attr:`result` - The search result.

                The :attr:`interpretation` is given as a list of dicts, each
                explaining how a part of the search key was interpreted (ie. what
                ASN attribute the search operation was performed on).

                The :attr:`result` is a list of dicts containing the search result.

            The smart search function tries to convert the query from a text
            string to a `query` dict which is passed to the
            :func:`search_asn` function.  If multiple search keys are
            detected, they are combined with a logical AND.

            See the :func:`search_asn` function for an explanation of the
            `search_options` argument.
        """

        if search_options is None:
            search_options = {}

        self._logger.debug("smart_search_asn called; query_str: %s" % query_str)

        # find query parts
        try:
            query_str_parts = self._get_query_parts(query_str)
        except NipapValueError:
            return {
                'interpretation': [
                    {
                        'string': query_str,
                        'interpretation': 'unclosed quote',
                        'attribute': 'text'
                    }
                ],
                'search_options': search_options,
                'result': []
            }

        # go through parts and add to query_parts list
        query_parts = list()
        for query_str_part in query_str_parts:

            is_int = True
            try:
                int(query_str_part['string'])
            except ValueError:
                is_int = False

            if is_int:
                self._logger.debug("Query part '" + query_str_part['string'] + "' interpreted as integer (ASN)")
                query_str_part['interpretation'] = 'asn'
                query_str_part['operator'] = 'equals'
                query_str_part['attribute'] = 'asn'
                query_parts.append({
                    'operator': 'equals',
                    'val1': 'asn',
                    'val2': query_str_part['string']
                })

            else:
                self._logger.debug("Query part '" + query_str_part['string'] + "' interpreted as text")
                query_str_part['interpretation'] = 'text'
                query_str_part['operator'] = 'regex'
                query_str_part['attribute'] = 'name'
                query_parts.append({
                    'operator': 'regex_match',
                    'val1': 'name',
                    'val2': query_str_part['string']
                })

        # Sum all query parts to one query
        query = {}
        if len(query_parts) > 0:
            query = query_parts[0]

        if len(query_parts) > 1:
            for query_part in query_parts[1:]:
                query = {
                    'operator': 'and',
                    'val1': query_part,
                    'val2': query
                }

        if extra_query is not None:
            query = {
                'operator': 'and',
                'val1': query,
                'val2': extra_query
            }

        self._logger.debug("Expanded to: %s" % str(query))

        search_result = self.search_asn(auth, query, search_options)
        search_result['interpretation'] = query_str_parts

        return search_result



    #
    # Tag functions
    #

    def _expand_tag_query(self, query, table_name = None):
        """ Expand Tag query dict into a WHERE-clause.

            If you need to prefix each column reference with a table
            name, that can be supplied via the table_name argument.
        """

        where = str()
        opt = list()

        # handle table name, can be None
        if table_name is None:
            col_prefix = ""
        else:
            col_prefix = table_name + "."

        if type(query['val1']) == dict and type(query['val2']) == dict:
            # Sub expression, recurse! This is used for boolean operators: AND OR
            # add parantheses

            sub_where1, opt1 = self._expand_tag_query(query['val1'], table_name)
            sub_where2, opt2 = self._expand_tag_query(query['val2'], table_name)
            try:
                where += str(" (%s %s %s) " % (sub_where1, _operation_map[query['operator']], sub_where2) )
            except KeyError:
                raise NipapNoSuchOperatorError("No such operator %s" % str(query['operator']))

            opt += opt1
            opt += opt2

        else:

            # TODO: raise exception if someone passes one dict and one "something else"?

            # val1 is variable, val2 is string.
            tag_attr = dict()
            tag_attr['name'] = 'name'

            if query['val1'] not in tag_attr:
                raise NipapInputError('Search variable \'%s\' unknown' % str(query['val1']))

            # workaround for handling equal matches of NULL-values
            if query['operator'] == 'equals' and query['val2'] is None:
                query['operator'] = 'is'
            elif query['operator'] == 'not_equals' and query['val2'] is None:
                query['operator'] = 'is_not'

            # build where clause
            if query['operator'] not in _operation_map:
                raise NipapNoSuchOperatorError("No such operator %s" % query['operator'])

            where = str(" %s%s %s %%s " %
                ( col_prefix, tag_attr[query['val1']],
                _operation_map[query['operator']] )
            )

            opt.append(query['val2'])

        return where, opt



    def search_tag(self, auth, query, search_options=None):
        """ Search Tags for entries matching 'query'

            * `auth` [BaseAuth]
                AAA options.
            * `query` [dict_to_sql]
                How the search should be performed.
            * `search_options` [options_dict]
                Search options, see below.

            Returns a list of dicts.

            The `query` argument passed to this function is designed to be
            able to specify how quite advanced search operations should be
            performed in a generic format. It is internally expanded to a SQL
            WHERE-clause.

            The `query` is a dict with three elements, where one specifies the
            operation to perform and the two other specifies its arguments. The
            arguments can themselves be `query` dicts, to build more complex
            queries.

            The :attr:`operator` key specifies what operator should be used for the
            comparison. Currently the following operators are supported:

            * :data:`and` - Logical AND
            * :data:`or` - Logical OR
            * :data:`equals` - Equality; =
            * :data:`not_equals` - Inequality; !=
            * :data:`like` - SQL LIKE
            * :data:`regex_match` - Regular expression match
            * :data:`regex_not_match` - Regular expression not match

            The :attr:`val1` and :attr:`val2` keys specifies the values which are subjected
            to the comparison. :attr:`val1` can be either any prefix attribute or an
            entire query dict. :attr:`val2` can be either the value you want to
            compare the prefix attribute to, or an entire `query` dict.

            The search options can also be used to limit the number of rows
            returned or set an offset for the result.

            The following options are available:
                * :attr:`max_result` - The maximum number of prefixes to return (default :data:`50`).
                * :attr:`offset` - Offset the result list this many prefixes (default :data:`0`).
        """

        if search_options is None:
            search_options = {}

        #
        # sanitize search options and set default if option missing
        #

        # max_result
        if 'max_result' not in search_options:
            search_options['max_result'] = 50
        else:
            try:
                search_options['max_result'] = int(search_options['max_result'])
            except (ValueError, TypeError):
                raise NipapValueError('Invalid value for option' +
                    ''' 'max_result'. Only integer values allowed.''')

        # offset
        if 'offset' not in search_options:
            search_options['offset'] = 0
        else:
            try:
                search_options['offset'] = int(search_options['offset'])
            except (ValueError, TypeError):
                raise NipapValueError('Invalid value for option' +
                    ''' 'offset'. Only integer values allowed.''')

        self._logger.debug('search_tag search_options: %s' % str(search_options))

        opt = None
        sql = """ SELECT * FROM (SELECT DISTINCT unnest(tags) AS name FROM
        ip_net_plan) AS a """

        # add where clause if we have any search terms
        if query != {}:

            where, opt = self._expand_tag_query(query)
            sql += " WHERE " + where

        sql += " ORDER BY name LIMIT " + str(search_options['max_result'])
        self._execute(sql, opt)

        result = list()
        for row in self._curs_pg:
            result.append(dict(row))

        return { 'search_options': search_options, 'result': result }

    def audit_log(self, auth, action, message=None,
                  vrf=None, pool=None, prefix=None):
        # write to audit table
        audit_params = {
            'username': auth.username,
            'authenticated_as': auth.authenticated_as,
            'full_name': auth.full_name,
            'authoritative_source': auth.authoritative_source,
            'description': message or 'no message provided',
        }

        self._logger.info(
            'USER:{username}({full_name})@{authenticated_as} '
            'SOURCE:{authoritative_source} ACTION:{op} '
            'DESC:{description}'.format(op=action, **audit_params))

        # add in addition details for the DB portion
        if vrf:
            audit_params.update({
                'vrf_id': vrf.get('vrf_id') or vrf.get('id'),
                'vrf_rt': vrf.get('vrf_rt') or vrf.get('rt'),
                'vrf_name': vrf.get('vrf_name') or vrf.get('name'),
            })

        if pool:
            audit_params.update({
                'pool_id': pool['id'],
                'pool_name': pool['name'],
            })

        if prefix:
            audit_params.update({
                'prefix_id': prefix['id'],
                'prefix_prefix': prefix['prefix'],
            })

        sql, params = self._sql_expand_insert(audit_params)
        self._execute('INSERT INTO ip_net_log %s' % sql, params)


class NipapError(Exception):
    """ NIPAP base error class.
    """

    error_code = 1000


class NipapInputError(NipapError):
    """ Erroneous input.

        A general input error.
    """

    error_code = 1100


class NipapMissingInputError(NipapInputError):
    """ Missing input.

        Most input is passed in dicts, this could mean a missing key in a dict.
    """

    error_code = 1110


class NipapExtraneousInputError(NipapInputError):
    """ Extraneous input.

        Most input is passed in dicts, this could mean an unknown key in a dict.
    """

    error_code = 1120


class NipapNoSuchOperatorError(NipapInputError):
    """ A non existent operator was specified.
    """

    error_code = 1130


class NipapValueError(NipapError):
    """ Something wrong with a value

        For example, trying to send an integer when an IP address is expected.
    """

    error_code = 1200


class NipapNonExistentError(NipapError):
    """ A non existent object was specified

        For example, try to get a prefix from a pool which doesn't exist.
    """

    error_code = 1300


class NipapDuplicateError(NipapError):
    """ The passed object violates unique constraints

        For example, create a VRF with a name of an already existing one.
    """

    error_code = 1400

# vim: et ts=4 :
