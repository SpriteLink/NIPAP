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


class NapTest(unittest.TestCase):
    """ Tests the schema features of NAP
    """

    logger = logging.getLogger()
    nap = nap.Nap()

    def test_add_schema(self):
        """ Add a schema and check it's there using list functions
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



    def test_dupe_schema(self):
        """ Check so we can't create duplicate schemas
        """
        schema_attrs = {
                'name': 'test-schema-wrong',
                'description': 'A simple test schema with incorrect name!'
                }
        # TODO: this should raise a better exception, something like non-unique or duplicate
        self.assertRaises(nap.NapError, self.nap.add_schema, schema_attrs)



    def test_modify_schema(self):
        """ Modify schema
        """
        spec = { 'name': 'test-schema-wrong' }
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


    def test_remove_schema(self):
        """ Remove a schema
        """
        spec = { 'name': 'test-schema' }
        self.nap.remove_schema(spec)
        # check that search for old record doesn't return anything
        schema = self.nap.list_schema(spec)
        self.assertEqual(schema, [], 'Old entry still exists')



    def test_pool_add(self):
        """ Add a pool and check it's there using list functions
        """
        schema = self.nap.list_schema({ 'name': 'test-schema' })
        attrs = {
                'name': 'test-pool-wrong',
                'schema': schema[0]['id'],
                'default_type': 'assignment',
                'description': 'A simple test pool with incorrect name!'
                }
        pool_id = self.nap.add_pool(attrs)
        pool = self.nap.list_pool({ 'id': pool_id })
        self.assertEqual(pool[0]['id'], pool_id, 'Add operations returned id differ from listed id')
        self.assertEqual(pool[0]['name'], attrs['name'], 'Added name differ from listed name')
        self.assertEqual(pool[0]['description'], attrs['description'], 'Added description differ from listed description')
        self.assertEqual(pool[0]['schema'], schema[0]['id'], 'Added schema differ from listed schema')
        self.assertEqual(pool[0]['default_type'], attrs['default_type'], 'Added default_type differ from listed default_type')



    def test_pool(self):
        """ Simple test of address-pool functions

            1. Add address-schema named 'global'
            1. Add address-pool named 'test-pool' with default_type of
               reservation
            2. Verify 'test-pool' exists and default_type is reservation
            3. Modify 'test-pool' default_type to assignment
            4. Remove 'test-pool'
            5. Verify 'test-pool' does not exist
        """
        pool_attrs = {
                'name': 'test-pool',
                'schema': 'test-schema',
                'description': 'A test pool!'
                }
#        self.nap.add_pool(pool_attrs)





def clean_db():
    """ Better start from a clean slate!
    """
    # local nap object to avoid fscking up something
    n = nap.Nap()
    n._execute("DELETE FROM ip_net_plan")
    n._execute("DELETE FROM ip_net_pool")
    n._execute("DELETE FROM ip_net_schema")


def main():
    clean_db()
    if sys.version_info >= (2,7):
        unittest.main(verbosity=2)
    else:
        unittest.main()




if __name__ == '__main__':
    main()
