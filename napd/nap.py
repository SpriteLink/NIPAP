# vim: et ts=4 :
import logging
import psycopg2
import psycopg2.extras
import shlex
import socket
import re


_operation_map = {
    'and': 'AND',
    'or': 'OR',
    'equals': '=',
    'not_equals': '!=',
    'like': 'LIKE',
    'regex_match': '~*',
    'regex_not_match': '!~*',
    'contains': '>>',
    'contains_equals': '>>=',
    'contained_within': '<<',
    'contained_within_equals': '<<='
    }


class Inet(object):
    """ This works around a bug in psycopg2 version somewhere before 2.4.
        The __init__ function in the original class is broken and so this is merely a copy with the bug fixed.

        Wrap a string to allow for correct SQL-quoting of inet values.

        Note that this adapter does NOT check the passed value to make
        sure it really is an inet-compatible address but DOES call adapt()
        on it to make sure it is impossible to execute an SQL-injection
        by passing an evil value to the initializer.
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



class Nap:
    """ Network Address Planner
    """

    _logger = None
    _con_pg = None
    _curs_pg =  None

    def __init__(self):
        """ Constructor.

            Creates database connections n' stuff, yo.
        """

        self._logger = logging.getLogger(self.__class__.__name__)
        self._logger.debug("Initialising NAP")

        # Create database connection
        try:
            self._con_pg = psycopg2.connect("host='localhost' dbname='nap' user='napd' password='dpan'")
            self._con_pg.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            self._curs_pg = self._con_pg.cursor(cursor_factory=psycopg2.extras.DictCursor)
            self.register_inet()
        except psycopg2.Error, e:
            estr = str(e)
            self._logger.error(estr)
            raise NapError(estr)
        except psycopg2.Warning, w:
            self._logger.warning(str(w))


    #
    # Miscellaneous help functions
    #

    def register_inet(oid=None, conn_or_curs=None):
        """Create the INET type and an Inet adapter."""
        from psycopg2 import extensions as _ext
        if not oid: oid = 869
        _ext.INET = _ext.new_type((oid, ), "INET",
                lambda data, cursor: data and Inet(data) or None)
        _ext.register_type(_ext.INET, conn_or_curs)
        return _ext.INET



    def _is_ipv4(self, ip):
        """ Return true if given arg is a valid IPv4 address
        """

        try:
            socket.inet_aton(ip)
        except socket.error:
            return False
        return True



    def _is_ipv6(self, ip):
        """ Return true if given arg is a valid IPv6 address
        """

        try:
            socket.inet_pton(socket.AF_INET6, ip)
        except socket.error:
            return False
        return True



    def _get_afi(self, ip):
        """ Return address-family (4 or 6) for IP or None if invalid address
        """

        parts = str(ip).split("/")
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
            except:
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

    def _execute(self, sql, opt=None):
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
                raise NapError(e)
            code = str(e).split(":", 1)[0]
            try:
                int(code)
            except:
                raise NapError(e)

            text = str(e).split(":", 1)[1]

            if code == '1200':
                raise NapValueError(text)
            else:
                raise NapError()
        except psycopg2.IntegrityError, e:
            self._con_pg.rollback()

            if e.pgcode == "23505":
                raise NapDuplicateError("Objects primary keys already exist")

        except psycopg2.Error, e:
            self._con_pg.rollback()
            estr = "Unable to execute query: %s" % e
            self._logger.error(estr)
            raise NapError(estr)
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

        sql = ' AND '.join(col_prefix + key + ' = %(' + key_prefix + key + ')s' for key in spec)
        params = {}
        for key in spec:
            params[key_prefix + key] = spec[key]

        return sql, params



    # TODO: make this more generic and use for testing of spec too?
    def _check_attr(self, attr, req_attr, allowed_attr):
        """
        """
        if type(attr) is not dict:
            raise NapInputError("invalid input type, must be dict")

        for a in req_attr:
            if not a in attr:
                raise NapMissingInputError("missing attribute %s" % a)
        for a in attr:
            if a not in allowed_attr:
                raise NapExtraneousInputError("extraneous attribute %s" % a)



    #
    # Schema functions
    #
    def _expand_schema_spec(self, spec):
        """ Expand schema specification to SQL.

            id [integer]
                internal database id of schema

            name [string]
                name of schema

            A schema is referenced either by its internal database id or by its
            name. Both are used for exact matching and so no wildcard or
            regular expressions are allowed. Only one key may be used and an
            error will be thrown if both id and name is specified.
        """

        if type(spec) is not dict:
            raise NapInputError("schema specification must be a dict")

        allowed_values = ['id', 'name']
        for a in spec:
            if a not in allowed_values:
                raise NapExtraneousInputError("extraneous specification key %s" % a)

        if 'id' in spec:
            if long(spec['id']) != spec['id']:
                raise NapValueError("schema specification key 'id' must be an integer")
            if 'name' in spec:
                raise NapExtraneousInputError("schema specification contain both 'id' and 'key', specify schema id or name")
        elif 'name' in spec:
            if type(spec['name']) != type(''):
                raise NapValueError("schema specification key 'name' must be a string")
            if 'id' in spec:
                raise NapExtraneousInputError("schema specification contain both 'id' and 'key', specify schema id or name")
        else:
            raise NapMissingInputError('missing both id and name in schema spec')

        where, params = self._sql_expand_where(spec, 'spec_')

        return where, params



    def _translate_pool_spec(self, schema_spec, spec):
        """ Expand 'pool_name' or 'pool_id'.

            Translates 'pool_name' or 'pool_id' element in spec
            to a 'pool' element containing the pool ID.
        """

        if 'pool_id' in spec and 'pool_name' in spec:
            raise NapExtraneousInputError("specification contain both 'id' and 'name', specify pool id or name")

        if 'pool_id' in spec:
            pool = self.list_pool(schema_spec, { 'id': spec['pool_id'] })
            if pool == []:
                raise NapInputError("non-existing pool specified")
            spec['pool'] = pool[0]['id']
            del(spec['pool_id'])
        elif 'pool_name' in spec:
            if 'schema' not in spec:
                raise NapMissingInputError("schema needs to be specified together with 'pool_name'")

            pool = self.list_pool(schema_spec, { 'name': spec['pool_name'] })
            if pool == []:
                raise NapInputError("non-existing pool specified")
            spec['pool'] = pool[0]['id']
            del(spec['pool_name'])
        else:
            raise NapInputError("Missing pool, add pool_id or pool_name to spec!")

        return spec



    def add_schema(self, attr):
        """ Add a new network schema.

            attr [schema_attr]
                schema_attr, attributes for a schema

            Add a schema based on the values stored in the inputted attr dict.
        """

        self._logger.debug("add_schema called; attr: %s" % str(attr))

        # sanity check - do we have all attributes?
        req_attr = [ 'name', 'description']
        self._check_attr(attr, req_attr, req_attr)

        insert, params = self._sql_expand_insert(attr)
        sql = "INSERT INTO ip_net_schema " + insert

        self._execute(sql, params)
        return self._lastrowid()



    def remove_schema(self, spec):
        """ Remove a schema.

            spec [schema_spec]
                a schema specification, please see documentation for
                _expand_schema_spec for details

            Remove a schema matching the spec parameter.
        """

        self._logger.debug("remove_schema called; spec: %s" % str(spec))

        where, params = self._expand_schema_spec(spec)

        sql = "DELETE FROM ip_net_schema WHERE %s" % where
        self._execute(sql, params)



    def list_schema(self, spec=None):
        """ List schemas.
        """

        self._logger.debug("list_schema called; spec: %s" % str(spec))

        sql = "SELECT * FROM ip_net_schema"
        params = list()

        if spec is not None:
            where, params = self._expand_schema_spec(spec)
            sql += " WHERE " + where

        sql += " ORDER BY name ASC"

        self._execute(sql, params)

        res = list()
        for row in self._curs_pg:
            res.append(dict(row))

        return res



    def _get_schema(self, spec):
        """ Get a schema.

            Shorthand function to reduce code in the functions below, since
            more or less all of them needs to perform the actions that are
            specified here.

            The major difference is that an exception is raised if no schema
            matching the spec is found.
        """

        schema = self.list_schema(spec)
        if len(schema) == 0:
            raise NapInputError("non-existing schema specified")
        return schema[0]



    def edit_schema(self, spec, attr):
        """ Edit a schema.
        """

        self._logger.debug("edit_schema called; spec: %s  attr: %s" %
                (str(spec), str(attr)))

        # sanity check - do we have all attributes?
        req_attr = [ 'name', 'description']
        allowed_attr = [ 'name', 'description' ]
        self._check_attr(attr, req_attr, allowed_attr)

        where, params1 = self._expand_schema_spec(spec)
        update, params2 = self._sql_expand_update(attr)
        params = dict(params2.items() + params1.items())

        sql = "UPDATE ip_net_schema SET " + update
        sql += " WHERE " + where

        self._execute(sql, params)



    #
    # Pool functions
    #
    def _expand_pool_spec(self, spec):
        """ Expand pool specification to sql.
        """

        if type(spec) is not dict:
            raise NapInputError("pool specification must be a dict")

        allowed_values = ['id', 'name', 'schema']
        for a in spec:
            if a not in allowed_values:
                raise NapExtraneousInputError("extraneous specification key %s" % a)

        if 'schema' not in spec:
            raise NapMissingInputError('missing schema')

        if 'id' in spec:
            if long(spec['id']) != spec['id']:
                raise NapValueError("pool specification key 'id' must be an integer")
            if spec != { 'id': spec['id'], 'schema': spec['schema'] }:
                raise NapExtraneousInputError("pool specification with 'id' should not contain anything else")
        elif 'name' in spec:
            if type(spec['name']) != type(''):
                raise NapValueError("pool specification key 'name' must be a string")
            if 'id' in spec:
                raise NapExtraneousInputError("pool specification contain both 'id' and 'name', specify pool id or name")

        where, params = self._sql_expand_where(spec, 'spec_', 'po.')

        return where, params



    def add_pool(self, schema_spec, attr):
        """ Add a pool.

            schema_spec specifies which schema the pool should belong
            to, attr contains the pool's attributes.
        """

        self._logger.debug("add_pool called; spec: %s" % str(attr))

        # populate 'schema' with correct id
        attr['schema'] = self._get_schema(schema_spec)['id']

        # sanity check - do we have all attributes?
        req_attr = ['name', 'schema', 'description', 'default_type']
        allowed_attr = req_attr + ['ipv4_default_prefix_length', 'ipv6_default_prefix_length']
        self._check_attr(attr, req_attr, allowed_attr)

        insert, params = self._sql_expand_insert(attr)
        sql = "INSERT INTO ip_net_pool " + insert

        self._execute(sql, params)
        return self._lastrowid()



    def remove_pool(self, schema_spec, spec):
        """ Remove a pool.
        """

        self._logger.debug("remove_pool called; spec: %s" % str(spec))

        # populate 'schema' with correct id
        spec['schema'] = self._get_schema(schema_spec)['id']

        where, params = self._expand_pool_spec(spec)

        sql = "DELETE FROM ip_net_pool AS po WHERE %s" % where
        self._execute(sql, params)



    def list_pool(self, schema_spec, spec = {}):
        """ List pools.
        """

        self._logger.debug("list_pool called; spec: %s" % str(spec))

        sql = """SELECT po.id,
                        po.name,
                        po.description,
                        po.schema,
                        po.default_type,
                        po.ipv4_default_prefix_length,
                        po.ipv6_default_prefix_length,
                        (SELECT array_agg(prefix::text) FROM (SELECT prefix FROM ip_net_plan WHERE pool=po.id ORDER BY prefix) AS a) AS prefixes
                FROM ip_net_pool AS po """
        params = list()

        # populate 'schema' with correct id
        spec['schema'] = self._get_schema(schema_spec)['id']

        # expand spec
        where, params = self._expand_pool_spec(spec)
        if len(where) > 0:
            sql += " WHERE " + where

        sql += " ORDER BY name"

        self._execute(sql, params)

        res = list()
        for row in self._curs_pg:
            res.append(dict(row))

        return res



    def edit_pool(self, schema_spec, spec, attr):
        """ Edit pool.
        """

        self._logger.debug("edit_pool called; spec: %s attr: %s" %
                (str(spec), str(attr)))

        if ('id' not in spec and 'name' not in spec) or ( 'id' in spec and 'name' in spec ):
            raise NapMissingInputError('''pool spec must contain either 'id' or 'name' ''')

        allowed_attr = [
                'name',
                'default_type',
                'description',
                'ipv4_default_prefix_length',
                'ipv6_default_prefix_length'
                ]
        self._check_attr(attr, [], allowed_attr)

        # populate 'schema' with correct id
        spec['schema'] = self._get_schema(schema_spec)['id']

        where, params1 = self._expand_pool_spec(spec)
        update, params2 = self._sql_expand_update(attr)
        params = dict(params2.items() + params1.items())

        sql = "UPDATE ip_net_pool SET " + update
        sql += " FROM ip_net_pool AS po WHERE ip_net_pool.id = po.id AND " + where

        self._execute(sql, params)



    #
    # PREFIX FUNCTIONS
    #
    def _expand_prefix_spec(self, spec):
        """ Expand prefix specification to SQL.
        """

        # sanity checks
        if type(spec) is not dict:
            raise NapInputError('invalid prefix specification')

        if 'schema' not in spec:
            raise NapMissingInputError('missing schema')

        allowed_keys = ['id', 'family', 'schema',
            'type', 'pool_name', 'pool_id', 'prefix']
        for key in spec.keys():
            if key not in allowed_keys:
                raise NapExtraneousInputError("Key '" + key + "' not allowed in prefix spec.")

        where = ""
        params = {}

        # if we have id, no other input is needed
        if 'id' in spec:
            if spec != {'id': spec['id'], 'schema': spec['schema']}:
                raise NapExtraneousInputError("If id specified, no other keys are allowed.")

        where, params = self._sql_expand_where(spec)

        self._logger.debug("where: %s params: %s" % (where, str(params)))
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


        if type(query['val1']) == dict and type(query['val2']) == dict:
            # Sub expression, recurse!
            # add parantheses

            sub_where1, opt1 = self._expand_prefix_query(query['val1'], table_name)
            sub_where2, opt2 = self._expand_prefix_query(query['val2'], table_name)
            try:
                where += str(" (%s %s %s ) " % (sub_where1, _operation_map[query['operator']], sub_where2) )
            except KeyError:
                raise NoSuchOperatorError("no such operator %s" % str(query['operator']))

            opt += opt1
            opt += opt2

        else:

            # TODO: raise exception if someone passes one dict and one "something else"?

            # val1 is variable, val2 is string.
            prefix_attr = dict()
            prefix_attr['prefix'] = 'prefix'
            prefix_attr['schema'] = 'schema'
            prefix_attr['description'] = 'description'
            prefix_attr['pool'] = 'pool'
            prefix_attr['family'] = 'family'
            prefix_attr['comment'] = 'comment'
            prefix_attr['type'] = 'type'
            prefix_attr['country'] = 'country'
            prefix_attr['span_order'] = 'span_order'
            prefix_attr['authoritative_source'] = 'authoritative_source'
            prefix_attr['alarm_priority'] = 'alarm_priority'

            if query['val1'] not in prefix_attr:
                raise NapInputError('Search variable \'%s\' unknown' % str(query['val1']))

            # build where caluse
            try:
                self._logger.debug("hey: %s" % table_name)
                where = str(" %s%s %s %%s " %
                    ( col_prefix, prefix_attr[query['val1']],
                    _operation_map[query['operator']] )
                )
            except KeyError:
                raise NapNoSuchOperatorError("No such operation %s" % query['operator'])
            opt.append(query['val2'])

        return where, opt



    def add_prefix(self, schema_spec, attr, args = {}):
        """ Add a prefix.
        """

        self._logger.debug("add_prefix called; attr: %s; args: %s" % (str(attr), str(args)))

        # populate 'schema' with correct id
        attr['schema'] = self._get_schema(schema_spec)['id']

        # sanity checks
        if 'prefix' in attr:
            if 'from-pool' in args or 'from-prefix' in args:
                raise NapExtraneousInputError("specify 'prefix' or 'from-prefix' or 'from-pool'")
        else:
            if ('from-pool' not in args and 'from-prefix' not in args) or ('from-pool' in args and 'from-prefix' in args):
                raise NapExtraneousInputError("specify 'prefix' or 'from-prefix' or 'from-pool'")
            res = self.find_free_prefix(schema_spec, args)
            if res != []:
                attr['prefix'] = res[0]
            else:
                # TODO: Raise other exception?
                raise NapNonExistentError("no free prefix found")

        if 'pool_id' in attr or 'pool_name' in attr:
            attr = self._translate_pool_spec(schema_spec, attr)

        # do we have all attributes?
        req_attr = [ 'prefix', 'schema', 'description' ]
        allowed_attr = [
            'authoritative_source', 'prefix', 'schema', 'description',
            'comment', 'pool', 'node', 'type', 'country',
            'span_order', 'alarm_priority']
        self._check_attr(attr, req_attr, allowed_attr)

        insert, params = self._sql_expand_insert(attr)
        sql = "INSERT INTO ip_net_plan " + insert

        self._execute(sql, params)
        prefix_id = self._lastrowid()

        return prefix_id



    def edit_prefix(self, schema_spec, spec, attr):
        """ Edit prefix.
        """

        self._logger.debug("edit_prefix called; spec: %s attr: %s" %
                (str(spec), str(attr)))

        allowed_attr = [
            'authoritative_source', 'prefix', 'description',
            'comment', 'pool', 'node', 'type', 'country',
            'span_order', 'alarm_priority']

        self._check_attr(attr, [], allowed_attr)

        spec['schema'] = self._get_schema(schema_spec)['id']

        where, params1 = self._expand_prefix_spec(spec)
        update, params2 = self._sql_expand_update(attr)
        params = dict(params2.items() + params1.items())

        sql = "UPDATE ip_net_plan SET " + update + " WHERE " + where

        self._execute(sql, params)



    def find_free_prefix(self, schema_spec, args):
        """ Find a free prefix

            Arguments:
        """

        # input sanity
        if type(args) is not dict:
            raise NapInputError("invalid input, please provide dict as args")

        args['schema'] = self._get_schema(schema_spec)['id']

        # TODO: find good default value for max_num
        # TODO: let max_num be configurable from configuration file
        max_count = 1000
        if 'count' in args:
            if int(args['count']) > max_count:
                raise NapValueError("count over the maximum result size")
        else:
            args['count'] = 1

        if 'from-pool' in args:
            if 'from-prefix' in args:
                raise NapInputError("specify 'from-pool' OR 'from-prefix'")
            if 'family' not in args:
                raise NapMissingInputError("'family' must be specified with 'from-pool' mode")
            if int(args['family']) != 4 and int(args['family']) != 6:
                raise NapValueError("incorrect family specified, must be 4 or 6")

        elif 'from-prefix' in args:
            if type(args['from-prefix']) is not list:
                raise NapInputError("from-prefix should be a list")
            if 'from-pool' in args:
                raise NapInputError("specify 'from-pool' OR 'from-prefix'")
            if 'prefix_length' not in args:
                raise NapMissingInputError("'prefix_length' must be specified with 'from-prefix'")
            if 'family' in args:
                raise NapExtraneousInputError("'family' is superfluous when in 'from-prefix' mode")

        # determine prefixes
        prefixes = []
        wpl = 0
        if 'from-pool' in args:
            # extract prefixes from
            pool_result = self.list_pool(schema_spec, args['from-pool'])
            if pool_result == []:
                raise NapNonExistentError("Non-existent pool specified")
            for p in pool_result[0]['prefixes']:
                if self._get_afi(p) == args['family']:
                    prefixes.append(p)
            if len(prefixes) == 0:
                raise NapInputError('No prefixes of family %d in pool' % args['family'])
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
                    raise NapInputError("mixing of address-family is not allowed for 'from-prefix' arg")
                prefixes.append(prefix)

        if 'prefix_length' in args:
            wpl = args['prefix_length']

        # sanity check the wanted prefix length
        if afi == 4:
            if wpl < 0 or wpl > 32:
                raise NapValueError("the specified wanted prefix length argument must be between 0 and 32 for ipv4")
        elif afi == 6:
            if wpl < 0 or wpl > 128:
                raise NapValueError("the specified wanted prefix length argument must be between 0 and 128 for ipv6")

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

        sql = """SELECT * FROM find_free_prefix(%(schema)s, (""" + damp + """), %(prefix_length)s, %(max_result)s) AS prefix"""

        params['schema'] = args['schema']
        params['prefixes'] = prefixes
        params['prefix_length'] = wpl
        params['max_result'] = args['count']

        self._execute(sql, params)

        res = list()
        for row in self._curs_pg:
            res.append(row['prefix'])

        return res



    def list_prefix(self, schema_spec, spec = None):
        """ List prefixes
        """

        self._logger.debug("list_prefix called; spec: %s" % str(spec))

        if type(spec) is dict:

            #if len(spec) == 0:
            #    raise NapInputError("empty prefix specification")

            spec['schema'] = self._get_schema(schema_spec)['id']

            where, params = self._expand_prefix_spec(spec)

        else:
            raise NapError("invalid prefix specification")

        sql = "SELECT * FROM ip_net_plan "
        sql += "WHERE prefix <<= (SELECT prefix FROM ip_net_plan WHERE " + where + ") ORDER BY prefix"

        self._execute(sql, params)

        res = list()
        for row in self._curs_pg:
            res.append(dict(row))

        return res



    def remove_prefix(self, schema_spec, spec):
        """ Remove a prefix.
        """

        self._logger.debug("remove_prefix called; spec: %s" % str(spec))

        spec['schema'] = self._get_schema(schema_spec)['id']
        where, params = self._expand_prefix_spec(spec)
        sql = "DELETE FROM ip_net_plan AS p WHERE %s" % where
        self._execute(sql, params)



    def search_prefix(self, schema_spec, query):
        """ Search for prefixes.
        """

        # Add schema to query part list
        schema_q = {
            'operator': 'equals',
            'val1': 'schema',
            'val2': self._get_schema(schema_spec)['id']
        }
        if len(query) == 0:
            query = schema_q
        query = {
            'operator': 'and',
            'val1': schema_q,
            'val2': query
        }

        where, opt = self._expand_prefix_query(query, 'ip2')
        sql = str("SELECT ip1.* FROM ip_net_plan AS ip1 " +
            "JOIN ip_net_plan AS ip2 " +
            "ON (" +
            "   (ip2.prefix <<= ip1.prefix OR ip2.prefix >>= ip1.prefix) " +
            "   AND (ip1.schema = ip2.schema)" +
            ") WHERE " + where + " ORDER BY ip1.prefix")

        self._execute(sql, opt)

        result = list()
        for row in self._curs_pg:
            result.append(dict(row))

        return result



    def smart_search_prefix(self, schema_spec, query_str):
        """ Perform a smart search.

            The smart search function tries extract a query from
            a text string. This query is then passed to the search_prefix
            function, which performs the search.
        """

        self._logger.debug("Query string: %s" % query_str)

        # find query parts
        query_str_parts = []
        for part in shlex.split(query_str):
            query_str_parts.append({ 'string': part })

        # go through parts and add to query_parts list
        query_parts = list()
        for query_str_part in query_str_parts:

            # prefix
            if self._get_afi(query_str_part['string']) is not None:
                query_str_part['interpretation'] = 'prefix'
                self._logger.debug("Query part '" + query_str_part['string'] + "' interpreted as prefix")
                query_parts.append({
                    'operator': 'contained_within_equals',
                    'val1': 'prefix',
                    'val2': query_str_part['string']
                })

            # Description or comment
            else:
                self._logger.debug("Query part '" + query_str_part['string'] + "' interpreted as desc/comment")
                query_str_part['interpretation'] = 'description'
                query_parts.append({
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
                })

        # Sum all query parts to one query
        query = query_parts[0]
        for query_part in query_parts[1:]:
            query = {
                'operator': 'and',
                'val1': query_part,
                'val2': query
            }

        self._logger.debug("Expanded to: %s" % str(query))

        return { 'interpretation': query_str_parts, 'result': self.search_prefix(schema_spec, query) }



class NapError(Exception):
    """ General NAP errors
    """
    pass


class NapInputError(NapError):
    """ Something wrong with the input we received

        A general case.
    """
    pass


class NapMissingInputError(NapInputError):
    """ Missing input

        Most input is passed in dicts, this could mean a missing key in a dict.
    """
    pass


class NapExtraneousInputError(NapInputError):
    """ Extraneous input

        Most input is passed in dicts, this could mean an unknown key in a dict.
    """
    pass


class NapNoSuchOperatorError(NapInputError):
    """ A non existent operator was specified.
    """
    pass


class NapValueError(NapError):
    """ Something wrong with a value we have

        For example, trying to send an integer when an IP address is expected.
    """
    pass


class NapNonExistentError(NapError):
    """ A non existent object was specified

        For example, try to get a prefix from a pool which doesn't exist.
    """
    pass


class NapDuplicateError(NapError):
    """ The passed object violates unique constraints

        For example, create a schema with a name of an already existing one.
    """
    pass
