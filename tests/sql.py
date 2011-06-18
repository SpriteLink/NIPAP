#!/usr/bin/python
# vim: et ts=4:

import unittest
import sys
sys.path.append('../napd/')

import nap

class NapSql(unittest.TestCase):
    nap = nap.Nap()

    def clean_up(self):
        self.nap._execute("DELETE FROM ip_net_plan")
        self.nap._execute("DELETE FROM ip_net_pool")
        self.nap._execute("DELETE FROM ip_net_schema")



    def setUp(self):
        self.clean_up()
        self.schema_id = self.nap.add_schema({ 'name': 'test-schema', 'description': '' })



    def test_calc_indent(self):
        """ Test automatic calculation of indent level

            Insert baseline data, namely 192.0.2.0/24
            Verify indent level is 0, since it should be a root prefix
            Insert 192.0.2.0/27
            Verify indent level is 1 for 192.0.2.0/27
            Insert 192.0.2.0/32
            Insert 192.0.2.1/32
            Insert 192.0.2.2/32
            Insert 192.0.2.3/32
            Verify indent level is 2 for 192.0.2.[0-3]/32
            Insert 192.0.2.32/32
            Insert 192.0.2.33/32
            Insert 192.0.2.34/32
            Insert 192.0.2.35/32
            Verify indent level is 1 for 192.0.2.3[2-5]/32
            Insert 192.0.2.32/27
            Verify indent level is 1 for 192.0.2.32/27
            Verify indent level is 2 for 192.0.2.3[2-5]/32
            Remove 192.0.2.0/27
            Verify indent level is 1 for 192.0.2.[0-3]/32
        """

    def test_db_constraints(self):
        """

            INSERT 1.3.0.0/16    r    allow
            INSERT 1.3.0.0/16    r    deny    duplicate
            INSERT 1.3.3.0/24    r    allow
            INSERT 1.3.3.0/27    a    allow
            INSERT 1.3.3.0/32    h    allow
            INSERT 1.3.3.1/32    h    allow
            INSERT 1.3.3.2/32    a    deny    assignment within assignment not allowed
            DELETE 1.3.3.0/27    a    deny    hosts inside assignment
        """
        self.assertEqual(self._inspre('1.3.0.0/16', 'reservation'), True, 'Unable to insert prefix 1.3.0.0/16')
        self.assertRaises(Exception, self._inspre, '1.3.0.0/16', 'reservation', 'Duplicate prefix detection not working')
        self.assertEqual(self._inspre('1.3.3.0/24', 'reservation'), True)
        self.assertEqual(self._inspre('1.3.3.0/27', 'assignment'), True)
        self.assertEqual(self._inspre('1.3.3.0/32', 'host'), True)
        self.assertEqual(self._inspre('1.3.3.1/32', 'host'), True)
        self.assertRaises(Exception, self._inspre, '1.3.3.2/31', 'host')
        self.assertRaises(Exception, self._inspre, '1.3.3.3/32', 'assignment', 'Able to create assignment within assignment - we should not')
        self.assertEqual(self._delpre('1.3.3.0/27'), False, 'Able to delete assignment containing hosts - we should not')



    def _inspre(self, prefix, prefix_type):
        """ Insert a prefix

            Return true on success, false otherwise
        """
        self.nap._execute("INSERT INTO ip_net_plan (authoritative_source, schema, prefix, type) VALUES ('naptest', %(schema)s, %(prefix)s, %(prefix_type)s)", { 'schema': self.schema_id, 'prefix': prefix, 'prefix_type': prefix_type })
        return True



    def _delpre(self, prefix):
        """ Delete a prefix

            Return true on success, false otherwise
        """
        self.nap._execute("DELETE FROM ip_net_plan WHERE schema = %(schema)s AND prefix = %(prefix)s", { 'schema': self.schema_id, 'prefix': prefix })
        return True


if __name__ == '__main__':
    unittest.main()
    NapSql.clean_up()

