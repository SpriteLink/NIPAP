#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Most of the tests here are performed via Pynipap which makes it a lot easier
# to test things given that we receive python objects and not just basic data
# structures like those returned in xmlrpc.py. If you want to write a new test,
# it is recommended that you place it here rather than in xmlrpc.py.
#

import datetime
import logging
import unittest
import sys
import time
sys.path.insert(0, '..')
sys.path.insert(0, '../pynipap')
sys.path.insert(0, '../nipap')
sys.path.insert(0, '../nipap-cli')

import nipap.backend
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


    def add_prefix(self, prefix, type, description, tags=None, pool_id=None):

        if tags is None:
            tags = []

        p = Prefix()
        p.prefix = prefix
        p.type = type
        p.status = 'assigned'
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
        p.status = 'assigned'

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



class TestPrefixExpires(unittest.TestCase):
    """ Test expires related stuff
    """
    def setUp(self):
        """ Test setup, which essentially means to empty the database
        """
        TestHelper.clear_database()


    def test_expires1(self):
        th = TestHelper()

        # make sure default is infinite expiry time
        p1 = th.add_prefix('1.3.0.0/16', 'reservation', 'test')
        self.assertEqual(p1.expires, None)

        # test absolute time by creating local datetime object and sending.
        # set expires to now but skip the microseconds as the backend doesn't
        # support that precision
        now = datetime.datetime.now().replace(microsecond = 0)
        p1.expires = now
        p1.save()
        self.assertEqual(p1.expires, now)

        # test the relative time parsing of the backend by setting "tomorrow",
        # which parsedatetime interprets as 09:00 the next day
        #
        tomorrow = datetime.datetime.now().replace(hour = 9, minute = 0,
                second = 0, microsecond = 0) + datetime.timedelta(days = 1)
        p1.expires = "tomorrow"
        p1.save()
        self.assertEqual(p1.expires, tomorrow)



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
        p.status = 'assigned'
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


    def test_tags1(self):
        """ Verify tags are correctly inherited
        """
        th = TestHelper()

        # add to "top level" prefix, each with a unique tag
        p1 = th.add_prefix('1.0.0.0/8', 'reservation', 'test', tags=['a'])
        p2 = th.add_prefix('1.0.0.0/9', 'reservation', 'test')
        p3 = th.add_prefix('1.0.0.0/10', 'reservation', 'test')

        # p3 should have inherited_tags = ['a'] from p1
        res = Prefix.smart_search('1.0.0.0/10', {})
        self.assertEqual(['a'], res['result'][0].inherited_tags.keys())

        p4 = th.add_prefix('1.0.0.0/24', 'reservation', 'test')
        p5 = th.add_prefix('1.0.0.0/23', 'reservation', 'test')
        p6 = th.add_prefix('1.0.0.0/22', 'reservation', 'test')

        # p4 should have inherited_tags = ['a'] from p1
        res = Prefix.smart_search('1.0.0.0/24', {})
        self.assertEqual(['a'], res['result'][0].inherited_tags.keys())

        # change tags on top level prefix
        p1.tags = ['b']
        p1.save()

        # p4 should have inherited_tags = ['a'] from p1
        res = Prefix.smart_search('1.0.0.0/8', {})
        self.assertEqual([], res['result'][0].inherited_tags.keys())
        self.assertEqual(['b'], res['result'][1].inherited_tags.keys())
        self.assertEqual(['b'], res['result'][2].inherited_tags.keys())
        self.assertEqual(['b'], res['result'][3].inherited_tags.keys())
        self.assertEqual(['b'], res['result'][4].inherited_tags.keys())
        self.assertEqual(['b'], res['result'][5].inherited_tags.keys())




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


    def test_children3(self):
        """ Check children are correct when adding prefix
        """
        th = TestHelper()
        # add a top level prefix
        p1 = th.add_prefix('1.0.0.0/24', 'assignment', 'test')

        # check stats for p1
        res = Prefix.smart_search('1.0.0.0/24', {})
        self.assertEqual(0, res['result'][0].children)

        # add a covering supernet around p1
        p2 = th.add_prefix('1.0.0.0/20', 'reservation', 'bar')

        # check stats for p2, our new top level prefix
        res = Prefix.smart_search('1.0.0.0/20', {})
        self.assertEqual(1, res['result'][0].children)


    def test_children4(self):
        """ Check children are correct when enlarging prefix
        """
        th = TestHelper()
        # add a top level prefix
        p1 = th.add_prefix('1.0.0.0/24', 'assignment', 'test')
        p2 = th.add_prefix('1.0.7.0/24', 'assignment', 'test')

        # add a covering supernet around p1
        p3 = th.add_prefix('1.0.0.0/22', 'reservation', 'bar')

        # check that p3 looks good
        res = Prefix.smart_search('1.0.0.0/22', {})
        self.assertEqual(1, res['result'][0].children)
        # now move our supernet, so we see that the update thingy works
        p3.prefix = '1.0.0.0/21'
        p3.save()

        # check stats for p2, our new top level prefix
        res = Prefix.smart_search('1.0.0.0/21', {})
        self.assertEqual(2, res['result'][0].children)


    def test_children5(self):
        """ Check children are correct when shrinking prefix
        """
        th = TestHelper()
        # add a top level prefix
        p1 = th.add_prefix('1.0.0.0/24', 'assignment', 'test')
        p2 = th.add_prefix('1.0.7.0/24', 'assignment', 'test')

        # add a covering supernet around p1 and p2
        p3 = th.add_prefix('1.0.0.0/21', 'reservation', 'bar')

        # check that p3 looks good
        res = Prefix.smart_search('1.0.0.0/21', {})
        self.assertEqual(2, res['result'][0].children)

        # shrink our supernet, so it only covers p1
        p3.prefix = '1.0.0.0/22'
        p3.save()

        # check that p3 only covers p1
        res = Prefix.smart_search('1.0.0.0/22', {})
        self.assertEqual(1, res['result'][0].children)



    def test_children6(self):
        """ Check children are correct when moving prefix
        """
        th = TestHelper()
        # add a top level prefix
        p1 = th.add_prefix('1.0.0.0/24', 'assignment', 'test')
        p2 = th.add_prefix('2.0.0.0/25', 'reservation', 'bar')
        # now move our supernet, so we see that the update thingy works
        p2.prefix = '2.0.0.0/22'
        p2.save()

        # check stats for p2, we shouldn't see children based on our old
        # position (2.0.0.0/25)
        res = Prefix.smart_search('2.0.0.0/22', {})
        self.assertEqual(0, res['result'][0].children)

        # now move our supernet, so we see that the update thingy works
        p2.prefix = '1.0.0.0/22'
        p2.save()

        # check stats for p2, we should get p1 as child
        res = Prefix.smart_search('1.0.0.0/22', {})
        self.assertEqual(1, res['result'][0].children)



    def test_children7(self):
        """ Add prefixes within other prefix and verify parent prefix has correct children
        """
        th = TestHelper()
        # add a top level prefix
        p1 = th.add_prefix('1.0.0.0/24', 'assignment', 'test')

        # check stats for p1
        res = Prefix.smart_search('1.0.0.0/24', {})
        self.assertEqual(0, res['result'][0].children)

        # add a host in our top prefix
        p2 = th.add_prefix('1.0.0.1/32', 'host', 'bar')

        # check stats for p1, our top level prefix
        res = Prefix.smart_search('1.0.0.0/24', {})
        self.assertEqual(1, res['result'][0].children)

        # check stats for p2, our new host prefix
        res = Prefix.smart_search('1.0.0.1/32', {})
        self.assertEqual(0, res['result'][0].children)


    def test_children8(self):
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
        self.assertEqual(3, res['result'][0].children)

        # moving back p2 which means that p1 get p2 and p5 as children
        p2.prefix = '1.0.0.0/22'
        p2.save()

        # check stats for p1
        res = Prefix.smart_search('1.0.0.0/20', {})
        self.assertEqual(2, res['result'][0].children)


    def test_children9(self):
        """ Move prefix several indent steps and check children is correct
        """
        th = TestHelper()

        # tree of prefixes
        p1 = th.add_prefix('1.0.0.0/20', 'reservation', 'test')
        p2 =  th.add_prefix('1.0.0.0/21', 'reservation', 'test')
        p3 =   th.add_prefix('1.0.0.0/22', 'reservation', 'test')
        p4 =    th.add_prefix('1.0.0.0/23', 'reservation', 'test')
        p5 =     th.add_prefix('1.0.0.0/24', 'reservation', 'test')
        p6 =    th.add_prefix('1.0.2.0/24', 'reservation', 'test')
        p7 =   th.add_prefix('1.0.4.0/22', 'reservation', 'test')

        # check stats for p2
        res = Prefix.smart_search('1.0.0.0/21', {})
        self.assertEqual(2, res['result'][0].children)

        # move p3 outside of the tree
        p3.prefix = '2.0.0.0/22'
        p3.save()

        # check stats for p2
        res = Prefix.smart_search('1.0.0.0/21', {})
        self.assertEqual(3, res['result'][0].children)

        # move p3 into the tree again
        p3.prefix = '1.0.0.0/22'
        p3.save()

        # check stats for p2
        res = Prefix.smart_search('1.0.0.0/21', {})
        self.assertEqual(2, res['result'][0].children)



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
        p.status = 'assigned'
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
        self.assertEqual(None, res[0].free_prefixes_v4)
        self.assertEqual(None, res[0].total_prefixes_v4)
        self.assertEqual(0, res[0].total_addresses_v4)
        self.assertEqual(0, res[0].used_addresses_v4)
        self.assertEqual(0, res[0].free_addresses_v4)
        # ipv6
        self.assertEqual(0, res[0].member_prefixes_v6)
        self.assertEqual(0, res[0].used_prefixes_v6)
        self.assertEqual(None, res[0].free_prefixes_v6)
        self.assertEqual(None, res[0].total_prefixes_v6)
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
        self.assertEqual(256, res[0].free_prefixes_v4)
        self.assertEqual(256, res[0].total_prefixes_v4)
        self.assertEqual(512, res[0].total_addresses_v4)
        self.assertEqual(0, res[0].used_addresses_v4)
        self.assertEqual(512, res[0].free_addresses_v4)
        # ipv6
        self.assertEqual(2, res[0].member_prefixes_v6)
        self.assertEqual(0, res[0].used_prefixes_v6)
        self.assertEqual(36893488147419103232, res[0].free_prefixes_v6)
        self.assertEqual(36893488147419103232, res[0].total_prefixes_v6)
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
        self.assertEqual(128, res[0].free_prefixes_v4)
        self.assertEqual(128, res[0].total_prefixes_v4)
        self.assertEqual(256, res[0].total_addresses_v4)
        self.assertEqual(0, res[0].used_addresses_v4)
        self.assertEqual(256, res[0].free_addresses_v4)
        # ipv6
        self.assertEqual(1, res[0].member_prefixes_v6)
        self.assertEqual(0, res[0].used_prefixes_v6)
        self.assertEqual(18446744073709551616, res[0].free_prefixes_v6)
        self.assertEqual(18446744073709551616, res[0].total_prefixes_v6)
        self.assertEqual(1208925819614629174706176, res[0].total_addresses_v6)
        self.assertEqual(0, res[0].used_addresses_v6)
        self.assertEqual(1208925819614629174706176, res[0].free_addresses_v6)

        pool1.ipv4_default_prefix_length = 30
        pool1.ipv6_default_prefix_length = 96
        pool1.save()

        # check stats for pool1
        res = Pool.list({ 'id': pool1.id })
        # ipv4
        self.assertEqual(1, res[0].member_prefixes_v4)
        self.assertEqual(0, res[0].used_prefixes_v4)
        self.assertEqual(64, res[0].free_prefixes_v4)
        self.assertEqual(64, res[0].total_prefixes_v4)
        self.assertEqual(256, res[0].total_addresses_v4)
        self.assertEqual(0, res[0].used_addresses_v4)
        self.assertEqual(256, res[0].free_addresses_v4)
        # ipv6
        self.assertEqual(1, res[0].member_prefixes_v6)
        self.assertEqual(0, res[0].used_prefixes_v6)
        self.assertEqual(281474976710656, res[0].free_prefixes_v6)
        self.assertEqual(281474976710656, res[0].total_prefixes_v6)
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
        self.assertEqual(64, res[0].free_prefixes_v4)
        self.assertEqual(64, res[0].total_prefixes_v4)
        self.assertEqual(128, res[0].total_addresses_v4)
        self.assertEqual(0, res[0].used_addresses_v4)
        self.assertEqual(128, res[0].free_addresses_v4)
        # ipv6
        self.assertEqual(1, res[0].member_prefixes_v6)
        self.assertEqual(0, res[0].used_prefixes_v6)
        self.assertEqual(281474976710656, res[0].free_prefixes_v6)
        self.assertEqual(281474976710656, res[0].total_prefixes_v6)
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
        self.assertEqual(127, res[0].free_prefixes_v4)
        self.assertEqual(128, res[0].total_prefixes_v4)
        self.assertEqual(256, res[0].total_addresses_v4)
        self.assertEqual(2, res[0].used_addresses_v4)
        self.assertEqual(254, res[0].free_addresses_v4)
        # ipv6
        self.assertEqual(1, res[0].member_prefixes_v6)
        self.assertEqual(1, res[0].used_prefixes_v6)
        self.assertEqual(18446744073709551615, res[0].free_prefixes_v6)
        self.assertEqual(18446744073709551616, res[0].total_prefixes_v6)
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
        self.assertEqual(128, res[0].free_prefixes_v4)
        self.assertEqual(128, res[0].total_prefixes_v4)
        self.assertEqual(256, res[0].total_addresses_v4)
        self.assertEqual(0, res[0].used_addresses_v4)
        self.assertEqual(256, res[0].free_addresses_v4)
        # ipv6
        self.assertEqual(1, res[0].member_prefixes_v6)
        self.assertEqual(0, res[0].used_prefixes_v6)
        self.assertEqual(18446744073709551616, res[0].free_prefixes_v6)
        self.assertEqual(18446744073709551616, res[0].total_prefixes_v6)
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
        self.assertEqual(64, res[0].free_prefixes_v4)
        self.assertEqual(65, res[0].total_prefixes_v4)
        self.assertEqual(256, res[0].total_addresses_v4)
        self.assertEqual(128, res[0].used_addresses_v4)
        self.assertEqual(128, res[0].free_addresses_v4)
        # ipv6
        self.assertEqual(1, res[0].member_prefixes_v6)
        self.assertEqual(1, res[0].used_prefixes_v6)
        self.assertEqual(18446462598732840960, res[0].free_prefixes_v6)
        self.assertEqual(18446462598732840961, res[0].total_prefixes_v6)
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
        self.assertEqual(128, res[0].free_prefixes_v4)
        self.assertEqual(128, res[0].total_prefixes_v4)
        self.assertEqual(256, res[0].total_addresses_v4)
        self.assertEqual(0, res[0].used_addresses_v4)
        self.assertEqual(256, res[0].free_addresses_v4)
        # ipv6
        self.assertEqual(1, res[0].member_prefixes_v6)
        self.assertEqual(0, res[0].used_prefixes_v6)
        self.assertEqual(18446744073709551616, res[0].free_prefixes_v6)
        self.assertEqual(18446744073709551616, res[0].total_prefixes_v6)
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
        self.assertEqual(255, res[0].free_prefixes_v4)
        self.assertEqual(256, res[0].total_prefixes_v4)
        self.assertEqual(512, res[0].total_addresses_v4)
        self.assertEqual(2, res[0].used_addresses_v4)
        self.assertEqual(510, res[0].free_addresses_v4)
        # ipv6
        self.assertEqual(2, res[0].member_prefixes_v6)
        self.assertEqual(1, res[0].used_prefixes_v6)
        self.assertEqual(36893488147419103231, res[0].free_prefixes_v6)
        self.assertEqual(36893488147419103232, res[0].total_prefixes_v6)
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

        # add a covering supernet around p1 and p2
        p3 = th.add_prefix('1.0.0.0/21', 'reservation', 'bar')

        # check that p3 looks good
        res = Prefix.smart_search('1.0.0.0/21', {})
        self.assertEqual(2048, res['result'][0].total_addresses)
        self.assertEqual(512, res['result'][0].used_addresses)
        self.assertEqual(1536, res['result'][0].free_addresses)

        # now move our supernet, so we see that the update thingy works
        p3.prefix = '1.0.0.0/22'
        p3.save()

        # check that p3 only covers p1
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
        # now move our supernet, so we see that the update thingy works
        p2.prefix = '2.0.0.0/22'
        p2.save()

        # check stats for p2, we shouldn't see stats based on our old position
        # (2.0.0.0/25)
        res = Prefix.smart_search('2.0.0.0/22', {})
        self.assertEqual(1024, res['result'][0].total_addresses)
        self.assertEqual(0, res['result'][0].used_addresses)
        self.assertEqual(1024, res['result'][0].free_addresses)



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


    def test_stats7(self):
        """ Move prefix several indent steps and check stats are correct
        """
        th = TestHelper()

        # tree of prefixes
        p1 = th.add_prefix('1.0.0.0/20', 'reservation', 'test')
        p2 =  th.add_prefix('1.0.0.0/21', 'reservation', 'test')
        p3 =   th.add_prefix('1.0.0.0/22', 'reservation', 'test')
        p4 =    th.add_prefix('1.0.0.0/23', 'reservation', 'test')
        p5 =     th.add_prefix('1.0.0.0/24', 'reservation', 'test')
        p6 =    th.add_prefix('1.0.2.0/24', 'reservation', 'test')
        p7 =   th.add_prefix('1.0.4.0/22', 'reservation', 'test')

        # check stats for p2
        res = Prefix.smart_search('1.0.0.0/21', {})
        self.assertEqual(2048, res['result'][0].total_addresses)
        self.assertEqual(2048, res['result'][0].used_addresses)
        self.assertEqual(0, res['result'][0].free_addresses)

        # move p3 outside of the tree
        p3.prefix = '2.0.0.0/22'
        p3.save()

        # check stats for p2
        res = Prefix.smart_search('1.0.0.0/21', {})
        self.assertEqual(2048, res['result'][0].total_addresses)
        self.assertEqual(1792, res['result'][0].used_addresses)
        self.assertEqual(256, res['result'][0].free_addresses)

        # move p3 into the tree again
        p3.prefix = '1.0.0.0/22'
        p3.save()

        # check stats for p2
        res = Prefix.smart_search('1.0.0.0/21', {})
        self.assertEqual(2048, res['result'][0].total_addresses)
        self.assertEqual(2048, res['result'][0].used_addresses)
        self.assertEqual(0, res['result'][0].free_addresses)


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


    def test_stats8(self):
        """ Make sure stats are correct
        """
        # we ran into this problem with #590
        th = TestHelper()

        p1 = th.add_prefix('1.0.0.0/24', 'reservation', 'test')
        p2 = th.add_prefix('1.0.0.0/32', 'reservation', 'test')

        # check stats for p1
        res = Prefix.smart_search('1.0.0.0/24', {})
        self.assertEqual(256, res['result'][0].total_addresses)
        self.assertEqual(1, res['result'][0].used_addresses)
        self.assertEqual(255, res['result'][0].free_addresses)

        p3 = th.add_prefix('1.0.0.2/31', 'reservation', 'test')

        # check stats for p1
        res = Prefix.smart_search('1.0.0.0/24', {})
        self.assertEqual(256, res['result'][0].total_addresses)
        self.assertEqual(3, res['result'][0].used_addresses)
        self.assertEqual(253, res['result'][0].free_addresses)

        p3.prefix = '1.0.0.2/32'
        p3.save()

        # check stats for p1
        res = Prefix.smart_search('1.0.0.0/24', {})
        self.assertEqual(256, res['result'][0].total_addresses)
        self.assertEqual(2, res['result'][0].used_addresses)
        self.assertEqual(254, res['result'][0].free_addresses)



class TestVrf(unittest.TestCase):
    """ Test various VRF related things
    """

    def setUp(self):
        """ Test setup, which essentially means to empty the database
        """
        TestHelper.clear_database()


    def test_vrf1(self):
        """ Test VRF RT input values
        """

        v = VRF()
        v.name = "test-vrf"

        broken_values = [
                "foo",
                "123:foo",
                "foo:123",
                "123.456.789.123:123",
                "123.123.200. 1:123",
                " 123.456.789.123:123"
                ]

        for bv in broken_values:
            with self.assertRaisesRegexp(pynipap.NipapValueError, 'Invalid input for column rt'):
                v.rt = bv
                v.save()

        # valid value
        v.rt = "123:456"
        v.save()
        self.assertEqual("123:456", VRF.list({"name": "test-vrf"})[0].rt)

        # valid value but with whitespace which should be stripped
        v.rt = " 123:456"
        v.save()
        self.assertEqual("123:456", VRF.list({"name": "test-vrf"})[0].rt)

        # valid IP:id value
        v.rt = "123.123.123.123:456"
        v.save()
        self.assertEqual("123.123.123.123:456", VRF.list({"name": "test-vrf"})[0].rt)



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



class TestPrefixLastModified(unittest.TestCase):
    """ Test updates of the last modified value
    """

    def setUp(self):
        """ Test setup, which essentially means to empty the database
        """
        TestHelper.clear_database()

    def test1(self):
        """ The last_modified timestamp should be updated when the prefix is
            edited
        """
        th = TestHelper()
        p1 = th.add_prefix('1.3.0.0/16', 'reservation', 'test')
        # make sure added and last_modified are equal
        self.assertEqual(p1.added, p1.last_modified)

        # this is a bit silly, but as the last_modified time is returned with a
        # precision of seconds, we need to make sure that we fall on the next
        # second to actually notice that last_modified is not equal to added
        time.sleep(1)

        p1.description = 'updated description'
        p1.save()

        # last_modified should have a later timestamp than added
        self.assertNotEqual(p1.added, p1.last_modified)




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


class TestCliPrefixAutoType(unittest.TestCase):
    """ Test CLI prefix auto type guessing
    """
    def setUp(self):
        """ Test setup, which essentially means to empty the database
        """
        TestHelper.clear_database()


    def mock_cfg(self):
        import ConfigParser
        cfg = ConfigParser.ConfigParser()
        cfg.add_section('global')
        cfg.set('global', 'default_vrf_rt', '-')
        cfg.set('global', 'default_list_vrf_rt', 'all')
        return cfg


    def test_auto_type1(self):
        """ Test automatic prefix type guessing
        """
        from nipap_cli import nipap_cli
        from pynipap import NipapError
        nipap_cli.cfg = self.mock_cfg()

        th = TestHelper()
        expected = []
        # add a few prefixes
        expected.append([th.add_prefix('10.0.0.0/16', 'reservation', 'test').prefix, 'reservation'])
        expected.append([th.add_prefix('10.0.0.0/24', 'assignment', 'test').prefix, 'assignment'])

        opts = {
            'prefix': '10.0.0.0/8',
            'type': 'reservation',
            'description': 'root'
            }
        expected.insert(0, [opts['prefix'], opts['type']])
        nipap_cli.add_prefix({}, opts, {})

        result = [[p.prefix, p.type] for p in Prefix.smart_search('')['result']]

        self.assertEqual(expected, result)


    def test_auto_type2(self):
        """ Test automatic prefix type guessing
        """
        from nipap_cli import nipap_cli
        from pynipap import NipapError
        nipap_cli.cfg = self.mock_cfg()

        th = TestHelper()
        expected = []
        # add a few prefixes
        expected.append([th.add_prefix('10.0.0.0/16', 'reservation', 'test').prefix, 'reservation'])
        expected.append([th.add_prefix('10.0.0.0/24', 'assignment', 'test').prefix, 'assignment'])

        opts = {
            'prefix': '10.0.0.0/24',
            'description': 'host'
            }
        expected.append(['10.0.0.0/32', 'host'])
        nipap_cli.add_prefix({}, opts, {})

        result = [[p.prefix, p.type] for p in Prefix.smart_search('')['result']]

        self.assertEqual(expected, result)


    def test_auto_type3(self):
        """ Test automatic prefix type guessing
        """
        from nipap_cli import nipap_cli
        from pynipap import NipapError
        nipap_cli.cfg = self.mock_cfg()

        th = TestHelper()
        expected = []
        # add a few prefixes
        expected.append([th.add_prefix('10.0.0.0/16', 'reservation', 'test').prefix, 'reservation'])
        expected.append([th.add_prefix('10.0.0.0/24', 'assignment', 'test').prefix, 'assignment'])

        opts = {
            'prefix': '10.0.0.0',
            'description': 'host'
            }
        expected.append([opts['prefix'] + '/32', 'host'])
        nipap_cli.add_prefix({}, opts, {})

        result = [[p.prefix, p.type] for p in Prefix.smart_search('')['result']]

        self.assertEqual(expected, result)


    def test_auto_type4(self):
        """ Test automatic prefix type guessing
        """
        from nipap_cli import nipap_cli
        from pynipap import NipapError
        nipap_cli.cfg = self.mock_cfg()

        th = TestHelper()
        expected = []
        # add a few prefixes
        expected.append([th.add_prefix('10.0.0.0/16', 'reservation', 'test').prefix, 'reservation'])
        expected.append([th.add_prefix('10.0.0.0/24', 'assignment', 'test').prefix, 'assignment'])

        opts = {
            'prefix': '10.0.0.1/24',
            'description': 'host'
            }
        expected.append(['10.0.0.1/32', 'host'])
        nipap_cli.add_prefix({}, opts, {})

        result = [[p.prefix, p.type] for p in Prefix.smart_search('')['result']]

        self.assertEqual(expected, result)


    def test_auto_type5(self):
        """ Test automatic prefix type guessing
        """
        from nipap_cli import nipap_cli
        from pynipap import NipapError
        nipap_cli.cfg = self.mock_cfg()

        th = TestHelper()
        expected = []
        # add a few prefixes
        expected.append([th.add_prefix('10.0.0.0/16', 'reservation', 'test').prefix, 'reservation'])
        expected.append([th.add_prefix('10.0.0.0/24', 'assignment', 'test').prefix, 'assignment'])

        opts = {
            'prefix': '10.0.0.1',
            'description': 'host'
            }
        expected.append([opts['prefix'] + '/32', 'host'])
        nipap_cli.add_prefix({}, opts, {})

        result = [[p.prefix, p.type] for p in Prefix.smart_search('')['result']]

        self.assertEqual(expected, result)


    def test_auto_type6(self):
        """ Test automatic prefix type guessing
        """
        from nipap_cli import nipap_cli
        from pynipap import NipapError
        nipap_cli.cfg = self.mock_cfg()

        th = TestHelper()
        expected = []
        # add a few prefixes
        expected.append([th.add_prefix('10.0.0.0/16', 'reservation', 'test').prefix, 'reservation'])
        expected.append([th.add_prefix('10.0.0.0/24', 'assignment', 'test').prefix, 'assignment'])

        opts = {
            'prefix': '10.0.0.1/32',
            'description': 'host'
            }
        expected.append([opts['prefix'], 'host'])
        nipap_cli.add_prefix({}, opts, {})

        result = [[p.prefix, p.type] for p in Prefix.smart_search('')['result']]

        self.assertEqual(expected, result)


    def test_auto_type7(self):
        """ Test automatic prefix type guessing
        """
        from nipap_cli import nipap_cli
        from pynipap import NipapError
        nipap_cli.cfg = self.mock_cfg()

        th = TestHelper()
        expected = []
        # add a few prefixes
        expected.append([th.add_prefix('10.0.0.0/16', 'reservation', 'test').prefix, 'reservation'])
        expected.append([th.add_prefix('10.0.0.0/24', 'assignment', 'test').prefix, 'assignment'])

        opts = {
            'prefix': '10.0.0.1/25',
            'description': 'host'
            }

        with self.assertRaisesRegexp(SystemExit, "^1$"):
            nipap_cli.add_prefix({}, opts, {})


class TestNipapHelper(unittest.TestCase):
    """ Test the nipap helper app
    """
    def test_test1(self):
        from nipap_cli.command import Command, InvalidCommand
        from nipap_cli import nipap_cli
        from pynipap import NipapError

        cmd = Command(nipap_cli.cmds, ['pool', 'res'])
        self.assertEqual(['resize'], sorted(cmd.complete()))

        cmd = Command(nipap_cli.cmds, ['pool', 'resize'])
        self.assertEqual(['resize'], sorted(cmd.complete()))


class TestSmartParser(unittest.TestCase):
    """ Test the smart parsing functions
    """
    maxDiff = None

    def test_prefix1(self):
        cfg = NipapConfig('/etc/nipap/nipap.conf')
        n = Nipap()

        success, query = n._parse_prefix_query('foo')
        exp_query = {
                'interpretation': {
                    'attribute': 'description or comment or node or order_id or customer_id',
                    'interpretation': 'text',
                    'operator': 'regex',
                    'string': 'foo',
                    'error': False
                },
                'operator': 'or',
                'val1': {
                    'operator': 'or',
                    'val1': {
                        'operator': 'or',
                        'val1': {
                            'operator': 'or',
                            'val1': {
                                'operator': 'regex_match',
                                'val1': 'comment',
                                'val2': u'foo'
                                },
                            'val2': {
                                'operator': 'regex_match',
                                'val1': 'description',
                                'val2': u'foo'
                                }
                            },
                        'val2': {
                            'operator': 'regex_match',
                            'val1': 'node',
                            'val2': u'foo'
                            }
                        },
                    'val2': {
                        'operator': 'regex_match',
                        'val1': 'order_id',
                        'val2': u'foo'
                        }
                    },
                'val2': {
                    'operator': 'regex_match',
                    'val1': 'customer_id',
                    'val2': u'foo'
                    }
                }

        self.assertEqual(success, True)
        self.assertEqual(query, exp_query)



    def test_prefix2(self):
        cfg = NipapConfig('/etc/nipap/nipap.conf')
        n = Nipap()

        success, query = n._parse_prefix_query('1.3.3.0/24')
        exp_query = {
                'interpretation': {
                    'attribute': 'prefix',
                    'interpretation': 'IPv4 prefix',
                    'operator': 'contained_within_equals',
                    'string': '1.3.3.0/24',
                    'error': False
                },
                'operator': 'contained_within_equals',
                'val1': 'prefix',
                'val2': '1.3.3.0/24'
                }

        self.assertEqual(success, True)
        self.assertEqual(query, exp_query)



    def test_prefix3(self):
        cfg = NipapConfig('/etc/nipap/nipap.conf')
        n = Nipap()

        success, query = n._parse_prefix_query('1.3.3.0/24 foo')
        exp_query = {
                'interpretation': {
                    'interpretation': 'and',
                    'operator': 'and',
                    'error': False
                },
                'operator': 'and',
                'val1': {
                    'interpretation': {
                        'attribute': 'prefix',
                        'interpretation': 'IPv4 prefix',
                        'operator': 'contained_within_equals',
                        'string': u'1.3.3.0/24',
                        'error': False
                    },
                    'operator': 'contained_within_equals',
                    'val1': 'prefix',
                    'val2': '1.3.3.0/24'
                    },
                'val2': {
                    'interpretation': {
                        'attribute': 'description or comment or node or order_id or customer_id',
                        'interpretation': 'text',
                        'operator': 'regex',
                        'string': u'foo',
                        'error': False
                    },
                    'operator': 'or',
                    'val1': {
                        'operator': 'or',
                        'val1': {
                            'operator': 'or',
                            'val1': {
                                'operator': 'or',
                                'val1': {
                                    'operator': 'regex_match',
                                    'val1': 'comment',
                                    'val2': u'foo'
                                    },
                                'val2': {
                                    'operator': 'regex_match',
                                    'val1': 'description',
                                    'val2': u'foo'
                                    }
                                },
                            'val2': {
                                'operator': 'regex_match',
                                'val1': 'node',
                                'val2': u'foo'
                                }
                            },
                        'val2': {
                            'operator': 'regex_match',
                            'val1': 'order_id',
                            'val2': u'foo'
                            }
                        },
                    'val2': {
                        'operator': 'regex_match',
                        'val1': 'customer_id',
                        'val2': u'foo'
                        }
                    }
                }

        self.assertEqual(success, True)
        self.assertEqual(query, exp_query)



    def test_prefix4(self):
        """ Test unclosed quotes
        """
        cfg = NipapConfig('/etc/nipap/nipap.conf')
        n = Nipap()

        expected = {
            'operator': None,
            'val1': None,
            'val2': None,
            'interpretation': {
                'interpretation': None,
                'string': None,
                'attribute': 'text',
                'operator': None,
                'error': True,
                'error_message': 'unclosed quote'
            }
        }

        success, query = n._parse_vrf_query('"')
        expected['interpretation']['string'] = '"'
        self.assertEqual(success, False)
        self.assertEquals(query, expected)

        success, query = n._parse_prefix_query('\'')
        expected['interpretation']['string'] = '\''
        self.assertEqual(success, False)
        self.assertEquals(query, expected)



    def test_prefix5(self):
        """ Test unclosed parentheses
        """
        cfg = NipapConfig('/etc/nipap/nipap.conf')
        n = Nipap()

        expected = {
            'operator': None,
            'val1': None,
            'val2': None,
            'interpretation': {
                'interpretation': None,
                'string': None,
                'attribute': 'text',
                'operator': None,
                'error': True,
                'error_message': 'unclosed parentheses'
            }
        }

        success, query = n._parse_prefix_query('(')
        expected['interpretation']['string'] = '('
        self.assertEqual(success, False)
        self.assertEquals(query, expected)

        success, query = n._parse_prefix_query(')')
        expected['interpretation']['string'] = ')'
        self.assertEqual(success, False)
        self.assertEquals(query, expected)



    def test_prefix6(self):
        cfg = NipapConfig('/etc/nipap/nipap.conf')
        n = Nipap()

        success, query = n._parse_prefix_query('foo-agg-1 vlan>100 vlan< 200')
        exp_query = {
            'interpretation': {'interpretation': 'and', 'operator': 'and', 'error': False},
            'operator': 'and',
            'val1': {'interpretation': {'interpretation': 'and', 'operator': 'and', 'error': False},
                     'operator': 'and',
                     'val1': {'interpretation': {'attribute': 'description or comment or node or order_id or customer_id',
                                                 'interpretation': 'text',
                                                 'operator': 'regex',
                                                 'string': 'foo-agg-1',
                                                 'error': False},
                              'operator': 'or',
                              'val1': {'operator': 'or',
                                       'val1': {'operator': 'or',
                                                'val1': {'operator': 'or',
                                                         'val1': {'operator': 'regex_match',
                                                                  'val1': 'comment',
                                                                  'val2': 'foo-agg-1'},
                                                         'val2': {'operator': 'regex_match',
                                                                  'val1': 'description',
                                                                  'val2': 'foo-agg-1'}},
                                                'val2': {'operator': 'regex_match',
                                                         'val1': 'node',
                                                         'val2': 'foo-agg-1'}},
                                       'val2': {'operator': 'regex_match',
                                                'val1': 'order_id',
                                                'val2': 'foo-agg-1'}},
                              'val2': {'operator': 'regex_match',
                                       'val1': 'customer_id',
                                       'val2': 'foo-agg-1'}},
                     'val2': {
                         'interpretation': {
                             'interpretation': 'expression',
                             'attribute': 'vlan',
                             'operator': '>',
                             'string': 'vlan>100',
                             'error': False
                         },
                          'operator': '>',
                          'val1': 'vlan',
                          'val2': '100'
                    }
                    },
            'val2': {
                'interpretation': {
                     'interpretation': 'expression',
                     'attribute': 'vlan',
                     'operator': '<',
                     'string': 'vlan<200',
                     'error': False
                 },
                 'operator': '<',
                 'val1': 'vlan',
                 'val2': '200'
                }
        }


        self.assertEqual(success, True)
        self.assertEqual(query, exp_query)



    def test_prefix7(self):
        cfg = NipapConfig('/etc/nipap/nipap.conf')
        n = Nipap()

        success, query = n._parse_prefix_query('123:456')
        exp_query = {
                'interpretation': {
                    'attribute': 'VRF RT',
                    'string': '123:456',
                    'interpretation': 'vrf_rt',
                    'operator': 'equals',
                    'error': False
                },
                'operator': 'equals',
                'val1': 'vrf_rt',
                'val2': u'123:456'
                }

        self.assertEqual(success, True)
        self.assertEqual(query, exp_query)



    def test_prefix8(self):
        cfg = NipapConfig('/etc/nipap/nipap.conf')
        n = Nipap()

        success, query = n._parse_prefix_query('2001:1000::/32')
        exp_query = {
                'interpretation': {
                    'attribute': 'prefix',
                    'interpretation': 'IPv6 prefix',
                    'operator': 'contained_within_equals',
                    'string': '2001:1000::/32',
                    'error': False
                },
                'operator': 'contained_within_equals',
                'val1': 'prefix',
                'val2': '2001:1000::/32'
                }

        self.assertEqual(success, True)
        self.assertEqual(query, exp_query)



    def test_prefix9(self):
        cfg = NipapConfig('/etc/nipap/nipap.conf')
        n = Nipap()

        success, query = n._parse_prefix_query('2001:1000:1234::/32')
        exp_query = {
                'interpretation': {
                    'attribute': 'prefix',
                    'interpretation': 'IPv6 prefix',
                    'operator': 'contained_within_equals',
                    'string': '2001:1000:1234::/32',
                    'strict_prefix': '2001:1000::/32',
                    'error': False
                },
                'operator': 'contained_within_equals',
                'val1': 'prefix',
                'val2': '2001:1000::/32'
                }

        self.assertEqual(success, True)
        self.assertEqual(query, exp_query)



    def test_prefix10(self):
        cfg = NipapConfig('/etc/nipap/nipap.conf')
        n = Nipap()

        success, query = n._parse_prefix_query('2001:1000::')
        exp_query = {
                'interpretation': {
                    'attribute': 'prefix',
                    'interpretation': 'IPv6 address',
                    'operator': 'contains_equals',
                    'string': '2001:1000::',
                    'error': False
                },
                'operator': 'contains_equals',
                'val1': 'prefix',
                'val2': '2001:1000::'
                }

        self.assertEqual(success, True)
        self.assertEqual(query, exp_query)



    def test_prefix11(self):
        cfg = NipapConfig('/etc/nipap/nipap.conf')
        n = Nipap()

        success, query = n._parse_prefix_query('1.3.3.0')
        exp_query = {
                'interpretation': {
                    'attribute': 'prefix',
                    'interpretation': 'IPv4 address',
                    'operator': 'contains_equals',
                    'string': '1.3.3.0',
                    'error': False
                },
                'operator': 'contains_equals',
                'val1': 'prefix',
                'val2': '1.3.3.0'
                }

        self.assertEqual(success, True)
        self.assertEqual(query, exp_query)



    def test_prefix12(self):
        cfg = NipapConfig('/etc/nipap/nipap.conf')
        n = Nipap()

        success, query = n._parse_prefix_query('1.3.3.0/16')
        exp_query = {
                'interpretation': {
                    'attribute': 'prefix',
                    'interpretation': 'IPv4 prefix',
                    'operator': 'contained_within_equals',
                    'string': '1.3.3.0/16',
                    'strict_prefix': '1.3.0.0/16',
                    'error': False
                },
                'operator': 'contained_within_equals',
                'val1': 'prefix',
                'val2': '1.3.0.0/16'
                }

        self.assertEqual(success, True)
        self.assertEqual(query, exp_query)



    def test_prefix13(self):
        cfg = NipapConfig('/etc/nipap/nipap.conf')
        n = Nipap()

        success, query = n._parse_prefix_query('1.3.3/16')
        exp_query = {
                'interpretation': {
                    'attribute': 'prefix',
                    'interpretation': 'IPv4 prefix',
                    'operator': 'contained_within_equals',
                    'string': '1.3.3/16',
                    'strict_prefix': '1.3.0.0/16',
                    'expanded': '1.3.3.0/16',
                    'error': False
                },
                'operator': 'contained_within_equals',
                'val1': 'prefix',
                'val2': '1.3.0.0/16'
                }

        self.assertEqual(success, True)
        self.assertEqual(query, exp_query)



    def test_prefix14(self):
        """ Match against invalid attribute
        """
        cfg = NipapConfig('/etc/nipap/nipap.conf')
        n = Nipap()

        expected = {
            'operator': "=",
            'val1': "foo",
            'val2': "bar",
            'interpretation': {
                'interpretation': 'expression',
                'string': 'foo=bar',
                'attribute': 'foo',
                'operator': '=',
                'error': True,
                'error_message': 'unknown attribute'
            }
        }

        success, query = n._parse_vrf_query('foo=bar')

        self.assertEqual(success, False)
        self.assertEquals(expected, query)



    def test_prefix15(self):
        """ Match invalid prefix type
        """
        cfg = NipapConfig('/etc/nipap/nipap.conf')
        n = Nipap()

        expected = {
            'operator': "=",
            'val1': "type",
            'val2': "foo",
            'interpretation': {
                'interpretation': 'expression',
                'string': 'type=foo',
                'attribute': 'type',
                'operator': '=',
                'error': True,
                'error_message': 'invalid value'
            }
        }

        success, query = n._parse_prefix_query('type=foo')

        self.assertEqual(success, False)
        self.assertEquals(expected, query)



    def test_prefix16(self):
        """ Single quoted string, double quotes - "foo bar"
        """

        cfg = NipapConfig('/etc/nipap/nipap.conf')
        n = Nipap()

        success, query = n._parse_prefix_query('"foo bar"')
        expected = {
            'interpretation': {
                'string': 'foo bar',
                'interpretation': 'text',
                'operator': 'regex',
                'attribute': 'description or comment or node or order_id or customer_id',
                'error': False
            },
            'operator': 'or',
            'val1': {
                'operator': 'or',
                 'val1': {
                    'operator': 'or',
                    'val1': {
                        'operator': 'or',
                        'val1': {
                            'operator': 'regex_match',
                            'val1': 'comment',
                            'val2': 'foo bar',
                        },
                        'val2': {
                            'operator': 'regex_match',
                            'val1': 'description',
                            'val2': 'foo bar'
                        }
                    },
                    'val2': {
                        'operator': 'regex_match',
                        'val1': 'node',
                        'val2': 'foo bar'
                    }
                },
                'val2': {
                    'operator': 'regex_match',
                    'val1': 'order_id',
                    'val2': 'foo bar'
                 }
            },
            'val2': {
                'operator': 'regex_match',
                'val1': 'customer_id',
                'val2': 'foo bar'
            }
        }

        self.assertEqual(success, True)
        self.assertEqual(query, expected)



    def test_prefix17(self):
        """ Mixed quoted and un-quoted strings, single quotes - 'foo bar' baz
        """

        cfg = NipapConfig('/etc/nipap/nipap.conf')
        n = Nipap()

        success, query = n._parse_prefix_query('\'foo bar\' baz')
        expected = {
            'interpretation': {
                'interpretation': 'and',
                'operator': 'and',
                'error': False
            },
            'operator': 'and',
            'val1': {
                'interpretation': {
                    'string': 'foo bar',
                    'interpretation': 'text',
                    'operator': 'regex',
                    'attribute': 'description or comment or node or order_id or customer_id',
                    'error': False
                },
                'operator': 'or',
                'val1': {
                    'operator': 'or',
                    'val1': {
                        'operator': 'or',
                        'val1': {
                            'operator': 'or',
                            'val1': {
                                'operator': 'regex_match',
                                'val1': 'comment',
                                'val2': 'foo bar'
                            },
                            'val2': {
                                'operator': 'regex_match',
                                'val1': 'description',
                                'val2': 'foo bar'
                            }
                        },
                        'val2': {
                            'operator': 'regex_match',
                            'val1': 'node',
                            'val2': 'foo bar'
                        },
                    },
                    'val2': {
                        'operator': 'regex_match',
                        'val1': 'order_id',
                        'val2': 'foo bar'
                    },
                },
                'val2': {
                    'operator': 'regex_match',
                    'val1': 'customer_id',
                    'val2': 'foo bar'
                }
            },
            'val2': {
                'interpretation': {
                    'string': 'baz',
                    'interpretation': 'text',
                    'operator': 'regex',
                    'attribute': 'description or comment or node or order_id or customer_id',
                    'error': False
                },
                'operator': 'or',
                'val1': {
                    'operator': 'or',
                    'val1': {
                        'operator': 'or',
                        'val1': {
                            'operator': 'or',
                            'val1': {
                                'operator': 'regex_match',
                                'val1': 'comment',
                                'val2': 'baz'
                            },
                            'val2': {
                                'operator': 'regex_match',
                                'val1': 'description',
                                'val2': 'baz'
                            }
                        },
                        'val2': {
                            'operator': 'regex_match',
                            'val1': 'node',
                            'val2': 'baz'
                        }
                    },
                    'val2': {
                        'operator': 'regex_match',
                        'val1': 'order_id',
                        'val2': 'baz'
                    }
                },
                'val2': {
                    'val2': 'baz',
                    'val1': 'customer_id',
                    'operator': 'regex_match'
                }
            }
        }

        self.assertEqual(success, True)
        self.assertEqual(query, expected)



    def test_prefix18(self):
        cfg = NipapConfig('/etc/nipap/nipap.conf')
        n = Nipap()

        success, query = n._parse_prefix_query('#foo')

        expected = {
            'interpretation': {
                'attribute': 'tag',
                'error': False,
                'interpretation': 'tag',
                'operator': 'equals_any',
                'string': '#foo'
            },
            'operator': 'equals_any',
            'val1': 'tags',
            'val2': 'foo'
        }

        self.assertEqual(success, True)
        self.assertEqual(query, expected)


    def test_prefix19(self):
        """ Test smart parser using unicode characters
        """
        cfg = NipapConfig('/etc/nipap/nipap.conf')
        n = Nipap()

        success, query = n._parse_prefix_query(u'åäö')

        exp_query = {
                'interpretation': {
                    'attribute': 'description or comment or node or order_id or customer_id',
                    'interpretation': 'text',
                    'operator': 'regex',
                    'string': u'åäö',
                    'error': False
                },
                'operator': 'or',
                'val1': {
                    'operator': 'or',
                    'val1': {
                        'operator': 'or',
                        'val1': {
                            'operator': 'or',
                            'val1': {
                                'operator': 'regex_match',
                                'val1': 'comment',
                                'val2': u'åäö'
                                },
                            'val2': {
                                'operator': 'regex_match',
                                'val1': 'description',
                                'val2': u'åäö'
                                }
                            },
                        'val2': {
                            'operator': 'regex_match',
                            'val1': 'node',
                            'val2': u'åäö'
                            }
                        },
                    'val2': {
                        'operator': 'regex_match',
                        'val1': 'order_id',
                        'val2': u'åäö'
                        }
                    },
                'val2': {
                    'operator': 'regex_match',
                    'val1': 'customer_id',
                    'val2': u'åäö'
                }
            }

        self.assertEqual(success, True)
        self.assertEqual(query, exp_query)


    def test_prefix20(self):
        """ Test smart parsing with a "contained by" operator (<<=) on the
            prefix attribute
        """
        cfg = NipapConfig('/etc/nipap/nipap.conf')
        n = Nipap()

        success, query = n._parse_prefix_query('prefix<<=1.3.0.0/16')
        exp_query = {
                'interpretation': {
                    'attribute': 'prefix',
                    'interpretation': 'expression',
                    'operator': '<<=',
                    'string': 'prefix<<=1.3.0.0/16',
                    'error': False
                },
                'operator': '<<=',
                'val1': 'prefix',
                'val2': u'1.3.0.0/16'
            }

        self.assertEqual(success, True)
        self.assertEqual(query, exp_query)



    def test_vrf1(self):
        cfg = NipapConfig('/etc/nipap/nipap.conf')
        n = Nipap()

        success, query = n._parse_vrf_query('foo')
        exp_query = {
                'interpretation': {
                    'attribute': 'vrf or name or description',
                    'interpretation': 'text',
                    'operator': 'regex',
                    'string': u'foo',
                    'error': False
                },
                'operator': 'or',
                'val1': {
                    'operator': 'or',
                    'val1': {
                        'operator': 'regex_match',
                        'val1': 'name',
                        'val2': u'foo'
                        },
                    'val2': {
                        'operator': 'regex_match',
                        'val1': 'description',
                        'val2': u'foo'
                        }
                },
                'val2': {
                    'operator': 'regex_match',
                    'val1': 'rt',
                    'val2': u'foo'
                }
            }

        self.assertEqual(success, True)
        self.assertEqual(query, exp_query)



    def test_vrf2(self):
        cfg = NipapConfig('/etc/nipap/nipap.conf')
        n = Nipap()

        success, query = n._parse_vrf_query('123:456')
        exp_query = {
                'interpretation': {
                    'attribute': 'vrf or name or description',
                    'interpretation': 'text',
                    'operator': 'regex',
                    'string': u'123:456',
                    'error': False
                },
                'operator': 'or',
                'val1': {
                    'operator': 'or',
                    'val1': {
                        'operator': 'regex_match',
                        'val1': 'name',
                        'val2': u'123:456'
                        },
                    'val2': {
                        'operator': 'regex_match',
                        'val1': 'description',
                        'val2': u'123:456'
                        }
                },
                'val2': {
                    'operator': 'regex_match',
                    'val1': 'rt',
                    'val2': u'123:456'
                }
            }

        self.assertEqual(success, True)
        self.assertEqual(query, exp_query)



    def test_vrf3(self):
        cfg = NipapConfig('/etc/nipap/nipap.conf')
        n = Nipap()

        success, query = n._parse_vrf_query('#bar')
        exp_query = {
                'interpretation': {
                    'attribute': 'tag',
                    'interpretation': 'tag',
                    'operator': 'equals_any',
                    'string': u'#bar',
                    'error': False
                },
                'operator': 'equals_any',
                'val1': 'tags',
                'val2': u'bar'
            }

        self.assertEqual(success, True)
        self.assertEqual(query, exp_query)



    def test_vrf4(self):
        """ Unclosed quotes
        """
        cfg = NipapConfig('/etc/nipap/nipap.conf')
        n = Nipap()

        expected = {
            'operator': None,
            'val1': None,
            'val2': None,
            'interpretation': {
                'interpretation': None,
                'string': None,
                'attribute': 'text',
                'operator': None,
                'error': True,
                'error_message': 'unclosed quote'
            }
        }

        success, query = n._parse_vrf_query('"')
        expected['interpretation']['string'] = '"'
        self.assertEqual(success, False)
        self.assertEqual(query, expected)

        success, query = n._parse_vrf_query('\'')
        expected['interpretation']['string'] = '\''
        self.assertEqual(success, False)
        self.assertEqual(query, expected)



    def test_vrf5(self):
        """ Unclosed parentheses
        """
        cfg = NipapConfig('/etc/nipap/nipap.conf')
        n = Nipap()

        expected = {
            'operator': None,
            'val1': None,
            'val2': None,
            'interpretation': {
                'interpretation': None,
                'string': None,
                'attribute': 'text',
                'operator': None,
                'error': True,
                'error_message': 'unclosed parentheses'
            }
        }

        success, query = n._parse_vrf_query('(')
        expected['interpretation']['string'] = '('
        self.assertEqual(success, False)
        self.assertEqual(query, expected)

        success, query = n._parse_vrf_query(')')
        expected['interpretation']['string'] = ')'
        self.assertEqual(success, False)
        self.assertEqual(query, expected)



    def test_vrf6(self):
        cfg = NipapConfig('/etc/nipap/nipap.conf')
        n = Nipap()

        success, query = n._parse_vrf_query('foo bar')
        exp_query = {
                'interpretation': {
                    'interpretation': 'and',
                    'operator': 'and',
                    'error': False
                },
                'operator': 'and',
                'val1': {
                    'interpretation': {
                        'attribute': 'vrf or name or description',
                        'interpretation': 'text',
                        'operator': 'regex',
                        'string': u'foo',
                        'error': False
                    },
                    'operator': 'or',
                    'val1': {
                        'operator': 'or',
                        'val1': {
                            'operator': 'regex_match',
                            'val1': 'name',
                            'val2': u'foo'
                            },
                        'val2': {
                            'operator': 'regex_match',
                            'val1': 'description',
                            'val2': u'foo'
                            }
                    },
                    'val2': {
                        'operator': 'regex_match',
                        'val1': 'rt',
                        'val2': u'foo'
                    }
                },
                'val2': {
                    'interpretation': {
                        'attribute': 'vrf or name or description',
                        'interpretation': 'text',
                        'operator': 'regex',
                        'string': u'bar',
                        'error': False
                    },
                    'operator': 'or',
                    'val1': {
                        'operator': 'or',
                        'val1': {
                            'operator': 'regex_match',
                            'val1': 'name',
                            'val2': u'bar'
                            },
                        'val2': {
                            'operator': 'regex_match',
                            'val1': 'description',
                            'val2': u'bar'
                            }
                    },
                    'val2': {
                        'operator': 'regex_match',
                        'val1': 'rt',
                        'val2': u'bar'
                    }
                }
            }

        self.assertEqual(success, True)
        self.assertEqual(query, exp_query)



    def test_vrf7(self):
        cfg = NipapConfig('/etc/nipap/nipap.conf')
        n = Nipap()

        success, query = n._parse_vrf_query('#foo')

        expected = {
            'interpretation': {
                'attribute': 'tag',
                'error': False,
                'interpretation': 'tag',
                'operator': 'equals_any',
                'string': '#foo'
            },
            'operator': 'equals_any',
            'val1': 'tags',
            'val2': 'foo'
        }

        self.assertEqual(success, True)
        self.assertEqual(query, expected)



    def test_pool1(self):
        cfg = NipapConfig('/etc/nipap/nipap.conf')
        n = Nipap()

        success, query = n._parse_pool_query('foo')
        exp_query = {
                'interpretation': {
                    'attribute': 'name or description',
                    'interpretation': 'text',
                    'operator': 'regex',
                    'string': u'foo',
                    'error': False
                },
                'operator': 'or',
                'val1': {
                    'operator': 'regex_match',
                    'val1': 'name',
                    'val2': u'foo'
                },
                'val2': {
                    'operator': 'regex_match',
                    'val1': 'description',
                    'val2': u'foo'
                }
            }

        self.assertEqual(success, True)
        self.assertEqual(query, exp_query)



    def test_pool2(self):
        cfg = NipapConfig('/etc/nipap/nipap.conf')
        n = Nipap()

        success, query = n._parse_pool_query('123:456')
        exp_query = {
                'interpretation': {
                    'attribute': 'name or description',
                    'interpretation': 'text',
                    'operator': 'regex',
                    'string': u'123:456',
                    'error': False
                },
                'operator': 'or',
                'val1': {
                    'operator': 'regex_match',
                    'val1': 'name',
                    'val2': u'123:456'
                },
                'val2': {
                    'operator': 'regex_match',
                    'val1': 'description',
                    'val2': u'123:456'
                }
            }

        self.assertEqual(success, True)
        self.assertEqual(exp_query, query)



    def test_pool3(self):
        cfg = NipapConfig('/etc/nipap/nipap.conf')
        n = Nipap()

        success, query = n._parse_pool_query('#bar')
        exp_query = {
                'interpretation': {
                    'attribute': 'tag',
                    'interpretation': 'tag',
                    'operator': 'equals_any',
                    'string': '#bar',
                    'error': False
                },
                'operator': 'equals_any',
                'val1': 'tags',
                'val2': 'bar'
            }

        self.assertEqual(success, True)
        self.assertEqual(exp_query, query)



    def test_pool4(self):
        """ Unclosed quote
        """
        cfg = NipapConfig('/etc/nipap/nipap.conf')
        n = Nipap()

        expected = {
            'operator': None,
            'val1': None,
            'val2': None,
            'interpretation': {
                'interpretation': None,
                'string': None,
                'attribute': 'text',
                'operator': None,
                'error': True,
                'error_message': 'unclosed quote'
            }
        }

        success, query = n._parse_pool_query('"')
        expected['interpretation']['string'] = '"'
        self.assertEqual(success, False)
        self.assertEqual(query, expected)

        success, query = n._parse_pool_query('\'')
        expected['interpretation']['string'] = '\''
        self.assertEqual(success, False)
        self.assertEqual(query, expected)



    def test_pool5(self):
        """ Unclosed parentheses
        """
        cfg = NipapConfig('/etc/nipap/nipap.conf')
        n = Nipap()

        expected = {
            'operator': None,
            'val1': None,
            'val2': None,
            'interpretation': {
                'interpretation': None,
                'string': None,
                'attribute': 'text',
                'operator': None,
                'error': True,
                'error_message': 'unclosed parentheses'
            }
        }

        success, query = n._parse_pool_query('(')
        expected['interpretation']['string'] = '('
        self.assertEqual(success, False)
        self.assertEqual(query, expected)

        success, query = n._parse_pool_query(')')
        expected['interpretation']['string'] = ')'
        self.assertEqual(success, False)
        self.assertEqual(query, expected)



    def test_pool6(self):
        cfg = NipapConfig('/etc/nipap/nipap.conf')
        n = Nipap()

        success, query = n._parse_pool_query('#foo and bar')
        exp_query = {
                'interpretation': {
                    'interpretation': 'and',
                    'operator': 'and',
                    'error': False
                },
                'operator': 'and',
                'val1': {
                    'interpretation': {
                        'attribute': 'tag',
                        'interpretation': 'tag',
                        'operator': 'equals_any',
                        'string': '#foo',
                        'error': False
                    },
                    'operator': 'equals_any',
                    'val1': 'tags',
                    'val2': 'foo'
                },
                'val2': {
                    'interpretation': {
                        'attribute': 'name or description',
                        'interpretation': 'text',
                        'operator': 'regex',
                        'string': u'bar',
                        'error': False
                    },
                    'operator': 'or',
                    'val1': {
                        'operator': 'regex_match',
                        'val1': 'name',
                        'val2': u'bar'
                    },
                    'val2': {
                        'operator': 'regex_match',
                        'val1': 'description',
                        'val2': u'bar'
                    }
                }
            }

        self.assertEqual(success, True)
        self.assertEqual(query, exp_query)



    def test_pool7(self):
        cfg = NipapConfig('/etc/nipap/nipap.conf')
        n = Nipap()

        success, query = n._parse_pool_query('#foo')

        expected = {
            'interpretation': {
                'attribute': 'tag',
                'error': False,
                'interpretation': 'tag',
                'operator': 'equals_any',
                'string': '#foo'
            },
            'operator': 'equals_any',
            'val1': 'tags',
            'val2': 'foo'
        }

        self.assertEqual(success, True)
        self.assertEqual(query, expected)



class TestAvpEmptyName(unittest.TestCase):
    """ Test AVP with empty name
    """

    def setUp(self):
        """ Test setup, which essentially means to empty the database
        """
        TestHelper.clear_database()


    def test_pool_add_avp(self):
        p = Pool()
        p.name = 'test AVP with empty name'
        p.avps = { '': '1337' }
        with self.assertRaisesRegexp(NipapValueError, "AVP with empty name is not allowed"):
            p.save()


    def test_pool_edit_avp(self):
        th = TestHelper()

        # add a pool
        p = th.add_pool('test', 'assignment', 31, 112)

        p.avps = { '': '1337' }
        with self.assertRaisesRegexp(NipapValueError, "AVP with empty name is not allowed"):
            p.save()


    def test_prefix_add_avp(self):
        p = Prefix()
        p.prefix = '1.2.3.0/24'
        p.type = 'assignment'
        p.status = 'assigned'
        p.description = 'test AVP with empty name'
        p.avps = { '': '1337' }
        with self.assertRaisesRegexp(NipapValueError, "AVP with empty name is not allowed"):
            p.save()


    def test_prefix_edit_avp(self):
        th = TestHelper()
        p = th.add_prefix('192.0.2.0/24', 'assignment', 'test AVP with empty name')

        p.avps = { '': '1337' }
        with self.assertRaisesRegexp(NipapValueError, "AVP with empty name is not allowed"):
            p.save()


    def test_vrf_add_avp(self):
        v = VRF()
        v.rt = '123:456'
        v.name = 'test AVP with empty name'
        v.avps = { '': '1337' }
        with self.assertRaisesRegexp(NipapValueError, "AVP with empty name is not allowed"):
            v.save()


    def test_vrf_edit_avp(self):
        v = VRF()
        v.rt = '123:456'
        v.name = 'test AVP with empty name'
        v.save()

        v.avps = { '': '1337' }
        with self.assertRaisesRegexp(NipapValueError, "AVP with empty name is not allowed"):
            v.save()


class TestDatabaseConstraints(unittest.TestCase):
    """ Test if the database constraints are correctly implemented
    """

    def setUp(self):
        """ Test setup, which essentially means to empty the database
        """
        TestHelper.clear_database()


    def test_constraints(self):
        """Testing of database constraints
        """

        th = TestHelper()
        d = "test description"
        th.add_prefix('1.3.0.0/16', 'reservation', d)
        with self.assertRaisesRegexp(NipapDuplicateError, "Duplicate"):
            # exact duplicate
            th.add_prefix('1.3.0.0/16', 'reservation', d)
        p2 = th.add_prefix('1.3.3.0/24', 'reservation', d)
        p3 = th.add_prefix('1.3.3.0/27', 'assignment', d)
        th.add_prefix('1.3.3.0/32', 'host', d)
        th.add_prefix('1.3.3.1/32', 'host', d)
        with self.assertRaisesRegexp(NipapValueError, "Prefix of type host must have all bits set in netmask"):
             # do not allow /31 as type 'host'
             th.add_prefix('1.3.3.2/31', 'host', d)
        with self.assertRaisesRegexp(NipapValueError, "Parent prefix .* is of type assignment"):
             # unable to create assignment within assignment
             th.add_prefix('1.3.3.3/32', 'assignment', d)
        with self.assertRaisesRegexp(NipapValueError, "contains hosts"):
             # unable to remove assignment containing hosts
             p3.remove()
        with self.assertRaisesRegexp(NipapValueError, "'assignment' must not have any subnets other than of type 'host'"):
             p2.type = 'assignment'
             p2.save()


if __name__ == '__main__':

    # set up logging
    log = logging.getLogger()
    logging.basicConfig()
    log.setLevel(logging.INFO)

    if sys.version_info >= (2,7):
        unittest.main(verbosity=2)
    else:
        unittest.main()


