#!/usr/bin/env python

#
# Most of the tests here are performed via Pynipap which makes it a lot easier
# to test things given that we receive python objects and not just basic data
# structures like those returned in xmlrpc.py. If you want to write a new test,
# it is recommended that you place it here rather than in xmlrpc.py.
#

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

pynipap.xmlrpc_uri = 'http://unittest:gottatest@127.0.0.1:1337'
o = AuthOptions({
        'authoritative_source': 'nipap'
        })

# disable caching of objects in Pynipap
pynipap.CACHE = False


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


    def add_prefix(self, prefix, type, description, tags=[], pool_id=None):

        p = Prefix()
        p.prefix = prefix
        p.type = type
        p.description = description
        p.tags = tags
        if pool_id:
            pool = Pool.get(pool_id)
            p.pool = pool
        p.save()
        return p


    def add_prefix_from_pool(self, pool, family, description):
        p = Prefix()
        args = {}
        args['from-pool'] = pool
        args['family'] = family
        p.type = pool.default_type

        p.save(args)
        return p



    def add_pool(self, name, default_type, ipv4_default_prefix_length, ipv6_default_prefix_length):
        pool = Pool()
        pool.name = name
        pool.default_type = default_type
        pool.ipv4_default_prefix_length = ipv4_default_prefix_length
        pool.ipv6_default_prefix_length = ipv6_default_prefix_length
        pool.save()
        return pool




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



class TestPrefixDisplayPrefix(unittest.TestCase):
    """ Test calculation of display_prefix on child prefixes
    """

    def setUp(self):
        """ Test setup, which essentially means to empty the database
        """
        TestHelper.clear_database()


    def test_prefix_edit(self):
        """ Make sure display_prefix is correctly updated on modification of
            parent
        """
        # we ran into display_prefix not being updated correctly in #515

        th = TestHelper()
        # add a few prefixes
        p1 = th.add_prefix('192.168.0.0/24', 'assignment', 'test')
        p2 = th.add_prefix('192.168.0.1/32', 'host', 'test')

        # now edit the "middle prefix" so that it now covers 192.168.1.0/24
        p1.prefix = '192.168.0.0/23'
        p1.save()

        # check that display_prefix of host is as expected
        res = Prefix.smart_search('192.168.0.1/32', {})
        self.assertEqual('192.168.0.1/23', res['result'][0].display_prefix)



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



class TestPrefixTags(unittest.TestCase):
    """ Test prefix tag calculation
    """

    def setUp(self):
        """ Test setup, which essentially means to empty the database
        """
        TestHelper.clear_database()


    def test_prefix_edit(self):
        """ Verify tags are correct after prefix edit
        """
        # ran into this issue in #507

        th = TestHelper()
        # add to "top level" prefix, each with a unique tag
        p1 = th.add_prefix('1.0.0.0/8', 'reservation', 'test', tags=['a'])
        p2 = th.add_prefix('2.0.0.0/8', 'reservation', 'test', tags=['b'])

        # add a subnet of p1
        p3 = th.add_prefix('1.0.0.0/24', 'reservation', 'test')

        # p3 should have inherited_tags = ['a'] from p1
        res = Prefix.smart_search('1.0.0.0/24', {})
        self.assertEqual(['a'], res['result'][0].inherited_tags.keys())

        # edit p3 to become subnet of p2
        p3.prefix = '2.0.0.0/24'
        p3.save()

        # p3 should have inherited_tags = ['b'] from p2
        res = Prefix.smart_search('2.0.0.0/24', {})
        self.assertEqual(['b'], res['result'][0].inherited_tags.keys())



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

        # p4 192.168.1.0/24 => 192.168.0.0/21
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

    def test_children2(self):
        """ Add an assignment and a host and make children calculation works
            after modifying the assignment
        """
        # we ran into children not being updated correctly in #515

        th = TestHelper()
        # add a few prefixes
        p1 = th.add_prefix('192.168.0.0/24', 'assignment', 'test')
        p2 = th.add_prefix('192.168.0.1/32', 'host', 'test')

        # now edit the "middle prefix" so that it now covers 192.168.1.0/24
        p1.prefix = '192.168.0.0/23'
        p1.save()

        # check that children of parent is as expected
        res = Prefix.smart_search('192.168.0.0/23', {})
        self.assertEqual(1, res['result'][0].children)



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



class TestPoolStatistics(unittest.TestCase):
    """ Test calculation of statistics for pools
    """
    def setUp(self):
        """ Test setup, which essentially means to empty the database
        """
        TestHelper.clear_database()


    def test_stats1(self):
        """ Check total stats are correct when adding and removing member prefix
        """
        th = TestHelper()

        # add a pool
        pool1 = th.add_pool('test', 'assignment', 31, 112)

        # check stats for pool1
        res = Pool.list({ 'id': pool1.id })
        # ipv4
        self.assertEqual(0, res[0].member_prefixes_v4)
        self.assertEqual(0, res[0].used_prefixes_v4)
        self.assertEqual(0, res[0].total_addresses_v4)
        self.assertEqual(0, res[0].used_addresses_v4)
        self.assertEqual(0, res[0].free_addresses_v4)
        # ipv6
        self.assertEqual(0, res[0].member_prefixes_v6)
        self.assertEqual(0, res[0].used_prefixes_v6)
        self.assertEqual(0, res[0].total_addresses_v6)
        self.assertEqual(0, res[0].used_addresses_v6)
        self.assertEqual(0, res[0].free_addresses_v6)

        # add some members to the pool
        p1 = th.add_prefix('1.0.0.0/24', 'assignment', 'test', pool_id=pool1.id)
        p2 = th.add_prefix('2.0.0.0/24', 'assignment', 'test', pool_id=pool1.id)
        p3 = th.add_prefix('2001:db8::/48', 'assignment', 'test', pool_id=pool1.id)
        p4 = th.add_prefix('2001:db8:1::/48', 'assignment', 'test', pool_id=pool1.id)

        # check stats for pool1
        res = Pool.list({ 'id': pool1.id })
        # ipv4
        self.assertEqual(2, res[0].member_prefixes_v4)
        self.assertEqual(0, res[0].used_prefixes_v4)
        self.assertEqual(512, res[0].total_addresses_v4)
        self.assertEqual(0, res[0].used_addresses_v4)
        self.assertEqual(512, res[0].free_addresses_v4)
        # ipv6
        self.assertEqual(2, res[0].member_prefixes_v6)
        self.assertEqual(0, res[0].used_prefixes_v6)
        self.assertEqual(2417851639229258349412352, res[0].total_addresses_v6)
        self.assertEqual(0, res[0].used_addresses_v6)
        self.assertEqual(2417851639229258349412352, res[0].free_addresses_v6)

        # remove one IPv4 and one IPv6 member from the pool
        p1.remove()
        p3.remove()

        # check stats for pool1
        res = Pool.list({ 'id': pool1.id })
        # ipv4
        self.assertEqual(1, res[0].member_prefixes_v4)
        self.assertEqual(0, res[0].used_prefixes_v4)
        self.assertEqual(256, res[0].total_addresses_v4)
        self.assertEqual(0, res[0].used_addresses_v4)
        self.assertEqual(256, res[0].free_addresses_v4)
        # ipv6
        self.assertEqual(1, res[0].member_prefixes_v6)
        self.assertEqual(0, res[0].used_prefixes_v6)
        self.assertEqual(1208925819614629174706176, res[0].total_addresses_v6)
        self.assertEqual(0, res[0].used_addresses_v6)
        self.assertEqual(1208925819614629174706176, res[0].free_addresses_v6)


    def test_stats2(self):
        """ Check total stats are correct when updating member prefix
        """
        th = TestHelper()

        # add a pool
        pool1 = th.add_pool('test', 'assignment', 31, 112)

        # add some members to the pool
        p1 = th.add_prefix('1.0.0.0/24', 'reservation', 'test', pool_id=pool1.id)
        p2 = th.add_prefix('2001:db8::/48', 'reservation', 'test', pool_id=pool1.id)

        p1.prefix = '1.0.0.0/25'
        p1.save()
        p2.prefix = '2001:db8::/64'
        p2.save()

        # check stats for pool1
        res = Pool.list({ 'id': pool1.id })
        # ipv4
        self.assertEqual(1, res[0].member_prefixes_v4)
        self.assertEqual(0, res[0].used_prefixes_v4)
        self.assertEqual(128, res[0].total_addresses_v4)
        self.assertEqual(0, res[0].used_addresses_v4)
        self.assertEqual(128, res[0].free_addresses_v4)
        # ipv6
        self.assertEqual(1, res[0].member_prefixes_v6)
        self.assertEqual(0, res[0].used_prefixes_v6)
        self.assertEqual(18446744073709551616, res[0].total_addresses_v6)
        self.assertEqual(0, res[0].used_addresses_v6)
        self.assertEqual(18446744073709551616, res[0].free_addresses_v6)


    def test_stats3(self):
        """ Check total stats are correct when adding and removing child prefixes from pool
        """
        th = TestHelper()

        # add a pool
        pool1 = th.add_pool('test', 'assignment', 31, 112)

        # add some members to the pool
        p1 = th.add_prefix('1.0.0.0/24', 'reservation', 'test', pool_id=pool1.id)
        p2 = th.add_prefix('2001:db8::/48', 'reservation', 'test', pool_id=pool1.id)

        # add child from pool
        pc1 = th.add_prefix_from_pool(pool1, 4, 'foo')
        pc2 = th.add_prefix_from_pool(pool1, 6, 'foo')

        # check stats for pool1
        res = Pool.list({ 'id': pool1.id })
        # ipv4
        self.assertEqual(1, res[0].member_prefixes_v4)
        self.assertEqual(1, res[0].used_prefixes_v4)
        self.assertEqual(256, res[0].total_addresses_v4)
        self.assertEqual(2, res[0].used_addresses_v4)
        self.assertEqual(254, res[0].free_addresses_v4)
        # ipv6
        self.assertEqual(1, res[0].member_prefixes_v6)
        self.assertEqual(1, res[0].used_prefixes_v6)
        self.assertEqual(1208925819614629174706176, res[0].total_addresses_v6)
        self.assertEqual(65536, res[0].used_addresses_v6)
        self.assertEqual(1208925819614629174640640, res[0].free_addresses_v6)

        # remove child prefixes
        pc1.remove()
        pc2.remove()

        # check stats for pool1
        res = Pool.list({ 'id': pool1.id })
        # ipv4
        self.assertEqual(1, res[0].member_prefixes_v4)
        self.assertEqual(0, res[0].used_prefixes_v4)
        self.assertEqual(256, res[0].total_addresses_v4)
        self.assertEqual(0, res[0].used_addresses_v4)
        self.assertEqual(256, res[0].free_addresses_v4)
        # ipv6
        self.assertEqual(1, res[0].member_prefixes_v6)
        self.assertEqual(0, res[0].used_prefixes_v6)
        self.assertEqual(1208925819614629174706176, res[0].total_addresses_v6)
        self.assertEqual(0, res[0].used_addresses_v6)
        self.assertEqual(1208925819614629174706176, res[0].free_addresses_v6)


    def test_stats4(self):
        """ Check total stats are correct when modifying child prefixes in pool
        """
        th = TestHelper()

        # add a pool
        pool1 = th.add_pool('test', 'assignment', 31, 112)

        # add some members to the pool
        p1 = th.add_prefix('1.0.0.0/24', 'reservation', 'test', pool_id=pool1.id)
        p2 = th.add_prefix('2001:db8::/48', 'reservation', 'test', pool_id=pool1.id)

        # add child from pool
        pc1 = th.add_prefix_from_pool(pool1, 4, 'foo')
        pc2 = th.add_prefix_from_pool(pool1, 6, 'foo')

        # change child prefix and size and make sure stats are updated correctly
        pc1.prefix = '1.0.0.128/25'
        pc1.save()
        pc2.prefix = '2001:db8:0:1::/64'
        pc2.save()

        # check stats for pool1
        res = Pool.list({ 'id': pool1.id })
        # ipv4
        self.assertEqual(1, res[0].member_prefixes_v4)
        self.assertEqual(1, res[0].used_prefixes_v4)
        self.assertEqual(256, res[0].total_addresses_v4)
        self.assertEqual(128, res[0].used_addresses_v4)
        self.assertEqual(128, res[0].free_addresses_v4)
        # ipv6
        self.assertEqual(1, res[0].member_prefixes_v6)
        self.assertEqual(1, res[0].used_prefixes_v6)
        self.assertEqual(1208925819614629174706176, res[0].total_addresses_v6)
        self.assertEqual(18446744073709551616, res[0].used_addresses_v6)
        self.assertEqual(1208907372870555465154560, res[0].free_addresses_v6)


    def test_stats5(self):
        """ Check total stats are correct when adding and removing member prefix with childs from pool

            This is trickier as there is now a child in the pool that needs to
            be accounted for.
        """
        th = TestHelper()

        # add a pool
        pool1 = th.add_pool('test', 'assignment', 31, 112)

        # add some members to the pool
        p1 = th.add_prefix('1.0.0.0/24', 'reservation', 'test', pool_id=pool1.id)
        p2 = th.add_prefix('2.0.0.0/24', 'reservation', 'test', pool_id=pool1.id)
        p3 = th.add_prefix('2001:db8:1::/48', 'reservation', 'test', pool_id=pool1.id)
        p4 = th.add_prefix('2001:db8:2::/48', 'reservation', 'test', pool_id=pool1.id)

        # add child from pool
        pc1 = th.add_prefix_from_pool(pool1, 4, 'foo')
        pc2 = th.add_prefix_from_pool(pool1, 6, 'foo')

        # remove first member prefixes from pool
        p1.pool = None
        p1.save()
        p3.pool = None
        p3.save()

        # check stats for pool1
        res = Pool.list({ 'id': pool1.id })
        # ipv4
        self.assertEqual(1, res[0].member_prefixes_v4)
        self.assertEqual(0, res[0].used_prefixes_v4)
        self.assertEqual(256, res[0].total_addresses_v4)
        self.assertEqual(0, res[0].used_addresses_v4)
        self.assertEqual(256, res[0].free_addresses_v4)
        # ipv6
        self.assertEqual(1, res[0].member_prefixes_v6)
        self.assertEqual(0, res[0].used_prefixes_v6)
        self.assertEqual(1208925819614629174706176, res[0].total_addresses_v6)
        self.assertEqual(0, res[0].used_addresses_v6)
        self.assertEqual(1208925819614629174706176, res[0].free_addresses_v6)

        # readd prefixes to pool
        p1.pool = pool1
        p1.save()
        p3.pool = pool1
        p3.save()

        # check stats for pool1
        res = Pool.list({ 'id': pool1.id })
        # ipv4
        self.assertEqual(2, res[0].member_prefixes_v4)
        self.assertEqual(1, res[0].used_prefixes_v4)
        self.assertEqual(512, res[0].total_addresses_v4)
        self.assertEqual(2, res[0].used_addresses_v4)
        self.assertEqual(510, res[0].free_addresses_v4)
        # ipv6
        self.assertEqual(2, res[0].member_prefixes_v6)
        self.assertEqual(1, res[0].used_prefixes_v6)
        self.assertEqual(2417851639229258349412352, res[0].total_addresses_v6)
        self.assertEqual(65536, res[0].used_addresses_v6)
        self.assertEqual(2417851639229258349346816, res[0].free_addresses_v6)



    def test_stats6(self):
        """ Check total stats are correct when adding member prefix with childs to pool
        """
        th = TestHelper()

        # add a pool
        pool1 = th.add_pool('test', 'assignment', 31, 112)

        # add some members to the pool
        p1 = th.add_prefix('1.0.0.0/24', 'reservation', 'test', pool_id=pool1.id)
        p2 = th.add_prefix('2.0.0.0/24', 'reservation', 'test', pool_id=pool1.id)
        p3 = th.add_prefix('2001:db8::/48', 'reservation', 'test', pool_id=pool1.id)
        p4 = th.add_prefix('2001:db8:1::/48', 'reservation', 'test', pool_id=pool1.id)

        # add child from pool
        pc1 = th.add_prefix_from_pool(pool1, 4, 'foo')
        pc2 = th.add_prefix_from_pool(pool1, 6, 'foo')



class TestPrefixStatistics(unittest.TestCase):
    """ Test calculation of statistics for prefixes
    """

    def setUp(self):
        """ Test setup, which essentially means to empty the database
        """
        TestHelper.clear_database()


    def test_stats1(self):
        """ Check stats are correct when adding prefix
        """
        th = TestHelper()
        # add a top level prefix
        p1 = th.add_prefix('1.0.0.0/24', 'assignment', 'test')

        # check stats for p1
        res = Prefix.smart_search('1.0.0.0/24', {})
        self.assertEqual(256, res['result'][0].total_addresses)
        self.assertEqual(0, res['result'][0].used_addresses)
        self.assertEqual(256, res['result'][0].free_addresses)

        # add a covering supernet around p1
        p2 = th.add_prefix('1.0.0.0/20', 'reservation', 'bar')

        # check stats for p2, our new top level prefix
        res = Prefix.smart_search('1.0.0.0/20', {})
        self.assertEqual(4096, res['result'][0].total_addresses)
        self.assertEqual(256, res['result'][0].used_addresses)
        self.assertEqual(3840, res['result'][0].free_addresses)


    def test_stats2(self):
        """ Check stats are correct when enlarging prefix
        """
        th = TestHelper()
        # add a top level prefix
        p1 = th.add_prefix('1.0.0.0/24', 'assignment', 'test')
        p2 = th.add_prefix('1.0.7.0/24', 'assignment', 'test')

        # add a covering supernet around p1
        p3 = th.add_prefix('1.0.0.0/22', 'reservation', 'bar')

        # check that p3 looks good
        res = Prefix.smart_search('1.0.0.0/22', {})
        self.assertEqual(1024, res['result'][0].total_addresses)
        self.assertEqual(256, res['result'][0].used_addresses)
        self.assertEqual(768, res['result'][0].free_addresses)
        # now move our supernet, so we see that the update thingy works
        p3.prefix = '1.0.0.0/21'
        p3.save()

        # check stats for p2, our new top level prefix
        res = Prefix.smart_search('1.0.0.0/21', {})
        self.assertEqual(2048, res['result'][0].total_addresses)
        self.assertEqual(512, res['result'][0].used_addresses)
        self.assertEqual(1536, res['result'][0].free_addresses)


    def test_stats3(self):
        """ Check stats are correct when shrinking prefix
        """
        th = TestHelper()
        # add a top level prefix
        p1 = th.add_prefix('1.0.0.0/24', 'assignment', 'test')
        p2 = th.add_prefix('1.0.7.0/24', 'assignment', 'test')

        # add a covering supernet around p1
        p3 = th.add_prefix('1.0.0.0/21', 'reservation', 'bar')

        # check that p3 looks good
        res = Prefix.smart_search('1.0.0.0/21', {})
        self.assertEqual(2048, res['result'][0].total_addresses)
        self.assertEqual(512, res['result'][0].used_addresses)
        self.assertEqual(1536, res['result'][0].free_addresses)

        # now move our supernet, so we see that the update thingy works
        p3.prefix = '1.0.0.0/22'
        p3.save()

        # check stats for p2, our new top level prefix
        res = Prefix.smart_search('1.0.0.0/22', {})
        self.assertEqual(1024, res['result'][0].total_addresses)
        self.assertEqual(256, res['result'][0].used_addresses)
        self.assertEqual(768, res['result'][0].free_addresses)


    def test_stats4(self):
        """ Check stats are correct when moving prefix
        """
        th = TestHelper()
        # add a top level prefix
        p1 = th.add_prefix('1.0.0.0/24', 'assignment', 'test')
        p2 = th.add_prefix('2.0.0.0/25', 'reservation', 'bar')
        p2 = th.add_prefix('1.0.0.0/23', 'reservation', 'bar')
        # now move our supernet, so we see that the update thingy works
        p2.prefix = '2.0.0.0/22'
        p2.save()

        # check stats for p2, our new top level prefix
        res = Prefix.smart_search('2.0.0.0/22', {})
        self.assertEqual(1024, res['result'][0].total_addresses)
        self.assertEqual(128, res['result'][0].used_addresses)
        self.assertEqual(896, res['result'][0].free_addresses)



    def test_stats5(self):
        """ Add prefixes within other prefix and verify parent prefix has correct statistics
        """
        th = TestHelper()
        # add a top level prefix
        p1 = th.add_prefix('1.0.0.0/24', 'assignment', 'test')

        # check stats for p1
        res = Prefix.smart_search('1.0.0.0/24', {})
        self.assertEqual(256, res['result'][0].total_addresses)
        self.assertEqual(0, res['result'][0].used_addresses)
        self.assertEqual(256, res['result'][0].free_addresses)

        # add a host in our top prefix
        p2 = th.add_prefix('1.0.0.1/32', 'host', 'bar')

        # check stats for p1, our top level prefix
        res = Prefix.smart_search('1.0.0.0/24', {})
        self.assertEqual(256, res['result'][0].total_addresses)
        self.assertEqual(1, res['result'][0].used_addresses)
        self.assertEqual(255, res['result'][0].free_addresses)

        # check stats for p2, our new host prefix
        res = Prefix.smart_search('1.0.0.1/32', {})
        self.assertEqual(1, res['result'][0].total_addresses)
        self.assertEqual(1, res['result'][0].used_addresses)
        self.assertEqual(0, res['result'][0].free_addresses)


    def test_stats6(self):
        """ Remove prefix and check old parent is correctly updated
        """
        th = TestHelper()

        # p1 children are p2 (which covers p3 and p4) and p5
        p1 = th.add_prefix('1.0.0.0/20', 'reservation', 'test')
        p2 = th.add_prefix('1.0.0.0/22', 'reservation', 'test')
        p3 = th.add_prefix('1.0.0.0/24', 'reservation', 'test')
        p4 = th.add_prefix('1.0.1.0/24', 'reservation', 'test')
        p5 = th.add_prefix('1.0.7.0/24', 'reservation', 'test')

        # moving p2 means that p1 get p3, p4 and p5 as children
        p2.prefix = '2.0.0.0/22'
        p2.save()

        # check stats for p1
        res = Prefix.smart_search('1.0.0.0/20', {})
        self.assertEqual(4096, res['result'][0].total_addresses)
        self.assertEqual(768, res['result'][0].used_addresses)
        self.assertEqual(3328, res['result'][0].free_addresses)

        # moving back p2 which means that p1 get p2 and p5 as children
        p2.prefix = '1.0.0.0/22'
        p2.save()

        # check stats for p1
        res = Prefix.smart_search('1.0.0.0/20', {})
        self.assertEqual(4096, res['result'][0].total_addresses)
        self.assertEqual(1280, res['result'][0].used_addresses)
        self.assertEqual(2816, res['result'][0].free_addresses)
        # TODO: check what happens when a prefix is moved several indents,
        # something like 1.3.3.0/24 to 1.3.0.0/16 where 1.3.0.0/20 and /21 is in
        # between



    def test_stats7(self):
        """ Enlarge / shrink prefix over several indent levels
        """
        th = TestHelper()

        # p1 children are p2 (which covers p3 and p4) and p5
        p1 = th.add_prefix('1.0.0.0/16', 'reservation', 'test')
        p2 = th.add_prefix('1.0.0.0/22', 'reservation', 'test')
        p3 = th.add_prefix('1.0.0.0/23', 'reservation', 'FOO')
        p4 = th.add_prefix('1.0.0.0/24', 'reservation', 'test')
        p5 = th.add_prefix('1.0.1.0/24', 'reservation', 'test')
        p6 = th.add_prefix('1.0.2.0/24', 'reservation', 'test')
        p7 = th.add_prefix('1.0.3.0/24', 'reservation', 'test')

        # enlarge p3 so that it covers p2, ie moved up several indent levels
        p3.prefix = '1.0.0.0/21'
        p3.save()

        # check stats for p3
        res = Prefix.smart_search('1.0.0.0/21', {})
        self.assertEqual(2048, res['result'][0].total_addresses)
        self.assertEqual(1024, res['result'][0].used_addresses)
        self.assertEqual(1024, res['result'][0].free_addresses)

        # move back p3
        p3.prefix = '1.0.0.0/23'
        p3.save()

        # check stats for p3
        res = Prefix.smart_search('1.0.0.0/23', {})
        self.assertEqual(512, res['result'][0].total_addresses)
        self.assertEqual(512, res['result'][0].used_addresses)
        self.assertEqual(0, res['result'][0].free_addresses)




class TestVrfStatistics(unittest.TestCase):
    """ Test calculation of statistics for VRFs
    """

    def setUp(self):
        """ Test setup, which essentially means to empty the database
        """
        TestHelper.clear_database()


    def test_stats1(self):
        """ Check stats are correct when adding and removing prefixes
        """
        th = TestHelper()

        # add some top level prefixes to the default VRF
        p1 = th.add_prefix('1.0.0.0/24', 'reservation', 'test')
        p2 = th.add_prefix('2.0.0.0/24', 'reservation', 'test')
        p3 = th.add_prefix('2001:db8:1::/48', 'reservation', 'test')
        p4 = th.add_prefix('2001:db8:2::/48', 'reservation', 'test')

        # check stats for VRF
        res = VRF.get(0)
        # ipv4
        self.assertEqual(2, res.num_prefixes_v4)
        self.assertEqual(512, res.total_addresses_v4)
        self.assertEqual(0, res.used_addresses_v4)
        self.assertEqual(512, res.free_addresses_v4)
        # ipv6
        self.assertEqual(2, res.num_prefixes_v6)
        self.assertEqual(2417851639229258349412352, res.total_addresses_v6)
        self.assertEqual(0, res.used_addresses_v6)
        self.assertEqual(2417851639229258349412352, res.free_addresses_v6)

        # remove some prefixes
        p1.remove()
        p3.remove()

        # check stats for VRF
        res = VRF.get(0)
        # ipv4
        self.assertEqual(1, res.num_prefixes_v4)
        self.assertEqual(256, res.total_addresses_v4)
        self.assertEqual(0, res.used_addresses_v4)
        self.assertEqual(256, res.free_addresses_v4)
        # ipv6
        self.assertEqual(1, res.num_prefixes_v6)
        self.assertEqual(1208925819614629174706176, res.total_addresses_v6)
        self.assertEqual(0, res.used_addresses_v6)
        self.assertEqual(1208925819614629174706176, res.free_addresses_v6)


    def test_stats2(self):
        """ Check stats are correct when adding and removing prefixes
        """
        th = TestHelper()

        # add some top level prefixes to the default VRF
        p1 = th.add_prefix('1.0.0.0/24', 'reservation', 'test')
        p2 = th.add_prefix('1.0.0.128/25', 'assignment', 'test')
        p3 = th.add_prefix('2001:db8:1::/48', 'reservation', 'test')
        p4 = th.add_prefix('2001:db8:1:1::/64', 'reservation', 'test')

        # check stats for VRF
        res = VRF.get(0)
        # ipv4
        self.assertEqual(2, res.num_prefixes_v4)
        self.assertEqual(256, res.total_addresses_v4)
        self.assertEqual(128, res.used_addresses_v4)
        self.assertEqual(128, res.free_addresses_v4)
        # ipv6
        self.assertEqual(2, res.num_prefixes_v6)
        self.assertEqual(1208925819614629174706176, res.total_addresses_v6)
        self.assertEqual(18446744073709551616, res.used_addresses_v6)
        self.assertEqual(1208907372870555465154560, res.free_addresses_v6)

        # remove some prefixes
        p1.remove()
        p3.remove()

        # check stats for VRF
        res = VRF.get(0)
        # ipv4
        self.assertEqual(1, res.num_prefixes_v4)
        self.assertEqual(128, res.total_addresses_v4)
        self.assertEqual(0, res.used_addresses_v4)
        self.assertEqual(128, res.free_addresses_v4)
        # ipv6
        self.assertEqual(1, res.num_prefixes_v6)
        self.assertEqual(18446744073709551616, res.total_addresses_v6)
        self.assertEqual(0, res.used_addresses_v6)
        self.assertEqual(18446744073709551616, res.free_addresses_v6)


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


