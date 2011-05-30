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
    """ Tests the NAP class
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
        self.prefix_attrs = {
                'authoritative_source': 'naptest',
                'schema': self.schema_attrs['id'],
                'prefix': '1.3.3.1/32',
                'description': 'Test prefix numero uno!'
                }
        self.prefix_attrs['id'] = self.nap.add_prefix(self.prefix_attrs)



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
        attrs['id'] = self.nap.add_schema(attrs)
        schema = self.nap.list_schema({ 'id': attrs['id'] })
        for a in attrs:
            self.assertEqual(schema[0][a], attrs[a], 'Added object differ from listed on attribute: ' + a)



    def test_schema_add_crap_input(self):
        """ Try to input junk into add_schema and expect error

        """
        attrs = {
                'name': 'test-schema-crap',
                'description': 'A simple test schema with incorrect name!',
                'crap': 'this is just some crap'
                }
        # missing everything
        self.assertRaises(nap.NapMissingInputError, self.nap.add_schema, { })
        # missing description
        self.assertRaises(nap.NapMissingInputError, self.nap.add_schema, { 'name': 'crapson' })
        # have required and extra crap
        self.assertRaises(nap.NapInputError, self.nap.add_schema, attrs)



    def test_schema_edit_crap_input(self):
        """ Try to input junk into edit_schema and expect error

        """
        attrs = {
                'name': 'test-schema-crap',
                'description': 'A simple test schema with incorrect name!'
                }
        crap_attrs = {
                'name': 'test-schema-crap',
                'description': 'A simple test schema with incorrect name!',
                'crap': 'this is just some crap'
                }
        # crap spec
        self.assertRaises(nap.NapMissingInputError, self.nap.edit_schema, { 'crap': self.schema_attrs['name'] }, attrs)
        # proper spec, totally crap attr
        self.assertRaises(nap.NapMissingInputError, self.nap.edit_schema, { 'name': self.schema_attrs['name'] }, { 'crap': 'crap' })
        # proper spec, required attr and extra crap
        self.assertRaises(nap.NapInputError, self.nap.edit_schema, { 'name': self.schema_attrs['name'] }, crap_attrs)



    def test_schema_list_crap_input(self):
        """ Try to input junk into list_schema and expect error

        """
        # TODO: what do we really expect?
        self.assertRaises(nap.NapMissingInputError, self.nap.list_schema, { 'crap': 'crap crap' })



    def test_schema_remove_crap_input(self):
        """ Try to input junk into remove_schema and expect error

        """
        # just crap spec
        self.assertRaises(nap.NapMissingInputError, self.nap.remove_schema, { 'crap': 'crap crap' })
        # contains required attrs plus some crap
        # TODO: fix this!
        #self.assertRaises(nap.NapInputError, self.nap.remove_schema, { 'name': self.schema_attrs['name'], 'crap': 'crap crap' })



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
        for a in attrs:
            self.assertEqual(schema[0][a], attrs[a], 'Modified schema differ from listed on attribute: ' + a)



    def test_schema_remove(self):
        """ Remove a schema

            Remove the schema previously modified and make sure it's not there.
        """
        spec = { 'name': 'test-schema' }
        self.nap.remove_schema(spec)
        # check that search for old record doesn't return anything
        schema = self.nap.list_schema(spec)
        self.assertEqual(schema, [], 'Old entry still exists')



    def test_pool_add(self):
        """ Add a pool and check it's there using list functions
        """
        attrs = {
                'name': 'test-pool-wrong',
                'schema': self.schema_attrs['id'],
                'default_type': 'reservation',
                'description': 'A simple test pool with incorrect name!'
                }
        pool_id = self.nap.add_pool(attrs)
        pool = self.nap.list_pool({ 'id': pool_id })
        for a in attrs:
            self.assertEqual(pool[0][a], attrs[a], 'Added object differ from listed on attribute: ' + a)



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
        for a in attrs:
            self.assertEqual(pool[0][a], attrs[a], 'Added object differ from listed on attribute: ' + a)



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



    def test_prefix_basic(self):
        """
        """
        prefix_attrs = {
                'authoritative_source': 'nap-test',
                'schema': self.schema_attrs['id'],
                'prefix': '1.3.3.7/32',
                'description': 'test prefix',
                'comment': 'test comment, please remove! ;)'
                }
        self.nap.add_prefix(prefix_attrs)
        prefix = self.nap.list_prefix({ 'prefix': prefix_attrs['prefix'] })
        for a in prefix_attrs:
            self.assertEqual(prefix[0][a], prefix_attrs[a], 'Added object differ from listed on attribute: ' + a)





def main():
    if sys.version_info >= (2,7):
        unittest.main(verbosity=2)
    else:
        unittest.main()




if __name__ == '__main__':
    main()
