""" NIPAP API
    =========

    This module contains the Nipap class which provides most of the logic in
    NIPAP apart from that contained within the PostgreSQL database.

    NIPAP contains three types of objects: VRFs, prefixes and pools.

    VRF
    ------
    A VRF represents a Virtual Routing and Forwarding instance. By default, one
    VRF which represents the global routing table ("no VRF") is defined. This
    ID always has the ID 0.

    VRF attributes
    ^^^^^^^^^^^^^^
    * :attr:`id` - ID number of the VRF.
    * :attr:`vrf` - The VRF RDs administrator and assigned number subfields
        (eg. 65000:123).
    * :attr:`name` - A short name, such as 'VPN Customer A'.
    * :attr:`description` - A longer description of what the VRF is used for.

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
    A prefix object defines an address prefix. Prefixes can be one of three
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
    * :attr:`node` - FQDN of node the prefix is assigned to, if type is host.
    * :attr:`pool_id` - ID of pool, if the prefix belongs to a pool.
    * :attr:`pool_name` - Name of pool, if the prefix belongs to a pool.
    * :attr:`type` - Prefix type, string 'reservation', 'assignment' or 'host'.
    * :attr:`indent` - Depth in prefix tree. Set by NIPAP.
    * :attr:`country` - Two letter country code where the prefix resides.
    * :attr:`order_id` - Order identifier.
    * :attr:`external_key` - A field for use by external systems which needs to
        store references to its own dataset.
    * :attr:`authoritative_source` - String identifying which system last
        modified the prefix.
    * :attr:`alarm_priority` - String 'low', 'medium' or 'high'.
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
    Reserved prefixes can be gathered in a pool which then can be used when
    adding prefixes. The `add_prefix` can for example be asked to return a
    prefix from the pool CORE-LOOPBACKS. Then all the prefix member of this pool
    will be examined for a suitable prefix with the default length specified in
    the pool if nothing else is given.

    Pool attributes
    ^^^^^^^^^^^^^^^
    * :attr:`id` - ID number of the pool.
    * :attr:`name` - A short name.
    * :attr:`description` - A longer description of the pool.
    * :attr:`default_type` - Default prefix type (see prefix types above.
    * :attr:`ipv4_default_prefix_length` - Default prefix length of IPv4 prefixes.
    * :attr:`ipv6_default_prefix_length` - Default prefix length of IPv6 prefixes.

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
import exceptions
import logging
import psycopg2
import psycopg2.extras
import shlex
import socket
import re
import IPy


_operation_map = {
    'and': 'AND',
    'or': 'OR',
    'equals': '=',
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
        """Create the INET type and an Inet adapter."""
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
            socket.inet_aton(ip)
        except socket.error:
            return False
        except exceptions.UnicodeEncodeError:
            return False
        return True



    def _is_ipv6(self, ip):
        """ Return true if given arg is a valid IPv6 address
        """

        try:
            socket.inet_pton(socket.AF_INET6, ip)
        except socket.error, UnicodeEncodeError:
            return False
        except exceptions.UnicodeEncodeError:
            return False
        return True



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
        except psycopg2.Error, e:
            self._logger.error("pgsql: %s" % e)
            raise NipapError("Backend unable to connect to database")
        except psycopg2.Warning, w:
            self._logger.warning('pgsql: %s' % w)



    def _execute(self, sql, opt=None, callno = 0):
        """ Execute query, catch and log errors.
        """

        self._logger.debug("SQL: " + sql + "  params: " + str(opt))
        try:
            self._curs_pg.execute(sql, opt)
        except psycopg2.InternalError, e:
            self._con_pg.rollback()

            # FIXME: move logging
            estr = "Internal database error: %s" % e
            self._logger.error(estr)

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
            if len(str(e).split(":")) < 2:
                raise NipapError(e)
            code = str(e).split(":", 1)[0]
            try:
                int(code)
            except:
                raise NipapError(e)

            text = str(e).splitlines()[0].split(":", 1)[1]

            if code == '1200':
                raise NipapValueError(text)

            raise NipapError(str(e))

        except psycopg2.IntegrityError, e:
            self._con_pg.rollback()

            # this is a duplicate key error
            if e.pgcode == "23505":
                # figure out which column it is and retrieve the database
                # description for that column
                m = re.match(r'.*"([^"]+)"', e.pgerror)
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
                    m = re.match(r'.*=\(([^)]+)\) already exists.', e.pgerror.splitlines()[1])
                    if m is not None:
                        column_value = m.group(1)
                except:
                    pass
                else:
                    raise NipapDuplicateError("Duplicate value for '" + column_desc + "', the value '" + column_value + "' is already in use.")

                raise NipapDuplicateError("Duplicate value for '" + column_desc + "', the value you have inputted is already in use.")

            raise NipapError(str(e))

        except psycopg2.DataError, e:
            self._con_pg.rollback()

            m = re.search('invalid cidr value: "([^"]+)"', e.pgerror)
            if m is not None:
                strict_prefix = str(IPy.IP(m.group(1), make_net = True))
                estr = "Invalid prefix (%s); bits set to right of mask. Network address for current mask: %s" % (m.group(1), strict_prefix)
                raise NipapValueError(estr)

            m = re.search('invalid input syntax for type (cidr|inet): "([^"]+)"', e.pgerror)
            if m is not None:
                estr = "Invalid syntax for prefix (%s)" % m.group(2)
                raise NipapValueError(estr)

            raise NipapValueError(str(e))

        except psycopg2.Error, e:
            try:
                self._con_pg.rollback()
            except psycopg2.Error:
                pass

            estr = "Unable to execute query: %s" % e
            self._logger.error(estr)

            # abort if we've already tried to reconnect
            if callno > 0:
                self._logger.error(estr)
                raise NipapError(estr)

            # reconnect to database and retry query
            self._logger.info("Reconnecting to database...")
            self._connect_db()

            return self._execute(sql, opt, callno + 1)

        except psycopg2.Warning, w:
            self._logger.warning(str(w))



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



    def add_vrf(self, auth, attr):
        """ Add a new VRF.

            * `auth` [BaseAuth]
                AAA options.
            * `attr` [vrf_attr]
                The news VRF's attributes.

            Add a VRF based on the values stored in the `attr` dict.

            Returns the internal database ID of the added VRF.
        """

        self._logger.debug("add_vrf called; attr: %s" % str(attr))

        # sanity check - do we have all attributes?
        req_attr = [ 'rt', 'name' ]
        self._check_attr(attr, req_attr, req_attr + [ 'description', ])

        insert, params = self._sql_expand_insert(attr)
        sql = "INSERT INTO ip_net_vrf " + insert

        self._execute(sql, params)
        vrf_id = self._lastrowid()

        # write to audit table
        audit_params = {
            'vrf_id': vrf_id,
            'vrf_rt': attr['rt'],
            'vrf_name': attr['name'],
            'username': auth.username,
            'authenticated_as': auth.authenticated_as,
            'full_name': auth.full_name,
            'authoritative_source': auth.authoritative_source,
            'description': 'Added VRF %s with attr: %s' % (attr['rt'], str(attr))
        }

        sql, params = self._sql_expand_insert(audit_params)
        self._execute('INSERT INTO ip_net_log %s' % sql, params)

        return vrf_id


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

        # write to audit table
        for v in vrfs:
            audit_params = {
                'vrf_id': v['id'],
                'vrf_rt': v['rt'],
                'vrf_name': v['name'],
                'username': auth.username,
                'authenticated_as': auth.authenticated_as,
                'full_name': auth.full_name,
                'authoritative_source': auth.authoritative_source,
                'description': 'Removed vrf %s' % v['rt']
            }
            sql, params = self._sql_expand_insert(audit_params)
            self._execute('INSERT INTO ip_net_log %s' % sql, params)



    def list_vrf(self, auth, spec = {}):
        """ Return a list of VRFs matching `spec`.

            * `auth` [BaseAuth]
                AAA options.
            * `spec` [vrf_spec]
                A VRF specification. If omitted, all VRFs are returned.

            Returns a list of dicts.
        """

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
            # no VRF specified - return the no-VRF VRF
            return { 'id': 0, 'rt': None, 'name': None }

        if len(vrf) > 0:
            return vrf[0]

        raise NipapNonExistentError('No matching VRF found.')




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
        allowed_attr = [ 'rt', 'name', 'description' ]
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

        self._execute(sql, params)

        # write to audit table
        for v in vrfs:
            audit_params = {
                'vrf_id': v['id'],
                'vrf_rt': v['rt'],
                'vrf_name': v['name'],
                'username': auth.username,
                'authenticated_as': auth.authenticated_as,
                'full_name': auth.full_name,
                'authoritative_source': auth.authoritative_source,
                'description': 'Edited VRF %s attr: %s' % (v['rt'], str(attr))
            }
            sql, params = self._sql_expand_insert(audit_params)
            self._execute('INSERT INTO ip_net_log %s' % sql, params)



    def search_vrf(self, auth, query, search_options = {}):
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

        #
        # sanitize search options and set default if option missing
        #

        # max_result
        if 'max_result' not in search_options:
            search_options['max_result'] = 50
        else:
            try:
                search_options['max_result'] = int(search_options['max_result'])
            except (ValueError, TypeError), e:
                raise NipapValueError('Invalid value for option' +
                    ''' 'max_result'. Only integer values allowed.''')

        # offset
        if 'offset' not in search_options:
            search_options['offset'] = 0
        else:
            try:
                search_options['offset'] = int(search_options['offset'])
            except (ValueError, TypeError), e:
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



    def smart_search_vrf(self, auth, query_str, search_options = {}, extra_query = None):
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



    def add_pool(self, auth, attr):
        """ Create a pool according to `attr`.

            * `auth` [BaseAuth]
                AAA options.
            * `attr` [pool_attr]
                A dict containing the attributes the new pool should have.

            Returns ID of the added pool.
        """

        self._logger.debug("add_pool called; attrs: %s" % str(attr))

        # sanity check - do we have all attributes?
        req_attr = ['name', 'description', 'default_type']
        self._check_pool_attr(attr, req_attr)

        insert, params = self._sql_expand_insert(attr)
        sql = "INSERT INTO ip_net_pool " + insert

        self._execute(sql, params)
        pool_id = self._lastrowid()

        # write to audit table
        audit_params = {
            'pool_id': pool_id,
            'pool_name': attr['name'],
            'username': auth.username,
            'authenticated_as': auth.authenticated_as,
            'full_name': auth.full_name,
            'authoritative_source': auth.authoritative_source,
            'description': 'Added pool %s with attr: %s' % (attr['name'], str(attr))
        }
        sql, params = self._sql_expand_insert(audit_params)
        self._execute('INSERT INTO ip_net_log %s' % sql, params)

        return pool_id



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
        audit_params = {
            'username': auth.username,
            'authenticated_as': auth.authenticated_as,
            'full_name': auth.full_name,
            'authoritative_source': auth.authoritative_source,
        }
        for p in pools:
            audit_params['pool_id'] = p['id'],
            audit_params['pool_name'] = p['name'],
            audit_params['description'] = 'Removed pool %s' % p['name']

            sql, params = self._sql_expand_insert(audit_params)
            self._execute('INSERT INTO ip_net_log %s' % sql, params)



    def list_pool(self, auth, spec = {}):
        """ Return a list of pools.

            * `auth` [BaseAuth]
                AAA options.
            * `spec` [pool_spec]
                Specifies what pool(s) to list. Of omitted, all will be listed.

            Returns a list of dicts.
        """

        self._logger.debug("list_pool called; spec: %s" % str(spec))

        sql = """SELECT DISTINCT (po.id),
                        po.id,
                        po.name,
                        po.description,
                        po.default_type,
                        po.ipv4_default_prefix_length,
                        po.ipv6_default_prefix_length,
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


    def _check_pool_attr(self, attr, req_attr = []):
        """ Check pool attributes.
        """

        # check attribute names
        allowed_attr = [
                'name',
                'default_type',
                'description',
                'ipv4_default_prefix_length',
                'ipv6_default_prefix_length'
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

        self._execute(sql, params)

        # write to audit table
        audit_params = {
            'username': auth.username,
            'authenticated_as': auth.authenticated_as,
            'full_name': auth.full_name,
            'authoritative_source': auth.authoritative_source
        }
        for p in pools:
            audit_params['pool_id'] = p['id']
            audit_params['pool_name'] = p['name']
            audit_params['description'] = 'Edited pool %s attr: %s' % (p['name'], str(attr))

            sql, params = self._sql_expand_insert(audit_params)
            self._execute('INSERT INTO ip_net_log %s' % sql, params)



    def search_pool(self, auth, query, search_options = {}):
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

        #
        # sanitize search options and set default if option missing
        #

        # max_result
        if 'max_result' not in search_options:
            search_options['max_result'] = 50
        else:
            try:
                search_options['max_result'] = int(search_options['max_result'])
            except (ValueError, TypeError), e:
                raise NipapValueError('Invalid value for option' +
                    ''' 'max_result'. Only integer values allowed.''')

        # offset
        if 'offset' not in search_options:
            search_options['offset'] = 0
        else:
            try:
                search_options['offset'] = int(search_options['offset'])
            except (ValueError, TypeError), e:
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



    def smart_search_pool(self, auth, query_str, search_options = {}, extra_query = None):
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

        self._logger.debug("smart_search_pool query string: %s" % query_str)

        if query_str is None:
            raise NipapValueError("'query_string' must not be None")

        # find query parts
        # XXX: notice the ugly workarounds for shlex not supporting Unicode
        query_str_parts = []
        try:
            for part in shlex.split(query_str.encode('utf-8')):
                query_str_parts.append({ 'string': part.decode('utf-8') })
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
            prefix_attr['node'] = 'inp.node'
            prefix_attr['country'] = 'inp.country'
            prefix_attr['order_id'] = 'inp.order_id'
            prefix_attr['vrf_id'] = 'inp.vrf_id'
            prefix_attr['vrf_rt'] = 'vrf.rt'
            prefix_attr['vrf_name'] = 'vrf.name'
            prefix_attr['external_key'] = 'inp.external_key'
            prefix_attr['authoritative_source'] = 'inp.authoritative_source'
            prefix_attr['alarm_priority'] = 'inp.alarm_priority'
            prefix_attr['monitor'] = 'inp.monitor'

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



    def add_prefix(self, auth, attr, args = {}):
        """ Add a prefix and return its ID.

            * `auth` [BaseAuth]
                AAA options.
            * `attr` [prefix_attr]
                Prefix attributes.
            * `args` [add_prefix_args]
                Arguments explaining how the prefix should be allocated.

            Returns ID of the added prefix.

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
                    pool = self._get_pool(auth, { 'name': attr['pool_name'] })

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
        allowed_attr = [
            'authoritative_source', 'prefix', 'description',
            'comment', 'pool_id', 'node', 'type', 'country',
            'order_id', 'vrf_id', 'alarm_priority', 'monitor', 'external_key' ]
        self._check_attr(attr, req_attr, allowed_attr)
        if ('description' not in attr) and ('node' not in attr):
            raise NipapMissingInputError('Either description or node must be specified.')

        insert, params = self._sql_expand_insert(attr)
        sql = "INSERT INTO ip_net_plan " + insert

        self._execute(sql, params)
        prefix_id = self._lastrowid()

        # write to audit table
        audit_params = {
            'vrf_id': vrf['id'],
            'vrf_rt': vrf['rt'],
            'vrf_name': vrf['name'],
            'prefix_id': prefix_id,
            'prefix_prefix': attr['prefix'],
            'username': auth.username,
            'authenticated_as': auth.authenticated_as,
            'full_name': auth.full_name,
            'authoritative_source': auth.authoritative_source,
            'description': 'Added prefix %s with attr: %s' % (attr['prefix'], str(attr))
        }
        sql, params = self._sql_expand_insert(audit_params)
        self._execute('INSERT INTO ip_net_log %s' % sql, params)

        if pool['id'] is not None:
            audit_params['pool_id'] = pool['id']
            audit_params['pool_name'] = pool['name']
            audit_params['description'] = 'Pool %s expanded with prefix %s' % (pool['name'], attr['prefix'])

            sql, params = self._sql_expand_insert(audit_params)
            self._execute('INSERT INTO ip_net_log %s' % sql, params)

        return prefix_id



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
                    pool = self._get_pool(auth, { 'name': attr['pool_name'] })

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
            'comment', 'pool_id', 'node', 'type', 'country',
            'order_id', 'vrf_id', 'alarm_priority', 'monitor',
            'external_key' ]

        self._check_attr(attr, [], allowed_attr)

        prefixes = self.list_prefix(auth, spec)
        where, params1 = self._expand_prefix_spec(spec.copy())
        update, params2 = self._sql_expand_update(attr)
        params = dict(params2.items() + params1.items())

        sql = "UPDATE ip_net_plan SET " + update + " WHERE " + where

        self._execute(sql, params)

        # write to audit table
        audit_params = {
            'username': auth.username,
            'authenticated_as': auth.authenticated_as,
            'full_name': auth.full_name,
            'authoritative_source': auth.authoritative_source,
            'vrf_id': vrf['id'],
            'vrf_rt': vrf['rt'],
            'vrf_name': vrf['name']
        }

        for p in prefixes:
            audit_params['vrf_id'] = p['vrf_id']
            audit_params['vrf_rt'] = p['vrf_rt']
            audit_params['vrf_name'] = p['vrf_name']
            audit_params['prefix_id'] = p['id']
            audit_params['prefix_prefix'] = p['prefix']
            audit_params['description'] = 'Edited prefix %s attr: %s' % (p['prefix'], str(attr))
            sql, params = self._sql_expand_insert(audit_params)
            self._execute('INSERT INTO ip_net_log %s' % sql, params)

            # Only add to log if something was changed
            if p['pool_id'] != pool['id']:

                audit_params2 = {
                    'prefix_id': p['id'],
                    'prefix_prefix': p['prefix'],
                    'vrf_id': p['vrf_id'],
                    'vrf_rt': p['vrf_rt'],
                    'vrf_name': p['vrf_name'],
                    'username': auth.username,
                    'authenticated_as': auth.authenticated_as,
                    'full_name': auth.full_name,
                    'authoritative_source': auth.authoritative_source,
                }

                # If pool ID set, pool was expanded
                if pool['id'] is not None:

                    audit_params2['pool_id'] = pool['id']
                    audit_params2['pool_name'] = pool['name']
                    audit_params2['description'] = 'Expanded pool %s with prefix %s' % (pool['name'], p['prefix'])

                    sql, params = self._sql_expand_insert(audit_params2)
                    self._execute('INSERT INTO ip_net_log %s' % sql, params)

                # if prefix had pool set previously, prefix was removed from that pool
                if p['pool_id'] is not None:

                    pool2 = self._get_pool(auth, { 'id': p['pool_id'] })

                    audit_params2['pool_id'] = pool2['id']
                    audit_params2['pool_name'] = pool2['name']
                    audit_params2['description'] = 'Removed prefix %s from pool %s' % (p['prefix'], pool2['name'])

                    sql, params = self._sql_expand_insert(audit_params2)
                    self._execute('INSERT INTO ip_net_log %s' % sql, params)



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
                if self._get_afi(p) == args['family']:
                    prefixes.append(p)
            if len(prefixes) == 0:
                raise NipapInputError('No prefixes of family %d in pool' % args['family'])
            if 'prefix_length' not in args:
                if args['family'] == 4:
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
            wpl = args['prefix_length']

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
            inp.node,
            inp.comment,
            pool.id AS pool_id,
            pool.name AS pool_name,
            inp.type,
            inp.indent,
            inp.country,
            inp.order_id,
            inp.external_key,
            inp.authoritative_source,
            inp.alarm_priority,
            inp.monitor
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
        audit_params = {
            'username': auth.username,
            'authenticated_as': auth.authenticated_as,
            'full_name': auth.full_name,
            'authoritative_source': auth.authoritative_source
        }
        for p in prefixes:
            audit_params['prefix_id'] = p['id']
            audit_params['prefix_prefix'] = p['prefix']
            audit_params['description'] = 'Removed prefix %s' % p['prefix']
            audit_params['vrf_id'] = p['vrf_id']
            audit_params['vrf_rt'] = p['vrf_rt']
            audit_params['vrf_name'] = p['vrf_name']
            sql, params = self._sql_expand_insert(audit_params)
            self._execute('INSERT INTO ip_net_log %s' % sql, params)

            if p['pool_id'] is not None:
                pool = self._get_pool(auth, { 'id': p['pool'] })
                audit_params2 = {
                    'pool_id': pool['id'],
                    'pool_name': pool['name'],
                    'prefix_id': p['id'],
                    'prefix_prefix': p['prefix'],
                    'description': 'Prefix %s removed from pool %s' % (p['prefix'], pool['name']),
                    'username': auth.username,
                    'authenticated_as': auth.authenticated_as,
                    'full_name': auth.full_name,
                    'authoritative_source': auth.authoritative_source
                }
                sql, params = self._sql_expand_insert(audit_params2)
                self._execute('INSERT INTO ip_net_log %s' % sql, params)



    def search_prefix(self, auth, query, search_options = {}):
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
            except (ValueError, TypeError), e:
                raise NipapValueError('Invalid value for option' +
                    ''' 'parent_depth'. Only integer values allowed.''')

        # children_depth
        if 'children_depth' not in search_options:
            search_options['children_depth'] = 0
        else:
            try:
                search_options['children_depth'] = int(search_options['children_depth'])
            except (ValueError, TypeError), e:
                raise NipapValueError('Invalid value for option' +
                    ''' 'children_depth'. Only integer values allowed.''')

        # max_result
        if 'max_result' not in search_options:
            search_options['max_result'] = 50
        else:
            try:
                search_options['max_result'] = int(search_options['max_result'])
            except (ValueError, TypeError), e:
                raise NipapValueError('Invalid value for option' +
                    ''' 'max_result'. Only integer values allowed.''')

        # offset
        if 'offset' not in search_options:
            search_options['offset'] = 0
        else:
            try:
                search_options['offset'] = int(search_options['offset'])
            except (ValueError, TypeError), e:
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
        if search_options['parents_depth'] >= 0:
            parents_selector = 'AND p1.indent BETWEEN p2.indent - %d AND p1.indent' % search_options['parents_depth']
        else:
            parents_selector = ''

        if search_options['children_depth'] >= 0:
            children_selector = 'AND p1.indent BETWEEN p2.indent AND p2.indent + %d' % search_options['children_depth']
        else:
            children_selector = ''

        if search_options['include_all_parents']:
            where_parents = ''
        else:
            where_parents = parents_selector

        if search_options['include_all_children']:
            where_children = ''
        else:
            where_children = children_selector

        if search_options['parent_prefix']:
            vrf_id = 0
            if parent_prefix['vrf_id']:
                vrf_id = parent_prefix['vrf_id']
            query_parent_prefix = " (p1.vrf_id = %s AND iprange(p1.prefix) <<= iprange('%s') AND p1.indent <= %s) " % (vrf_id, parent_prefix['prefix'], parent_prefix['indent'] + 1)
            join_parent_prefix = " AND %s" % query_parent_prefix
            where_parent_prefix = " OR %s" % query_parent_prefix
        else:
            join_parent_prefix = ''
            where_parent_prefix = ''

        display = '(p1.prefix << p2.display_prefix OR p2.prefix <<= p1.prefix %s) OR (p2.prefix >>= p1.prefix %s)' % (parents_selector, children_selector)

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
        node,
        pool_id,
        pool_name,
        type,
        indent,
        country,
        order_id,
        external_key,
        authoritative_source,
        alarm_priority,
        monitor,
        CASE
            WHEN type = 'host'
                THEN 0
            WHEN type = 'assignment'
                THEN CASE
                    WHEN COUNT(1) OVER (PARTITION BY display_prefix::cidr) > 1
                        -- do not include the parent prefix in count
                        THEN COUNT(1) OVER (PARTITION BY display_prefix::cidr) - 1
                    ELSE -2
                END
            ELSE -2
        END AS children
    FROM (
        SELECT DISTINCT ON(vrf.rt, p1.prefix) p1.id,
            p1.prefix,
            p1.display_prefix,
            p1.description,
            p1.comment,
            p1.node,
            pool.id AS pool_id,
            pool.name AS pool_name,
            p1.type,
            p1.indent,
            p1.country,
            p1.order_id,
            p1.external_key,
            p1.authoritative_source,
            p1.alarm_priority,
            p1.monitor,
            vrf.id AS vrf_id,
            vrf.rt AS vrf_rt,
            vrf.name AS vrf_name,
            masklen(p1.prefix) AS prefix_length,
            family(p1.prefix) AS family,
            (""" + display + """) AS display,
            CASE WHEN p1.prefix = p2.prefix THEN true ELSE false END AS match
            FROM ip_net_plan AS p1
            JOIN ip_net_plan AS p2 ON
            (
                (
                    (p1.vrf_id = p2.vrf_id)
                    AND
                    (
                        -- Join in the parents which were requested
                        (iprange(p1.prefix) >>= iprange(p2.prefix) """ + where_parents + """)
                        OR
                        -- Join in the children which were requested
                        (iprange(p1.prefix) << iprange(p2.prefix) """ + where_children + """)
                        OR
                        -- Join in all neighbors to the matched prefix
                        (iprange(p1.prefix) << iprange(p2.display_prefix::cidr) AND p1.indent = p2.indent)
                    )
                )
                -- Join on the parent_prefix in addition to having it in the
                -- WHERE part of the query as this speeds up the JOIN tremendously
                """ + join_parent_prefix + """
            )
            JOIN ip_net_vrf AS vrf ON (p1.vrf_id = vrf.id)
            LEFT JOIN ip_net_pool AS pool ON (p1.pool_id = pool.id)
            WHERE p2.id IN (
                SELECT inp.id FROM ip_net_plan AS inp JOIN ip_net_vrf AS vrf ON inp.vrf_id = vrf.id LEFT JOIN ip_net_pool AS pool ON inp.pool_id = pool.id
                    WHERE """ + where + """
                ORDER BY vrf_rt_order(vrf.rt) NULLS FIRST, prefix
                LIMIT """ + str(int(search_options['max_result']) + int(search_options['offset'])) + """
                )
                """ + where_parent_prefix + """
            ORDER BY vrf.rt, p1.prefix, CASE WHEN p1.prefix = p2.prefix THEN 0 ELSE 1 END OFFSET """  + str(search_options['offset']) + ") AS a ORDER BY vrf_rt_order(vrf_rt) NULLS FIRST, prefix"

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



    def smart_search_prefix(self, auth, query_str, search_options = {}, extra_query = None):
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

        self._logger.debug("smart_search_prefix query string: %s" % query_str)

        if query_str is None:
            raise NipapValueError("'query_string' must not be None")

        # find query parts
        # XXX: notice the ugly workarounds for shlex not supporting Unicode
        query_str_parts = []
        try:
            for part in shlex.split(query_str.encode('utf-8')):
                query_str_parts.append({ 'string': part.decode('utf-8') })
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

            # IPv4 prefix
            if self._get_afi(query_str_part['string']) == 4 and len(query_str_part['string'].split('/')) == 2:
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
                query_str_part['operator'] = 'equals'
                query_str_part['attribute'] = 'prefix'
                query_parts.append({
                    'operator': 'equals',
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
                query_str_part['operator'] = 'equals'
                query_str_part['attribute'] = 'prefix'
                query_parts.append({
                    'operator': 'equals',
                    'val1': 'prefix',
                    'val2': query_str_part['string']
                })

            # Description or comment
            # TODO: add an equal search for VRF here
            else:
                self._logger.debug("Query part '" + query_str_part['string'] + "' interpreted as desc/comment")
                query_str_part['interpretation'] = 'text'
                query_str_part['operator'] = 'regex'
                query_str_part['attribute'] = 'description or comment or node or order id'
                query_parts.append({
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



    def list_asn(self, auth, asn = {}):
        """ List AS numbers
        """

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



    def add_asn(self, auth, attr):
        """ Add AS number to NIPAP.

            * `auth` [BaseAuth]
                AAA options.
            * `attr` [asn_attr]
                ASN attributes.
        """

        self._logger.debug("add_asn called; attr: %s" % str(attr))

        # sanity check - do we have all attributes?
        req_attr = [ 'asn', ]
        allowed_attr = [ 'asn', 'name' ]
        self._check_attr(attr, req_attr, allowed_attr)

        insert, params = self._sql_expand_insert(attr)
        sql = "INSERT INTO ip_net_asn " + insert

        self._execute(sql, params)

        # write to audit table
        audit_params = {
            'username': auth.username,
            'authenticated_as': auth.authenticated_as,
            'full_name': auth.full_name,
            'authoritative_source': auth.authoritative_source,
            'description': 'Added ASN %s with attr: %s' % (attr['asn'], str(attr))
        }

        sql, params = self._sql_expand_insert(audit_params)
        self._execute('INSERT INTO ip_net_log %s' % sql, params)

        return int(attr['asn'])



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

        self._execute(sql, params)

        # write to audit table
        for a in asns:
            audit_params = {
                'username': auth.username,
                'authenticated_as': auth.authenticated_as,
                'full_name': auth.full_name,
                'authoritative_source': auth.authoritative_source
            }
            audit_params['description'] = 'Edited ASN %s attr: %s' % (str(a['asn']), str(attr))

            sql, params = self._sql_expand_insert(audit_params)
            self._execute('INSERT INTO ip_net_log %s' % sql, params)



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
            audit_params = {
                'username': auth.username,
                'authenticated_as': auth.authenticated_as,
                'full_name': auth.full_name,
                'authoritative_source': auth.authoritative_source,
                'description': 'Removed ASN %s' % str(a['asn'])
            }
            sql, params = self._sql_expand_insert(audit_params)
            self._execute('INSERT INTO ip_net_log %s' % sql, params)



    def search_asn(self, auth, query, search_options = {}):
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

        #
        # sanitize search options and set default if option missing
        #

        # max_result
        if 'max_result' not in search_options:
            search_options['max_result'] = 50
        else:
            try:
                search_options['max_result'] = int(search_options['max_result'])
            except (ValueError, TypeError), e:
                raise NipapValueError('Invalid value for option' +
                    ''' 'max_result'. Only integer values allowed.''')

        # offset
        if 'offset' not in search_options:
            search_options['offset'] = 0
        else:
            try:
                search_options['offset'] = int(search_options['offset'])
            except (ValueError, TypeError), e:
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



    def smart_search_asn(self, auth, query_str, search_options = {}, extra_query = None):
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

        self._logger.debug("smart_search_asn called; query_str: %s" % query_str)

        if query_str is None:
            raise NipapValueError("'query_string' must not be None")

        # find query parts
        # XXX: notice the ugly workarounds for shlex not supporting Unicode
        query_str_parts = []
        try:
            for part in shlex.split(query_str.encode('utf-8')):
                query_str_parts.append({ 'string': part.decode('utf-8') })
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
