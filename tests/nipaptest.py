#!/usr/bin/env python

import logging
import unittest
import sys
sys.path.insert(0, '..')
sys.path.insert(0, '../pynipap')

import nipap.nipap
from nipap.authlib import SqliteAuth
from nipap.nipapconfig import NipapConfig

from pynipap import AuthOptions, VRF, Pool, Prefix, NipapNonExistentError, NipapDuplicateError, NipapValueError
import pynipap

pynipap.xmlrpc_uri = 'http://guest@local:guest@127.0.0.1:1337'
o = AuthOptions({
        'authoritative_source': 'nipap'
        })

class TestParentPrefix(unittest.TestCase):
    """ Test parent prefix related stuff
    """

    def setUp(self):
        """ Test setup, which essentially means to empty the database
        """
        self.cfg = NipapConfig('/etc/nipap/nipap.conf')
        self.nipap = nipap.nipap.Nipap()

        # have to delete hosts before we can delete the rest
        self.nipap._execute("DELETE FROM ip_net_plan WHERE masklen(prefix) = 32")
        # the rest
        self.nipap._execute("DELETE FROM ip_net_plan")
        # delete all except for the default VRF with id 0
        self.nipap._execute("DELETE FROM ip_net_vrf WHERE id > 0")
        # set default info for VRF 0
        self.nipap._execute("UPDATE ip_net_vrf SET name = 'default', description = 'The default VRF, typically the Internet.' WHERE id = 0")
        self.nipap._execute("DELETE FROM ip_net_pool")
        self.nipap._execute("DELETE FROM ip_net_asn")



    def test_parent_prefix(self):
        """ Verify that listing with parent_prefix returns match for 'foo'
        """
        expected = []
        parent = self.add_prefix('1.3.0.0/16', 'reservation', 'test')
        expected.append([parent.prefix, False])
        expected.append([self.add_prefix('1.3.1.0/24', 'assignment', 'foo').prefix, True])
        expected.append([self.add_prefix('1.3.2.0/24', 'assignment', 'test').prefix, False])
        expected.append([self.add_prefix('1.3.3.0/24', 'assignment', 'test').prefix, False])
        expected.append([self.add_prefix('1.3.4.0/24', 'assignment', 'test').prefix, False])
        self.add_prefix('1.2.4.0/24', 'assignment', 'test')

        res = Prefix.smart_search('foo', { 'parent_prefix': parent.id })
        result = []
        for prefix in res['result']:
            result.append([prefix.prefix, prefix.match])

        self.assertEqual(expected, result)



    def test_parent_prefix2(self):
        """ Verify that listing with parent_prefix returns a list with no matches

            Nothing matches foo but we should still get a list of prefixes
        """
        expected = []
        parent = self.add_prefix('1.3.0.0/16', 'reservation', 'test')
        expected.append([parent.prefix, False])
        expected.append([self.add_prefix('1.3.1.0/24', 'assignment', 'test').prefix, False])
        expected.append([self.add_prefix('1.3.2.0/24', 'assignment', 'test').prefix, False])
        expected.append([self.add_prefix('1.3.3.0/24', 'assignment', 'test').prefix, False])
        expected.append([self.add_prefix('1.3.4.0/24', 'assignment', 'test').prefix, False])
        self.add_prefix('1.2.4.0/24', 'assignment', 'test')

        res = Prefix.smart_search('foo', { 'parent_prefix': parent.id })
        result = []
        for prefix in res['result']:
            result.append([prefix.prefix, prefix.match])

        self.assertEqual(expected, result)


    def add_prefix(self, prefix, type, description):
        p = Prefix()
        p.prefix = prefix
        p.type = type
        p.description = description
        p.save()
        return p


if __name__ == '__main__':

    # set up logging
    log = logging.getLogger()
    logging.basicConfig()
    log.setLevel(logging.INFO)

    if sys.version_info >= (2,7):
        unittest.main(verbosity=2)
    else:
        unittest.main()


