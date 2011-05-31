# vim: et ts=4 :
import logging
import psycopg2
import psycopg2.extras

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
        except psycopg2.Error, e:
            estr = str(e)
            self._logger.error(estr)
            raise NapError(estr)
        except psycopg2.Warning, w:
            self._logger.warning(str(w))



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
                raise NapInputError("extraneous attribute %s" % a)



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
                raise NapInputError("extraneous specification key %s" % a)

        if 'id' in spec:
            if long(spec['id']) != spec['id']:
                raise NapValueError("schema specification key 'id' must be an integer")
            if 'name' in spec:
                raise NapInputError("schema specification contain both 'id' and 'key', specify schema id or name")
        elif 'name' in spec:
            if type(spec['name']) != type(''):
                raise NapValueError("schema specification key 'name' must be a string")
            if 'id' in spec:
                raise NapInputError("schema specification contain both 'id' and 'key', specify schema id or name")
        else:
            raise NapMissingInputError('missing both id and name in schema spec')

        where, params = self._sql_expand_where(spec, 'spec_')

        return where, params



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

        allowed_values = ['id', 'name']
        for a in spec:
            if a not in allowed_values:
                raise NapInputError("extraneous specification key %s" % a)

        if 'id' in spec:
            if long(spec['id']) != spec['id']:
                raise NapValueError("pool specification key 'id' must be an integer")
            if 'name' in spec:
                raise NapInputError("pool specification contain both 'id' and 'key', specify pool id or name")
        elif 'name' in spec:
            if type(spec['name']) != type(''):
                raise NapValueError("pool specification key 'name' must be a string")
            if 'id' in spec:
                raise NapInputError("pool specification contain both 'id' and 'key', specify pool id or name")
        else:
            raise NapMissingInputError('missing both id and name in pool spec')

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
        self._check_attr(attr, req_attr, req_attr)

        insert, params = self._sql_expand_insert(attr)
        sql = "INSERT INTO ip_net_pool " + insert

        self._execute(sql, params)
        return self._lastrowid()



    def remove_pool(self, spec):
        """ Remove a pool.
        """

        self._logger.debug("remove_pool called; spec: %s" % str(spec))

        where, params = self._expand_schema_spec(spec)

        sql = "DELETE FROM ip_net_pool AS po WHERE %s" % where
        self._execute(sql, params)



    def list_pool(self, spec = None):
        """ List pools.
        """

        self._logger.debug("list_pool called; spec: %s" % str(spec))

        sql = ("SELECT po.id, po.name, po.description, po.schema, po.default_type " +
            "FROM ip_net_pool AS po LEFT JOIN ip_net_plan AS pl ON pl.pool = po.id ")
        params = list()

        if spec is not None:
            where, params = self._expand_pool_spec(spec)
            sql += " WHERE " + where

        sql += " GROUP BY po.id, po.name, po.description, po.schema, po.default_type"

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

        allowed_attr = ['name', 'default_type', 'description']
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
        """ Expand prefix specification to sql.
        """

        if type(spec) is not dict:
            raise NapError('invalid prefix specification')

        params = {}
        if 'id' in spec:
            where = " p.id = %(spec_id)s "
            params['spec_id'] = spec['id']
        elif 'prefix' in spec:
            if 'schema' not in spec:
                raise NapError('invalid prefix specification, must include schema and prefix or id (missing schema)')
            where = " p.prefix = %(spec_prefix)s "
            params['spec_prefix'] = spec['prefix']
        elif 'schema' in spec:
            if 'prefix' not in spec:
                raise NapError('invalid prefix specification, must include schema and prefix or id (missing prefix)')
            where = "p.schema = %(spec_schema)s "
            params['spec_schema'] = spec['schema']
        else:
            raise NapError('missing valid search key in prefix spec')

        return where, params



    def add_prefix(self, attr):
        """ Add a prefix
        """

        self._logger.debug("add_prefix called; attr: %s" % str(attr))

        # sanity check - do we have all attributes?
        req_attr = ['prefix', 'schema', 'description' ]
        allowed_attr = ['authoritative_source', 'schema', 'prefix', 'description', 'comment']
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

        allowed_attr = [ 'name', 'description', 'comment', 'schema' ]

        self._check_attr(attr, [], allowed_attr)

        where, params1 = self._expand_prefix_spec(spec)
        update, params2 = self._sql_expand_update(attr)
        params = dict(params2.items() + params1.items())

        sql = "UPDATE ip_net_plan SET " + update
        sql += " FROM ip_net_plan AS p WHERE ip_net_plan.id = p.id AND " + where

        self._execute(sql, params)



    def find_free_prefix(self, prefixes, wanted_length, num = 1):
        """ Find a free prefix

            Arguments:
        """



    def list_prefix(self, spec):
        """ List prefixes
        """

        self._logger.debug("list_prefix called; spec: %s" % str(spec))

        where = str()
        params = list()

        if type(spec) is dict:

            if len(spec) == 0:
                raise NapError("invalid prefix specification")

            # search keys:
            # family, schema, type, pool, prefix
            if 'id' in spec:
                where += "id = %s AND "
                params.append(spec['id'])
            if 'family' in spec:
                where += "family = %s AND "
                params.append(spec['family'])
            if 'schema' in spec:
                where += "schema = %s AND "
                params.append(spec['schema'])
            if 'type' in spec:
                where += "type = %s AND "
                params.append(spec['type'])
            if 'pool' in spec:
                where += "pool = %s AND "
                params.append(spec['pool'])
            if 'prefix' in spec:
                where += "prefix = %s AND "
                params.append(spec['prefix'])

            if len(where) == 0:
                raise NapError("no valid search keys found in spec")

        elif spec is None:
            # list everything - should we really permit this?
            pass

        else:
            raise NapError("invalid prefix specification")

        sql = "SELECT * FROM ip_net_plan "
        sql += "WHERE prefix <<= (SELECT prefix FROM ip_net_plan WHERE " + where[:-4] + ") ORDER BY prefix"

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

        For example, an extra key in a dict.
    """
    pass


class NapMissingInputError(NapError):
    """ Missing input

        Most input is passed in dicts, this could mean a missing key in a dict.
    """
    pass


class NapValueError(NapError):
    """ Something wrong with a value we have

        For example, trying to send an integer when an IP address is expected.
    """
    pass


