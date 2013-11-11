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

from pynipap import AuthOptions, VRF, Pool, Prefix, NipapNonExistentError, NipapDuplicateError, NipapValueError
import pynipap

pynipap.xmlrpc_uri = 'http://guest@local:guest@127.0.0.1:1337'
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




class TestParentPrefix(unittest.TestCase):
    """ Test parent prefix related stuff
    """

    def setUp(self):
        """ Test setup, which essentially means to empty the database
        """
        TestHelper.clear_database()


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



class TestPrefixIndent(unittest.TestCase):
    """ Test prefix indent calculation
    """

    def setUp(self):
        """ Test setup, which essentially means to empty the database
        """
        TestHelper.clear_database()


    def test_prefix_edit(self):
        """ Verify indent is correct after prefix edit
        """
        th = TestHelper()
        # add a few prefixes
        p1 = th.add_prefix('192.168.0.0/16', 'reservation', 'test')
        p2 = th.add_prefix('192.168.0.0/24', 'reservation', 'test')
        p3 = th.add_prefix('192.168.1.0/24', 'reservation', 'test')

        # now edit the "middle prefix" so that it now covers 192.168.1.0/24
        p3.prefix = '192.168.0.0/20'
        p3.save()

        expected = []
        # expected result is a list of list, each row is a prefix, first value is prefix, next is indent level
        # notice how p2 and p3 switch places efter the edit
        expected.append([p1.prefix, 0])
        expected.append([p3.prefix, 1])
        expected.append([p2.prefix, 2])

        res = Prefix.smart_search('0.0.0.0/0', {})
        result = []
        for prefix in res['result']:
            result.append([prefix.prefix, prefix.indent])

        self.assertEqual(expected, result)



class TestPrefixChildren(unittest.TestCase):
    """ Test calculation of children prefixes
    """

    def setUp(self):
        """ Test setup, which essentially means to empty the database
        """
        TestHelper.clear_database()


    def test_children1(self):
        """ Add some prefixes and make sure number of children is correct
        """
        th = TestHelper()
        # add a few prefixes
        p1 = th.add_prefix('192.168.0.0/16', 'reservation', 'test')
        p2 = th.add_prefix('192.168.0.0/20', 'reservation', 'test')
        p3 = th.add_prefix('192.168.0.0/24', 'reservation', 'test')
        p4 = th.add_prefix('192.168.1.0/24', 'reservation', 'test')
        p5 = th.add_prefix('192.168.2.0/24', 'reservation', 'test')
        p6 = th.add_prefix('192.168.32.0/20', 'reservation', 'test')
        p7 = th.add_prefix('192.168.32.0/24', 'reservation', 'test')

        expected = []
        # expected result is a list of list, each row is a prefix, first value
        # is prefix, next is number of children
        expected.append([p1.prefix, 2])
        expected.append([p2.prefix, 3])
        expected.append([p3.prefix, 0])
        expected.append([p4.prefix, 0])
        expected.append([p5.prefix, 0])
        expected.append([p6.prefix, 1])
        expected.append([p7.prefix, 0])

        res = Prefix.smart_search('0.0.0.0/0', {})
        result = []
        for prefix in res['result']:
            result.append([prefix.prefix, prefix.children])

        self.assertEqual(expected, result)

        p5.prefix = '192.0.2.0/24'
        p5.save()
        expected = []
        expected.append([p5.prefix, 0])
        expected.append([p1.prefix, 2])
        expected.append([p2.prefix, 2])
        expected.append([p3.prefix, 0])
        expected.append([p4.prefix, 0])
        expected.append([p6.prefix, 1])
        expected.append([p7.prefix, 0])
        res = Prefix.smart_search('0.0.0.0/0', {})
        result = []
        for prefix in res['result']:
            result.append([prefix.prefix, prefix.children])

        self.assertEqual(expected, result)

        p4.prefix = '192.168.0.0/21'
        p4.save()
        expected = []
        expected.append([p5.prefix, 0])
        expected.append([p1.prefix, 2])
        expected.append([p2.prefix, 1])
        expected.append([p4.prefix, 1])
        expected.append([p3.prefix, 0])
        expected.append([p6.prefix, 1])
        expected.append([p7.prefix, 0])
        res = Prefix.smart_search('0.0.0.0/0', {})
        result = []
        for prefix in res['result']:
            result.append([prefix.prefix, prefix.children])

        self.assertEqual(expected, result)

        p1.remove()
        expected = []
        expected.append([p5.prefix, 0])
        expected.append([p2.prefix, 1])
        expected.append([p4.prefix, 1])
        expected.append([p3.prefix, 0])
        expected.append([p6.prefix, 1])
        expected.append([p7.prefix, 0])
        res = Prefix.smart_search('0.0.0.0/0', {})
        result = []
        for prefix in res['result']:
            result.append([prefix.prefix, prefix.children])

        self.assertEqual(expected, result)


class TestCountryCodeValue(unittest.TestCase):
    """ Test sanity for country value - should be ISO 3166-1 alpha-2 compliant
    """

    def setUp(self):
        """ Test setup, which essentially means to empty the database
        """
        TestHelper.clear_database()


    def test_country_code_length(self):
        """ Make sure only two character country codes are allowed
        """
        p = Prefix()
        p.prefix = '1.3.3.0/24'
        p.type = 'assignment'
        # try to input one character - should fail - this will be a INSERT operation
        p.country = 'a'
        with self.assertRaisesRegexp(NipapValueError, 'Please enter a two letter country code according to ISO 3166-1 alpha-2'):
            p.save()

        # try to input one character - should fail - this will be an UPDATE operation
        p.country = 'a'
        with self.assertRaisesRegexp(NipapValueError, 'Please enter a two letter country code according to ISO 3166-1 alpha-2'):
            p.save()

        # try to input three character - should fail
        p.country = 'aaa'
        with self.assertRaisesRegexp(NipapValueError, 'Please enter a two letter country code according to ISO 3166-1 alpha-2'):
            p.save()

        # try to input a number character - should fail
        p.country = 'a1'
        with self.assertRaisesRegexp(NipapValueError, 'Please enter a two letter country code according to ISO 3166-1 alpha-2'):
            p.save()

        # try to input two character - should succeed
        p.country = 'se'
        p.save()

        # output should be capitalized
        self.assertEqual('SE', p.country)



class TestAddressListing(unittest.TestCase):
    """
    """
    def setUp(self):
        """ Test setup, which essentially means to empty the database
        """
        TestHelper.clear_database()

    def testPrefixInclusion(self):
        """ Test prefix inclusion like include_neighbors, include_parents and include_children
        """
        th = TestHelper()
        # add a few prefixes
        p1 = th.add_prefix('192.168.0.0/16', 'reservation', 'root')
        p2 = th.add_prefix('192.168.0.0/20', 'reservation', 'test')
        p3 = th.add_prefix('192.168.0.0/24', 'reservation', 'foo')
        p4 = th.add_prefix('192.168.1.0/24', 'reservation', 'test')
        p5 = th.add_prefix('192.168.2.0/24', 'reservation', 'test')
        p6 = th.add_prefix('192.168.32.0/20', 'reservation', 'bar')
        p7 = th.add_prefix('192.168.32.0/24', 'assignment', 'test')
        p8 = th.add_prefix('192.168.32.1/32', 'host', 'test')
        p9 = th.add_prefix('192.168.32.2/32', 'host', 'xyz')
        p10 = th.add_prefix('192.168.32.3/32', 'host', 'test')

        expected = []
        # expected result is a list where each row is a prefix
        expected.append(p1.prefix)
        expected.append(p2.prefix)
        expected.append(p3.prefix)
        expected.append(p4.prefix)
        expected.append(p5.prefix)
        expected.append(p6.prefix)
        expected.append(p7.prefix)
        expected.append(p8.prefix)
        expected.append(p9.prefix)
        expected.append(p10.prefix)
        res = Prefix.smart_search('0.0.0.0/0', {})
        result = []
        for prefix in res['result']:
            result.append(prefix.prefix)
        self.assertEqual(expected, result)


        expected = []
        # expected result is a list where each row is a prefix
        expected.append(p1.prefix)
        res = Prefix.smart_search('root', {})
        result = []
        for prefix in res['result']:
            result.append(prefix.prefix)
        self.assertEqual(expected, result)

        expected = []
        # expected result is a list where each row is a prefix
        expected.append(p3.prefix)
        res = Prefix.smart_search('foo', {})
        result = []
        for prefix in res['result']:
            result.append(prefix.prefix)
        self.assertEqual(expected, result)

        expected = []
        # expected result is a list where each row is a prefix
        expected.append(p1.prefix)
        expected.append(p2.prefix)
        expected.append(p3.prefix)
        expected.append(p4.prefix)
        expected.append(p5.prefix)
        expected.append(p6.prefix)
        expected.append(p7.prefix)
        expected.append(p8.prefix)
        expected.append(p9.prefix)
        expected.append(p10.prefix)
        res = Prefix.smart_search('root', { 'children_depth': -1 })
        result = []
        for prefix in res['result']:
            result.append(prefix.prefix)
        self.assertEqual(expected, result)

        expected = []
        # expected result is a list where each row is a prefix
        expected.append(p1.prefix)
        expected.append(p2.prefix)
        expected.append(p3.prefix)
        res = Prefix.smart_search('foo', { 'parents_depth': -1 })
        result = []
        for prefix in res['result']:
            result.append(prefix.prefix)
        self.assertEqual(expected, result)

        expected = []
        # expected result is a list where each row is a prefix
        expected.append(p8.prefix)
        expected.append(p9.prefix)
        expected.append(p10.prefix)
        res = Prefix.smart_search('xyz', { 'include_neighbors': True })
        result = []
        for prefix in res['result']:
            result.append(prefix.prefix)
        self.assertEqual(expected, result)




class TestCli(unittest.TestCase):
    """ CLI tests
    """

    def test_extra_args(self):
        """ Extra arg should raise exception
        """
        from nipap_cli.command import Command, InvalidCommand
        from nipap_cli import nipap_cli
        from pynipap import NipapError

        # 'FOO' should not be there and should raise an exception
        with self.assertRaisesRegexp(InvalidCommand, 'Invalid argument:'):
            cmd = Command(nipap_cli.cmds, ['address', 'modify', '1.3.3.1/32', 'vrf_rt', 'none', 'set', 'FOO' ])



class TestNipapHelper(unittest.TestCase):
    """ Test sanity for country value - should be ISO 3166-1 alpha-2 compliant
    """
    def test_test1(self):
        from nipap_cli.command import Command, InvalidCommand
        from nipap_cli import nipap_cli
        from pynipap import NipapError

        cmd = Command(nipap_cli.cmds, ['vrf', 'list', 'nam'])
        self.assertEqual(['name'], sorted(cmd.complete()))

        cmd = Command(nipap_cli.cmds, ['vrf', 'list', 'name'])
        self.assertEqual(['name'], sorted(cmd.complete()))



if __name__ == '__main__':

    # set up logging
    log = logging.getLogger()
    logging.basicConfig()
    log.setLevel(logging.INFO)

    if sys.version_info >= (2,7):
        unittest.main(verbosity=2)
    else:
        unittest.main()


