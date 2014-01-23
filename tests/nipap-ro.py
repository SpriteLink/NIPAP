#!/usr/bin/env python

import logging
import unittest
import sys
sys.path.insert(0, '..')
sys.path.insert(0, '../pynipap')
sys.path.insert(0, '../nipap')
sys.path.insert(0, '../nipap-cli')

from nipap.backend import Nipap
from nipap.authlib import SqliteAuth
from nipap.nipapconfig import NipapConfig


from pynipap import AuthOptions, VRF, Pool, Prefix
from pynipap import NipapNonExistentError, NipapDuplicateError, NipapValueError, NipapAuthorizationError
import pynipap

pynipap.xmlrpc_uri = 'http://readonly:gottatest@127.0.0.1:1337'
o = AuthOptions({
        'authoritative_source': 'nipap'
        })


class TestHelper:

    @classmethod
    def clear_database(cls):
        cfg = NipapConfig('/etc/nipap/nipap.conf')
        n = Nipap()

        # have to delete hosts before we can delete the rest
        n._execute("DELETE FROM ip_net_plan WHERE masklen(prefix) = 32")
        # the rest
        n._execute("DELETE FROM ip_net_plan")
        # delete all except for the default VRF with id 0
        n._execute("DELETE FROM ip_net_vrf WHERE id > 0")
        # set default info for VRF 0
        n._execute("UPDATE ip_net_vrf SET name = 'default', description = 'The default VRF, typically the Internet.' WHERE id = 0")
        n._execute("DELETE FROM ip_net_pool")
        n._execute("DELETE FROM ip_net_asn")


    def add_prefix(self, prefix, type, description):
        p = Prefix()
        p.prefix = prefix
        p.type = type
        p.description = description
        p.save()
        return p



class TestReadonly(unittest.TestCase):
    """ Test that read-only functions truly are read-only
    """

    def setUp(self):
        """ Test setup, which essentially means to empty the database
        """
        TestHelper.clear_database()


    #
    # VRF
    #
    def test_add_vrf(self):
        """ We should NOT be able to execute add_vrf as read-only user
        """
        v = VRF()
        v.rt = '123:456'
        v.name = 'test'
        with self.assertRaises(NipapAuthorizationError):
            v.save()


    def test_remove_vrf(self):
        """ We should NOT be able to execute remove_vrf as read-only user
        """
        v = VRF()
        v.id = 0
        with self.assertRaises(NipapAuthorizationError):
            v.remove()


    def test_list_vrf(self):
        """ We should be able to execute list_vrf as read-only user
        """
        v = VRF.get(0)
        self.assertEqual(v.id, 0)


    def test_edit_vrf(self):
        """ We should NOT be able to execute edit_vrf as read-only user
        """
        v = VRF()
        v.id = 123
        with self.assertRaises(NipapAuthorizationError):
            v.save()


    def test_search_vrf(self):
        """ We should be able to execute search_vrf as read-only user
        """
        v = VRF.search({ 'val1': 'id',
            'operator': 'equals',
            'val2': 0 })
        self.assertEqual(v['result'][0].id, 0)


    def test_smart_search_vrf(self):
        """ We should be able to execute smart_search_vrf as read-only user
        """
        v = VRF.smart_search('default')
        self.assertEqual(v['result'][0].id, 0)



    #
    # Pool
    #
    def test_add_pool(self):
        """ We should NOT be able to execute add_pool as read-only user
        """
        p = Pool()
        p.name = 'test'
        with self.assertRaises(NipapAuthorizationError):
            p.save()


    def test_remove_pool(self):
        """ We should NOT be able to execute remove_pool as read-only user
        """
        p = Pool()
        p.id = 0
        with self.assertRaises(NipapAuthorizationError):
            p.remove()


    def test_list_pool(self):
        """ We should be able to execute list_pool as read-only user
        """
        with self.assertRaises(NipapNonExistentError):
            p = Pool.get(0)


    def test_edit_pool(self):
        """ We should NOT be able to execute edit_pool as read-only user
        """
        p = Pool()
        p.id = 123
        with self.assertRaises(NipapAuthorizationError):
            p.save()


    def test_search_pool(self):
        """ We should be able to execute search_pool as read-only user
        """
        p = Pool.search({ 'val1': 'id',
            'operator': 'equals',
            'val2': 0 })


    def test_smart_search_pool(self):
        """ We should be able to execute smart_search_pool as read-only user
        """
        p = Pool.smart_search('default')



    #
    # Prefix
    #
    def test_add_prefix(self):
        """ We should NOT be able to execute add_prefix as read-only user
        """
        p = Prefix()
        p.prefix = '1.3.3.7'
        with self.assertRaises(NipapAuthorizationError):
            p.save()


    def test_remove_prefix(self):
        """ We should NOT be able to execute remove_prefix as read-only user
        """
        p = Prefix()
        p.id = 0
        with self.assertRaises(NipapAuthorizationError):
            p.remove()


    def test_list_prefix(self):
        """ We should be able to execute list_prefix as read-only user
        """
        with self.assertRaises(NipapNonExistentError):
            p = Prefix.get(0)


    def test_edit_prefix(self):
        """ We should NOT be able to execute edit_prefix as read-only user
        """
        p = Prefix()
        p.id = 123
        with self.assertRaises(NipapAuthorizationError):
            p.save()


    def test_search_prefix(self):
        """ We should be able to execute search_prefix as read-only user
        """
        p = Prefix.search({ 'val1': 'id',
            'operator': 'equals',
            'val2': 0 })


    def test_smart_search_prefix(self):
        """ We should be able to execute smart_search_prefix as read-only user
        """
        p = Prefix.smart_search('default')


    def test_find_free_prefix(self):
        """ We should be able to execute find_free_prefix as read-only user
        """
        v = VRF.get(0)
        p = Prefix.find_free(v, { 'from-prefix': ['1.3.3.0/24'],
            'prefix_length': 27 })


    #
    # ASN
    #

    # TODO: add tests for the following backens functions
    # def list_asn(self, auth, asn = {}):
    # def add_asn(self, auth, attr):
    # def edit_asn(self, auth, asn, attr):
    # def remove_asn(self, auth, asn):
    # def search_asn(self, auth, query, search_options = {}):
    # def smart_search_asn(self, auth, query_str, search_options = {}, extra_query = None):
    # def search_tag(self, auth, query, search_options = {}):




if __name__ == '__main__':

    # set up logging
    log = logging.getLogger()
    logging.basicConfig()
    log.setLevel(logging.INFO)

    if sys.version_info >= (2,7):
        unittest.main(verbosity=2)
    else:
        unittest.main()


