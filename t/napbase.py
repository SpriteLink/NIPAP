#!/usr/bin/python
# vim: et :

import logging
import unittest
import sys
sys.path.append('../napd/')

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
log_format = "%(levelname)-8s %(message)s"

import nap


class NapSchemaTest(unittest.TestCase):
    """ Tests the schema features of NAP
    """

    logger = logging.getLogger()
    nap = nap.Nap()

    def setUp(self):
        """ Better start from a clean slate!
        """
        self.nap._execute("DELETE FROM ip_net_plan")
        self.nap._execute("DELETE FROM ip_net_pool")
        self.nap._execute("DELETE FROM ip_net_schema")

        attrs = {
                'name': 'test-schema1',
                'description': 'Test schema numero uno!'
                }
        schema_id = self.nap.add_schema(attrs)
        self.nap.add_schema


    def test_schema_basic(self):
        """ Basic schema test

            1. Add a new schema
            2. List with filters to get newly created schema
            3. Verify listed schema coincides with input args for added schema
            4. Remove schema
        """
        attrs = {
                'name': 'test-schema-wrong',
                'description': 'A simple test schema with incorrect name!'
                }
        schema_id = self.nap.add_schema(attrs)
        schema = self.nap.list_schema({ 'id': schema_id })
        self.assertEqual(schema[0]['id'], schema_id, 'Add operations returned id differ from listed id')
        self.assertEqual(schema[0]['name'], attrs['name'], 'Added name differ from listed name')
        self.assertEqual(schema[0]['description'], attrs['description'], 'Added description differ from listed description')



    def test_schema_dupe(self):
        """ Check so we can't create duplicate schemas

            There are unique indices in the database that should prevent us
            from creating duplicate schema (ie, with the same name).
        """
        schema_attrs = {
                'name': 'test-schema-dupe',
                'description': 'Testing dupe'
                }
        # TODO: this should raise a better exception, something like non-unique or duplicate
        self.nap.add_schema(schema_attrs)
        self.assertRaises(nap.NapError, self.nap.add_schema, schema_attrs)



    def test_schema_rename(self):
        """ Rename a schema

            Uses the edit_schema() functionality to rename our previously
            created and incorrectly named schema so it hereafter has the
            correct name. Also tests the list_schema() functionality since we
            use that to list the modified schema.
        """
        spec = { 'name': 'test-schema1' }
        attrs = {
                'name': 'test-schema',
                'description': 'A simple test schema with correct name!'
                }
        self.nap.edit_schema(spec, attrs)
        # check that search for old record doesn't return anything
        schema = self.nap.list_schema(spec)
        self.assertEqual(schema, [], 'Old entry still exists')
        schema = self.nap.list_schema({ 'name': 'test-schema' })
        self.assertEqual(schema[0]['name'], attrs['name'], 'Modified name differ from listed name')
        self.assertEqual(schema[0]['description'], attrs['description'], 'Modified description differ from listed description')



    def test_schema_remove(self):
        """ Remove a schema

            Remove the schema previously modified and make sure it's not there.
        """
        spec = { 'name': 'test-schema' }
        self.nap.remove_schema(spec)
        # check that search for old record doesn't return anything
        schema = self.nap.list_schema(spec)
        self.assertEqual(schema, [], 'Old entry still exists')



class NapPoolTest(unittest.TestCase):
    """ Tests the pool features of NAP
    """

    logger = logging.getLogger()
    nap = nap.Nap()

    def setUp(self):
        """ Better start from a clean slate!
        """
        self.nap._execute("DELETE FROM ip_net_plan")
        self.nap._execute("DELETE FROM ip_net_pool")
        self.nap._execute("DELETE FROM ip_net_schema")

        self.schema_attrs = {
                'name': 'test-schema1',
                'description': 'Test schema numero uno!'
                }
        self.schema_id = self.nap.add_schema(self.schema_attrs)
        self.pool_attrs = {
                'schema': self.schema_id,
                'name': 'test-pool1',
                'description': 'Test schema numero uno!',
                'default_type': 'assignment'
                }
        self.pool_attrs['id'] = self.nap.add_pool(self.pool_attrs)



    def test_pool_add(self):
        """ Add a pool and check it's there using list functions
        """
        attrs = {
                'name': 'test-pool-wrong',
                'schema': self.schema_id,
                'default_type': 'reservation',
                'description': 'A simple test pool with incorrect name!'
                }
        pool_id = self.nap.add_pool(attrs)
        pool = self.nap.list_pool({ 'id': pool_id })
        self.assertEqual(pool[0]['id'], pool_id, 'Add operations returned id differ from listed id')
        self.assertEqual(pool[0]['name'], attrs['name'], 'Added name differ from listed name')
        self.assertEqual(pool[0]['description'], attrs['description'], 'Added description differ from listed description')
        self.assertEqual(pool[0]['schema'], self.schema_id, 'Added schema differ from listed schema')
        self.assertEqual(pool[0]['default_type'], attrs['default_type'], 'Added default_type differ from listed default_type')



    def test_pool_modify(self):
        """ Rename a pool using edit_pool() function
        """
        spec = { 'name': self.pool_attrs['name'] }
        attrs = {
                'name': 'test-pool',
                'default_type': 'assignment',
                'description': 'A simple test pool with correct name!'
                }
        self.nap.edit_pool(spec, attrs)
        # check that search for old record doesn't return anything
        pool = self.nap.list_pool(spec)
        self.assertEqual(pool, [], 'Old entry still exists')
        pool = self.nap.list_pool({ 'name': attrs['name'] })
        self.assertEqual(pool[0]['name'], attrs['name'], 'Modified name differ from listed name')
        self.assertEqual(pool[0]['description'], attrs['description'], 'Modified description differ from listed description')



    def test_pool_remove(self):
        """ Remove a pool
        """
        pool = self.nap.list_pool({ 'name': self.pool_attrs['name'] })
        # first make sure our pool exists
        self.assertEqual(pool[0], self.pool_attrs, 'Record must exist before we can delete it')
        # remove the pool
        self.nap.remove_pool({ 'name': self.pool_attrs['name'] })
        # check that search for old record doesn't return anything
        pool = self.nap.list_pool({ 'name': self.pool_attrs['name'] })
        self.assertEqual(pool, [], 'Old entry still exists')





class NapPrefixTest(unittest.TestCase):
    """ Tests the prefix features of NAP
    """

    logger = logging.getLogger()
    nap = nap.Nap()

    def setUp(self):
        """ Better start from a clean slate!
        """
        self.nap._execute("DELETE FROM ip_net_plan")
        self.nap._execute("DELETE FROM ip_net_pool")
        self.nap._execute("DELETE FROM ip_net_schema")

        self.schema_attrs = {
                'name': 'test-schema1',
                'description': 'Test schema numero uno!'
                }
        self.schema_attrs['id'] = self.nap.add_schema(self.schema_attrs)
        self.pool_attrs = {
                'schema': self.schema_attrs['id'],
                'name': 'test-pool1',
                'description': 'Test schema numero uno!',
                'default_type': 'assignment'
                }
        self.pool_attrs['id'] = self.nap.add_pool(self.pool_attrs)


    def test_prefix_basic(self):
        """
        """
        prefix_attrs = {
                'schema': self.schema_attrs['id'],
                'prefix': '1.3.3.7/32',
                'description': 'test prefix'
                }
        self.nap.add_prefix(prefix_attrs)
        prefix = self.nap.list_prefix({ 'prefix': prefix_attrs['prefix'] })
        self.assertEqual(prefix[0], prefix_attrs)





def main():
    if sys.version_info >= (2,7):
        unittest.main(verbosity=2)
    else:
        unittest.main()




if __name__ == '__main__':
    main()
