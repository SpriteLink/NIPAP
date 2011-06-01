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
                'schema_id': self.schema_attrs['id'],
                'name': 'test-pool1',
                'description': 'Test pool numero uno!',
                'default_type': 'assignment',
                'ipv4_default_prefix_length': 30,
                'ipv6_default_prefix_length': 112
                }
        self.pool_attrs['id'] = self.nap.add_pool(self.pool_attrs)
        self.prefix_attrs = {
                'authoritative_source': 'naptest',
                'schema_id': self.schema_attrs['id'],
                'prefix': '1.3.3.1/32',
                'description': 'Test prefix numero uno!'
                }
        self.prefix_attrs['id'] = self.nap.add_prefix(self.prefix_attrs)
        self.prefix_attrs2 = {
                'authoritative_source': 'naptest',
                'schema_id': self.schema_attrs['id'],
                'prefix': '1.3.3.0/24',
                'description': ''
                }
        self.prefix_attrs2['id'] = self.nap.add_prefix(self.prefix_attrs2)
        self.prefix_attrs3 = {
                'authoritative_source': 'naptest',
                'schema_id': self.schema_attrs['id'],
                'prefix': '1.3.0.0/16',
                'description': ''
                }
        self.prefix_attrs3['id'] = self.nap.add_prefix(self.prefix_attrs3)



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
        self.assertRaises(nap.NapExtraneousInputError, self.nap.add_schema, attrs)



    def test_expand_schema_spec(self):
        """ Test the expand_schema_spec()

            The _expand_schema_spec() function is used throughout the schema
            functions to expand the schema specification input and so we test
            the separately.
        """
        # wrong type
        self.assertRaises(nap.NapInputError, self.nap._expand_schema_spec, 'string')
        # wrong type
        self.assertRaises(nap.NapInputError, self.nap._expand_schema_spec, 1)
        # wrong type
        self.assertRaises(nap.NapInputError, self.nap._expand_schema_spec, [])
        # missing keys
        self.assertRaises(nap.NapMissingInputError, self.nap._expand_schema_spec, { })
        # crap key
        self.assertRaises(nap.NapExtraneousInputError, self.nap._expand_schema_spec, { 'crap': self.schema_attrs['name'] })
        # required keys and extra crap
        self.assertRaises(nap.NapExtraneousInputError, self.nap._expand_schema_spec, { 'name': self.schema_attrs['name'], 'crap': 'crap' })
        # proper key but incorrect value (int vs string)
        self.assertRaises(nap.NapValueError, self.nap._expand_schema_spec, { 'id': '3' })
        # proper key but incorrect value (int vs string)
        self.assertRaises(nap.NapValueError, self.nap._expand_schema_spec, { 'name': 3 })
        # both id and name
        self.assertRaises(nap.NapExtraneousInputError, self.nap._expand_schema_spec, { 'id': 3, 'name': '3' })
        # proper key - id
        where, params = self.nap._expand_schema_spec({ 'id': 3 })
        self.assertEqual(where, 'id = %(spec_id)s', "Improperly expanded WHERE clause")
        self.assertEqual(params, {'spec_id': 3}, "Improperly expanded params dict")
        # proper spec - name
        where, params = self.nap._expand_schema_spec({ 'name': 'test' })



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
        # spec is tested elsewhere, just test attrs part
        self.assertRaises(nap.NapExtraneousInputError, self.nap.edit_schema, { 'name': self.schema_attrs['name'] }, crap_attrs)



    def test_schema_list_crap_input(self):
        """ Try to input junk into list_schema and expect error

        """
        # TODO: what do we really expect?
        self.assertRaises(nap.NapExtraneousInputError, self.nap.list_schema, { 'crap': 'crap crap' })



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



    def test_expand_pool_spec(self):
        """
        """
        # wrong type
        self.assertRaises(nap.NapInputError, self.nap._expand_pool_spec, 'string')
        # wrong type
        self.assertRaises(nap.NapInputError, self.nap._expand_pool_spec, 1)
        # wrong type
        self.assertRaises(nap.NapInputError, self.nap._expand_pool_spec, [])
        # missing keys
        self.assertRaises(nap.NapMissingInputError, self.nap._expand_pool_spec, { })
        # crap key
        self.assertRaises(nap.NapExtraneousInputError, self.nap._expand_pool_spec, { 'crap': self.pool_attrs['name'] })
        # required keys and extra crap
        self.assertRaises(nap.NapExtraneousInputError, self.nap._expand_pool_spec, { 'id': self.pool_attrs['id'], 'crap': 'crap' })
        # proper key but incorrect value (int vs string)
        self.assertRaises(nap.NapValueError, self.nap._expand_pool_spec, { 'id': '3' })
        # non unique key
        self.assertRaises(nap.NapInputError, self.nap._expand_pool_spec, { 'name': self.pool_attrs['name'] })
        # proper key but incorrect value (int vs string)
        self.assertRaises(nap.NapValueError, self.nap._expand_pool_spec, { 'name': 3 })
        # both id and name
        self.assertRaises(nap.NapExtraneousInputError, self.nap._expand_pool_spec, { 'id': 3, 'name': '3' })
        # proper key - id
        where, params = self.nap._expand_pool_spec({ 'id': 3 })
        self.assertEqual(where, 'po.id = %(spec_id)s', "Improperly expanded WHERE clause")
        self.assertEqual(params, {'spec_id': 3}, "Improperly expanded params dict")
        # proper spec - name & schema_id
        where, params = self.nap._expand_pool_spec({ 'name': 'test', 'schema_id': self.schema_attrs['id'] })
        self.assertEqual(where, 'po.name = %(spec_name)s AND po.schema = %(spec_schema)s', "Improperly expanded WHERE clause")
        self.assertEqual(params, {'spec_name': 'test', 'spec_schema': self.schema_attrs['id'] }, "Improperly expanded params dict")
        # proper spec - name & schema_name
        where, params = self.nap._expand_pool_spec({ 'name': 'test', 'schema_name': self.schema_attrs['name'] })
        self.assertEqual(where, 'po.name = %(spec_name)s AND po.schema = %(spec_schema)s', "Improperly expanded WHERE clause")
        self.assertEqual(params, {'spec_name': 'test', 'spec_schema': self.schema_attrs['id'] }, "Improperly expanded params dict")



    def test_pool_add1(self):
        """ Add a pool and check it's there using list functions

            Refer to schema by id
        """
        attrs = {
                'name': 'test-pool-wrong',
                'schema_id': self.schema_attrs['id'],
                'description': 'A simple test pool with incorrect name!',
                'default_type': 'reservation',
                'ipv4_default_prefix_length': 30,
                'ipv6_default_prefix_length': 112
                }
        pool_id = self.nap.add_pool(attrs)
        pool = self.nap.list_pool({ 'id': pool_id })
        for a in attrs:
            self.assertEqual(pool[0][a], attrs[a], 'Added object differ from listed on attribute: %s  %s!=%s' % (a, attrs[a], pool[0][a]))



    def test_pool_add2(self):
        """ Add a pool and check it's there using list functions

            Refer to schema by name
        """
        attrs = {
                'name': 'test-pool-wrong',
                'schema_name': self.schema_attrs['name'],
                'default_type': 'reservation',
                'description': 'A simple test pool with incorrect name!'
                }
        pool_id = self.nap.add_pool(attrs)
        pool = self.nap.list_pool({ 'id': pool_id })
        for a in attrs:
            self.assertEqual(pool[0][a], attrs[a], 'Added object differ from listed on attribute: ' + a)



    def test_edit_pool_by_name(self):
        """ Try to rename a pool using edit_pool() function

            Pool is not uniquely identified by name and so this should raise an error
        """
        spec = { 'name': self.pool_attrs['name'] }
        attrs = {
                'name': 'test-pool',
                'default_type': 'assignment',
                'description': 'A simple test pool with correct name!'
                }
        self.assertRaises(nap.NapInputError, self.nap.edit_pool, spec, attrs)



    def test_edit_pool(self):
        """ Rename a pool using edit_pool() function
        """
        spec = { 'id': self.pool_attrs['id'] }
        attrs = {
                'name': 'test-pool',
                'default_type': 'assignment',
                'description': 'A simple test pool with correct name!',
                'ipv4_default_prefix_length': 32,
                'ipv6_default_prefix_length': 128
                }
        self.nap.edit_pool(spec, attrs)
        # check that search for old record doesn't return anything
        pool = self.nap.list_pool({ 'schema_id': self.schema_attrs['id'], 'name': self.pool_attrs['name'] })
        self.assertEqual(pool, [], 'Old entry still exists')
        pool = self.nap.list_pool({ 'schema_id': self.schema_attrs['id'], 'name': attrs['name'] })
        for a in attrs:
            self.assertEqual(pool[0][a], attrs[a], 'Added object differ from listed on attribute: ' + a)



    def test_remove_pool_by_id(self):
        """ Remove a pool by id
        """
        pool = self.nap.list_pool({ 'id': self.pool_attrs['id'] })
        # first make sure our pool exists
        self.assertEqual(pool[0], self.pool_attrs, 'Record must exist before we can delete it')
        # remove the pool
        self.nap.remove_pool({ 'id': self.pool_attrs['id'] })
        # check that search for old record doesn't return anything
        pool = self.nap.list_pool({ 'id': self.pool_attrs['id'] })
        self.assertEqual(pool, [], 'Old entry still exists')



    def test_prefix_basic(self):
        """ Test basic prefix functions
        """
        prefix_attrs = {
                'authoritative_source': 'nap-test',
                'schema_id': self.schema_attrs['id'],
                'prefix': '1.3.3.7/32',
                'description': 'test prefix',
                'comment': 'test comment, please remove! ;)'
                }
        self.nap.add_prefix(prefix_attrs)
        prefix = self.nap.list_prefix({ 'prefix': prefix_attrs['prefix'], 'schema_name': self.schema_attrs['name'] })
        for a in prefix_attrs:
            self.assertEqual(prefix[0][a], prefix_attrs[a], 'Added object differ from listed on attribute: ' + a)

        # fetch many prefixes - all in a schema
        prefix = self.nap.list_prefix({'schema_id': self.schema_attrs['id']})
        self.assertGreater(len(prefix), 0, 'Found 0 prefixes in schema ' + self.schema_attrs['name'])


    def test_prefix_remove(self):
        """ Remove a prefix
        """
        prefix = self.nap.list_prefix({ 'id': self.prefix_attrs['id'] })
        # first make sure our prefix exists
        self.assertEqual(prefix[0]['id'], self.prefix_attrs['id'], 'Record must exist before we can delete it')
        # remove the prefix, by id
        self.nap.remove_prefix({ 'id': self.prefix_attrs['id'] })
        # check that search for old record doesn't return anything
        prefix = self.nap.list_prefix({ 'id': self.prefix_attrs['id'] })
        self.assertEqual(prefix, [], 'Old entry still exists')


    def test_prefix_indent(self):
        """ Check that our indentation calculation is working

            Prefixes gets an indent value automatically assigned to help in
            displaying prefix information. The indent value is written on
            updates to the table and this test is to make sure it is correctly
            calculated.
        """
        p1 = self.nap.list_prefix({ 'prefix': '1.3.3.1/32', 'schema_name': self.schema_attrs['name'] })[0]
        p2 = self.nap.list_prefix({ 'prefix': '1.3.3.0/24', 'schema_name': self.schema_attrs['name'] })[0]
        p3 = self.nap.list_prefix({ 'prefix': '1.3.0.0/16', 'schema_name': self.schema_attrs['name'] })[0]
        self.assertEqual(p1['indent'], 2, "Indent calc on add failed")
        self.assertEqual(p2['indent'], 1, "Indent calc on add failed")
        self.assertEqual(p3['indent'], 0, "Indent calc on add failed")
        # remove middle prefix
        self.nap.remove_prefix({ 'id': self.prefix_attrs2['id'] })
        # check that child prefix indent level has decreased
        p1 = self.nap.list_prefix({ 'prefix': '1.3.3.1/32', 'schema_name': self.schema_attrs['name'] })[0]
        p3 = self.nap.list_prefix({ 'prefix': '1.3.0.0/16', 'schema_name': self.schema_attrs['name'] })[0]
        self.assertEqual(p1['indent'], 1, "Indent calc on remove failed")
        self.assertEqual(p3['indent'], 0, "Indent calc on remove failed")



    def test_find_free_prefix(self):
        """ Test find_free_prefix

        """
        # set up a prefix not used elsewhere so we have a known good state
        prefix_attrs = {
                'authoritative_source': 'nap-test',
                'schema_id': self.schema_attrs['id'],
                'prefix': '100.0.0.0/16',
                'description': 'test prefix',
                'comment': 'test comment, please remove! ;)'
                }
        self.nap.add_prefix(prefix_attrs)
        res = self.nap.find_free_prefix({ 'schema': self.schema_attrs['id'], 'from-prefix': [ '100.0.0.0/16', '1.3.3.0/24' ] }, 24, 1)
        self.assertEqual(res, ['100.0.0.0/24'], "Incorrect prefix set returned")




def main():
    if sys.version_info >= (2,7):
        unittest.main(verbosity=2)
    else:
        unittest.main()




if __name__ == '__main__':
    main()
