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
            self._curs_pg = self._con_pg.cursor(cursor_factory=psycopg2.extras.DictCursor)
        except psycopg2.Error, e:
            estr = str(e)
            self._logger.error(estr)
            raise NapError(estr)
        except psycopg2.Warning, w: 
            self._logger.warning(str(w))


    #
    # Schema functions
    #
    def _expand_schema_spec(self, spec):
        """ Expand schema specification to sql.
        """ 

        if type(spec) is not dict:
            raise NapError('schema specification must be dict')

        params = {}
        if 'id' in spec:
            where = " id = %(spec_id)s "
            params['spec_id'] = spec['id']
        elif 'name' in spec:
            where = " name = %(spec_name)s "
            params['spec_name'] = spec['name']
        else:
            raise NapError('missing both id and name in schema spec')

        return where, params


    def add_schema(self, attr):
        """ Add a new network schema.
        """

        # sanity check - do we have all attributes?
        req_attr = ['name', 'description']

        for a in req_attr:
            if not a in attr:
                raise NapMissingValueError("missing %s" % a)

        self._logger.debug("Adding schema; name: %s desc: %s" %
            (attr['name'], attr['description']))

        sql = ("INSERT INTO ip_net_schema " +
            "(name, description) VALUES " +
            "(%(name)s, %(description)s)")

        self._execute(sql, attr)
        return self._lastrowid()


    def remove_schema(self, spec):
        """ Removes a schema.
        """

        self._logger.debug("Removing schema; spec: %s" % str(spec))

        where, params = self._expand_schema_spec(spec)
        sql = "DELETE FROM ip_net_schema WHERE %s" % where
        self._execute(sql, params)


    def list_schema(self, spec=None):
        """ List schemas.
        """

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
        
        sql = "UPDATE ip_net_schema SET "

        if type(attr) is not dict:
            raise NapInvalid

        where, params = self._expand_schema_spec(spec)

        if 'name' in attr:
            sql += "name = %(name)s, "
            params['name'] = attr['name']
        if 'description' in attr:
            sql += "description = %(description)s, "
            params['description'] = attr['description']

        sql = sql[:-2] + " WHERE " + where
        self._execute(sql, params)


    #
    # Pool functions
    #
    def _expand_pool_spec(self, spec):
        """ Expand pool specification to sql.
        """ 

        if type(spec) is not dict:
            raise NapError('Invalid pool specification')

        params = {}
        if 'id' in spec:
            where = " po.id = %(spec_id)s "
            params['spec_id'] = spec['id']
        elif 'name' in spec:
            where = " po.name = %(spec_name)s "
            params['spec_name'] = spec['name']
        elif 'family' in spec:
            where = "pl.family = %(spec_family)s "
            params['spec_family'] = spec['family']
        else:
            raise NapError('missing valid search key in pool spec')

        return where, params


    def add_pool(self, attr):
        """ Add a pool.
        """

        # sanity check - do we have all attributes?
        req_attr = ['name', 'schema', 'description', 'default_type']

        for a in req_attr:
            if not a in attr:
                raise NapMissingValueError("missing %s" % a)

        self._logger.debug("Adding pool; name: %s desc: %s" %
            (attr['name'], attr['description']))

        sql = ("INSERT INTO ip_net_pool " +
            "(name, schema, description, default_type) VALUES " +
            "(%(name)s, %(schema)s, %(description)s, %(default_type)s)")

        self._execute(sql, attr)
        return self._lastrowid()

    
    def remove_pool(self, spec):
        """ Remove a pool.
        """

        self._logger.debug("Removing pool; spec: %s" % str(spec))

        where, params = self._expand_schema_spec(spec)
        if 'family' in spec:
            raise NapError("don't specify family for remove operation")

        sql = "DELETE FROM ip_net_pool AS po WHERE %s" % where
        self._execute(sql, params)


    def list_pool(self, spec = None):
        """ List pools.
        """
        
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

        sql = "UPDATE ip_net_pool SET "

        if type(attr) is not dict:
            raise NapInvalid

        where, params = self._expand_pool_spec(spec)

        if 'name' in attr:
            sql += "name = %(name)s, "
            params['name'] = attr['name']
        if 'description' in attr:
            sql += "description = %(description)s, "
            params['description'] = attr['description']
        if 'default_type' in attr:
            sql += "default_type = %(default_type)s, "
            params['default_type'] = attr['default_type']
        if 'schema' in attr:
            sql += "schema = %(schema)s, "
            params['schema'] = attr['schema']

        sql = sql[:-2] +  " FROM ip_net_pool AS po WHERE ip_net_pool.id = po.id AND " + where
        self._execute(sql, params)


    #
    # PREFIX FUNCTIONS
    #
    def find_free_prefix(self, prefixes, wanted_length, num = 1):
        """ Find a free prefix

            Arguments:
        """


    def list_prefix(self, spec):
        """ List prefixes
        """


        where = str()
        params = list()

        if type(spec) is dict:

            if len(spec) == 0:
                raise NapError("invalid prefix specification")

            # search keys:
            # family, schema, type, pool, prefix
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


    def _execute(self, sql, opt=None):
        """ Execute query, catch and log errors. 
        """

        try:
            self._curs_pg.execute(sql, opt)
            self._con_pg.commit()
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


class NapError(Exception):
    pass

class NapMissingValueError(NapError):
    pass
