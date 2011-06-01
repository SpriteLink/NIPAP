# vim: et ts=4 :
import logging
import psycopg2
import psycopg2.extras

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

        if is_ipv4(ip):
            return 4
        elif is_ipv6(ip):
            return 6
        else:
            return None


    #
    # SQL related functions
    #

    def _execute(self, sql, opt=None):
        """ Execute query, catch and log errors.
        """

        try:
            self._curs_pg.execute(sql, opt)
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


    def _translate_schema_spec(self, spec):
        """ Expand 'schema_name' or 'schema_id'.

            Translates 'schema_name' or 'schema_id' element in spec
            to a 'schema' element containing the schema ID.
        """

        if 'schema_id' in spec and 'schema_name' in spec:
            raise NapExtraneousInputError("specification contain both 'id' and 'name', specify schema id or name")

        if 'schema_id' in spec:
            schema = self.list_schema({ 'id': spec['schema_id'] })
            if schema == []:
                raise NapInputError("non-existing schema specified")
            spec['schema'] = schema[0]['id']
            del(spec['schema_id'])
        elif 'schema_name' in spec:
            schema = self.list_schema({ 'name': spec['schema_name'] })
            if schema == []:
                raise NapInputError("non-existing schema specified")
            spec['schema'] = schema[0]['id']
            del(spec['schema_name'])
        else:
            raise NapInputError("Missing schema, add schema_id or schema_name to spec!")

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

        self._execute(sql, params)

        res = list()
        for row in self._curs_pg:
            res.append(dict(row))

        return res



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

        allowed_values = ['id', 'name', 'schema_id', 'schema_name']
        for a in spec:
            if a not in allowed_values:
                raise NapExtraneousInputError("extraneous specification key %s" % a)

        if 'id' in spec:
            if long(spec['id']) != spec['id']:
                raise NapValueError("pool specification key 'id' must be an integer")
            if spec != { 'id': spec['id'] }:
                raise NapExtraneousInputError("pool specification with 'id' should not contain anything else")
        elif 'name' in spec:
            if type(spec['name']) != type(''):
                raise NapValueError("pool specification key 'name' must be a string")
            if 'id' in spec:
                raise NapExtraneousInputError("pool specification contain both 'id' and 'name', specify pool id or name")

            # name is only unique together with schema, find schema
            spec = self._translate_schema_spec(spec)

        else:
            raise NapMissingInputError('missing both id and schema/name in pool spec')

        where, params = self._sql_expand_where(spec, 'spec_', 'po.')

        return where, params



    def add_pool(self, attr):
        """ Add a pool.
        """

        self._logger.debug("add_pool called; spec: %s" % str(attr))

        # check that given schema exists and populate 'schema' with correct id
        if 'schema_id' in attr:
            schema = self.list_schema({ 'id': attr['schema_id'] })
            if schema == []:
                raise NapInputError("non-existing schema specified")
            attr['schema'] = schema[0]['id']
            del(attr['schema_id'])
        elif 'schema_name' in attr:
            schema = self.list_schema({ 'name': attr['schema_name'] })
            if schema == []:
                raise NapInputError("non-existing schema specified")
            attr['schema'] = schema[0]['id']
            del(attr['schema_name'])

        # sanity check - do we have all attributes?
        req_attr = ['name', 'schema', 'description', 'default_type']
        allowed_attr = req_attr + ['ipv4_default_prefix_length', 'ipv6_default_prefix_length']
        self._check_attr(attr, req_attr, allowed_attr)

        insert, params = self._sql_expand_insert(attr)
        sql = "INSERT INTO ip_net_pool " + insert

        self._execute(sql, params)
        return self._lastrowid()



    def remove_pool(self, spec):
        """ Remove a pool.
        """

        self._logger.debug("remove_pool called; spec: %s" % str(spec))

        where, params = self._expand_pool_spec(spec)

        sql = "DELETE FROM ip_net_pool AS po WHERE %s" % where
        self._execute(sql, params)



    def list_pool(self, spec = None):
        """ List pools.
        """

        self._logger.debug("list_pool called; spec: %s" % str(spec))

        sql = """SELECT po.id,
                        po.name,
                        po.description,
                        po.schema,
                        po.default_type,
                        po.ipv4_default_prefix_length,
                        po.ipv6_default_prefix_length
                FROM ip_net_pool AS po
                LEFT JOIN ip_net_plan AS pl ON pl.pool = po.id """
        params = list()

        if spec is not None:
            where, params = self._expand_pool_spec(spec)
            sql += " WHERE " + where

        # TODO: what the hell is this for? Why aren't they unique to begin with?
        sql += " GROUP BY po.id, po.name, po.description, po.schema, po.default_type, po.ipv4_default_prefix_length, po.ipv6_default_prefix_length"

        self._execute(sql, params)

        res = list()
        for row in self._curs_pg:
            res.append(dict(row))

        return res



    def edit_pool(self, spec, attr):
        """ Edit pool.
        """

        self._logger.debug("edit_pool called; spec: %s attr: %s" %
                (str(spec), str(attr)))

        allowed_attr = [
                'name',
                'default_type',
                'description',
                'ipv4_default_prefix_length',
                'ipv6_default_prefix_length'
                ]
        self._check_attr(attr, [], allowed_attr)

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

        allowed_keys = ['id', 'family', 'schema_name', 'schema_id', 
            'type', 'pool_name', 'pool_id', 'prefix']
        for key in spec.keys():
            if key not in allowed_keys:
                raise NapExtraneousInputError("Key '" + key + "' not allowed in prefix spec.")

        where = ""
        params = {}

        # if we have id, no other input is needed
        if 'id' in spec:
            if spec != {'id': spec['id']}:
                raise NapExtraneousInputError("If id specified, no other keys are allowed.")
            where += "id = %(spec_id)s"
            params['spec_id'] = spec['id']

        else:
            # fetch schema ID
            spec = self._translate_schema_spec(spec)
            where, params = self._sql_expand_where(spec)

        self._logger.debug("where: %s params: %s" % (where, str(params)))
        return where, params



    def add_prefix(self, attr):
        """ Add a prefix
        """

        self._logger.debug("add_prefix called; attr: %s" % str(attr))

        # sanity check - do we have all attributes?
        req_attr = ['prefix', 'schema', 'description' ]
        allowed_attr = ['authoritative_source', 'prefix', 'schema', 'description', 'comment']
        attr = self._translate_schema_spec(attr)
        self._check_attr(attr, req_attr, allowed_attr)

        insert, params = self._sql_expand_insert(attr)
        sql = "INSERT INTO ip_net_plan " + insert

        self._execute(sql, params)
        prefix_id = self._lastrowid()

        return prefix_id


    def edit_prefix(self, spec, attr):
        """ Edit prefix.
        """

        self._logger.debug("edit_prefix called; spec: %s attr: %s" %
                (str(spec), str(attr)))

        allowed_attr = [ 'name', 'description', 'comment', 'schema_name', 'schema_id' ]

        self._check_attr(attr, [], allowed_attr)

        if 'schema_name' in attr or 'schema_id' in attr:
            attr = self._translate_schema_spec(attr)

        where, params1 = self._expand_prefix_spec(spec)
        update, params2 = self._sql_expand_update(attr)
        params = dict(params2.items() + params1.items())

        sql = "UPDATE ip_net_plan SET " + update
        sql += " FROM ip_net_plan AS p WHERE ip_net_plan.id = p.id AND " + where

        self._execute(sql, params)



    def find_free_prefix(self, spec, wanted_length, num = 1):
        """ Find a free prefix

            Arguments:
        """

        # input sanity
        if type(spec) is not dict:
            raise NapInputError("invalid input, please provide dict as spec")

        spec = self._translate_schema_spec(spec)

        if 'from-pool' in spec:
            if 'from-prefix' in spec:
                raise NapInputError("specify 'from-pool' OR 'from-prefix'")
        elif 'from-prefix' in spec:
            if 'from-pool' in spec:
                raise NapInputError("specify 'from-pool' OR 'from-prefix'")

        prefixes = []
        if 'from-pool' in spec:
            raise NotImplementedError()
            # TODO: hmm, we need to know if the user wants IPv4 or IPv6..

        params = {}
        if 'from-prefix' in spec:
            i = 0
            for prefix in spec['from-prefix']:
                # TODO: do proper verification this is truely a prefix
                # TODO: make sure we only have one address-family..
                prefixes.append(prefix)

            # TODO: this makes me want to piss my pants
            #       we should really write a patch to psycopg2 or something to
            #       properly adapt an python list of texts with values looking
            #       like prefixes to a postgresql array of inets
            sql_prefix = ' UNION '.join('SELECT %(prefix' + str(prefixes.index(p)) + ')s AS prefix' for p in prefixes)
            for p in prefixes:
                params['prefix' + str(prefixes.index(p))] = p

            damp = 'SELECT array_agg(prefix::inet) FROM (' + sql_prefix + ') AS a'

        # TODO: now we now address-family of from-pool or from-prefix, make
        #       sure wanted_prefix_length falls within boundaries for
        #       address-family, ie 32 for IPv4 and 128 for IPv6


        sql = """SELECT * FROM find_free_prefix(%(schema)s, (""" + damp + """), %(wanted_length)s, %(max_result)s) AS prefix"""

        params['schema'] = spec['schema']
        params['prefixes'] = prefixes
        params['wanted_length'] = wanted_length
        params['max_result'] = num

        self._execute(sql, params)

        res = list()
        for row in self._curs_pg:
            res.append(row['prefix'])

        return res



    def list_prefix(self, spec):
        """ List prefixes
        """

        self._logger.debug("list_prefix called; spec: %s" % str(spec))

        if type(spec) is dict:

            if len(spec) == 0:
                raise NapInputError("empty prefix specification")

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



    def remove_prefix(self, spec):
        """ Remove a prefix.
        """

        self._logger.debug("remove_prefix called; spec: %s" % str(spec))

        where, params = self._expand_prefix_spec(spec)

        sql = "DELETE FROM ip_net_plan AS p WHERE %s" % where

        self._execute(sql, params)



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


class NapValueError(NapError):
    """ Something wrong with a value we have

        For example, trying to send an integer when an IP address is expected.
    """
    pass


