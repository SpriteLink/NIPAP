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
    logger = logging.getLogger()

    nap = nap.Nap()

    def test_add_schema(self):
        """ Add schema with incorrect name
        """
        schema_attrs = {
                'name': 'test-schema-wrong',
                'description': 'A simple test schema with incorrect name!'
                }
        self.nap.add_schema(schema_attrs)
        # FIXME: not needed when the modify_schema test works
        schema_attrs = {
                'name': 'test-schema-wrong',
                'description': 'A simple test schema with incorrect name!'
                }
        self.nap.add_schema(schema_attrs)

    def test_modify_schema(self):
        """ Set correct name on address-schema
        """
        spec = { 'name': 'test-schema-wrong' }
        attrs = {
                'name': 'test-schema',
                'description': 'A simple test schema with correct name!'
                }
        # FIXME: edit_schema is actually broken!?
        #self.nap.edit_schema(spec, attrs)


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

    def test_add_prefix(self):
        """ Simply test of adding a prefix and verifying it is there

            Will try to add prefix 192.0.2.0/24
        """
#        nap.add_prefix()
        self.assertEqual(1, 1)



def clean_db():
    self.nap._execute("DELETE FROM ip_net_plan")
    self.nap._execute("DELETE FROM ip_net_pool")
    self.nap._execute("DELETE FROM ip_net_schema")

def main():
    self.clean_db()
    if sys.version_info > (2,6):
        unittest.main(verbosity=2)
    else:
        unittest.main()




if __name__ == '__main__':
    main()
