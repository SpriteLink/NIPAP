#!/usr/bin/env python
# vim: et :

#
# All of the tests in this test suite runs directly against the XML-RPC
# interfaces of NIPAP to check return data and so forth. As it can be rather
# time-consuming to test everything on a XML-RPC level (everything is received
# as basic Python data structures) it is often better to put the test in
# nipaptest.py and use Pynipap to run more of an "end-to-end" test.
#

import logging
import unittest
import sys
sys.path.append('../nipap/')

from nipap.backend import Nipap
from nipap.authlib import SqliteAuth
from nipap.nipapconfig import NipapConfig

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
log_format = "%(levelname)-8s %(message)s"

import xmlrpclib

server_url = "http://unittest:gottatest@127.0.0.1:1337/XMLRPC"
s = xmlrpclib.Server(server_url, allow_none=1);

ad = { 'authoritative_source': 'nipap' }

class NipapXmlTest(unittest.TestCase):
    """ Tests the NIPAP XML-RPC daemon

        We presume the database is empty
    """
    maxDiff = None

    logger = None
    cfg = None
    nipap = None

    def setUp(self):

        # logging
        self.logger = logging.getLogger(self.__class__.__name__)

        # NIPAP
        self.cfg = NipapConfig('/etc/nipap/nipap.conf')
        self.nipap = Nipap()

        # create dummy auth object
        # As the authentication is performed before the query hits the Nipap
        # class, it does not matter what user we use here
        self.auth = SqliteAuth('local', 'unittest', 'unittest', 'unittest')
        self.auth.authenticated_as = 'unittest'
        self.auth.full_name = 'Unit test'

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


    def _mangle_pool_result(self, res):
        """ Mangle pool result for easier testing

            We can never predict the values of things like the ID (okay, that
            one is actually kind of doable) or the added and last_modified
            timestamp. This function will make sure the values are present but
            then strip them to make it easier to test against an expected
            result.

            All testing of statistics is done in nipaptest.py so we strip that
            from the result here to make things simple.
        """

        if isinstance(res, list):
            # res from list_pool
            for p in res:
                self.assertIn('total_addresses_v4', p)
                self.assertIn('total_addresses_v6', p)
                self.assertIn('used_addresses_v4', p)
                self.assertIn('used_addresses_v6', p)
                self.assertIn('free_addresses_v4', p)
                self.assertIn('free_addresses_v6', p)
                self.assertIn('member_prefixes_v4', p)
                self.assertIn('member_prefixes_v6', p)
                self.assertIn('used_prefixes_v4', p)
                self.assertIn('used_prefixes_v6', p)
                self.assertIn('free_prefixes_v4', p)
                self.assertIn('free_prefixes_v6', p)
                self.assertIn('total_prefixes_v4', p)
                self.assertIn('total_prefixes_v6', p)
                del(p['total_addresses_v4'])
                del(p['total_addresses_v6'])
                del(p['used_addresses_v4'])
                del(p['used_addresses_v6'])
                del(p['free_addresses_v4'])
                del(p['free_addresses_v6'])
                del(p['member_prefixes_v4'])
                del(p['member_prefixes_v6'])
                del(p['used_prefixes_v4'])
                del(p['used_prefixes_v6'])
                del(p['free_prefixes_v4'])
                del(p['free_prefixes_v6'])
                del(p['total_prefixes_v4'])
                del(p['total_prefixes_v6'])

        elif isinstance(res, dict) and 'result' in res:
            # res from smart search
            for p in res['result']:
                self.assertIn('total_addresses_v4', p)
                self.assertIn('total_addresses_v6', p)
                self.assertIn('used_addresses_v4', p)
                self.assertIn('used_addresses_v6', p)
                self.assertIn('free_addresses_v4', p)
                self.assertIn('free_addresses_v6', p)
                self.assertIn('member_prefixes_v4', p)
                self.assertIn('member_prefixes_v6', p)
                self.assertIn('used_prefixes_v4', p)
                self.assertIn('used_prefixes_v6', p)
                self.assertIn('free_prefixes_v4', p)
                self.assertIn('free_prefixes_v6', p)
                self.assertIn('total_prefixes_v4', p)
                self.assertIn('total_prefixes_v6', p)
                del(p['total_addresses_v4'])
                del(p['total_addresses_v6'])
                del(p['used_addresses_v4'])
                del(p['used_addresses_v6'])
                del(p['free_addresses_v4'])
                del(p['free_addresses_v6'])
                del(p['member_prefixes_v4'])
                del(p['member_prefixes_v6'])
                del(p['used_prefixes_v4'])
                del(p['used_prefixes_v6'])
                del(p['free_prefixes_v4'])
                del(p['free_prefixes_v6'])
                del(p['total_prefixes_v4'])
                del(p['total_prefixes_v6'])

        elif isinstance(res, dict):
            # just one single pool
            self.assertIn('total_addresses_v4', res)
            self.assertIn('total_addresses_v6', res)
            self.assertIn('used_addresses_v4', res)
            self.assertIn('used_addresses_v6', res)
            self.assertIn('free_addresses_v4', res)
            self.assertIn('free_addresses_v6', res)
            self.assertIn('member_prefixes_v4', res)
            self.assertIn('member_prefixes_v6', res)
            self.assertIn('used_prefixes_v4', res)
            self.assertIn('used_prefixes_v6', res)
            self.assertIn('free_prefixes_v4', res)
            self.assertIn('free_prefixes_v6', res)
            self.assertIn('total_prefixes_v4', res)
            self.assertIn('total_prefixes_v6', res)
            del(res['total_addresses_v4'])
            del(res['total_addresses_v6'])
            del(res['used_addresses_v4'])
            del(res['used_addresses_v6'])
            del(res['free_addresses_v4'])
            del(res['free_addresses_v6'])
            del(res['member_prefixes_v4'])
            del(res['member_prefixes_v6'])
            del(res['used_prefixes_v4'])
            del(res['used_prefixes_v6'])
            del(res['free_prefixes_v4'])
            del(res['free_prefixes_v6'])
            del(res['total_prefixes_v4'])
            del(res['total_prefixes_v6'])

        return res


    def _mangle_prefix_result(self, res):
        """ Mangle prefix result for easier testing

            We can never predict the values of things like the ID (okay, that
            one is actually kind of doable) or the added and last_modified
            timestamp. This function will make sure the values are present but
            then strip them to make it easier to test against an expected
            result.

            All testing of statistics is done in nipaptest.py so we strip that
            from the result here to make things simple.
        """

        if isinstance(res, list):
            # res from list_prefix
            for p in res:
                self.assertIn('added', p)
                self.assertIn('last_modified', p)
                self.assertIn('total_addresses', p)
                self.assertIn('used_addresses', p)
                self.assertIn('free_addresses', p)
                del(p['added'])
                del(p['last_modified'])
                del(p['total_addresses'])
                del(p['used_addresses'])
                del(p['free_addresses'])

        elif isinstance(res, dict) and 'result' in res:
            # res from smart search
            for p in res['result']:
                self.assertIn('added', p)
                self.assertIn('last_modified', p)
                self.assertIn('total_addresses', p)
                self.assertIn('used_addresses', p)
                self.assertIn('free_addresses', p)
                del(p['added'])
                del(p['last_modified'])
                del(p['total_addresses'])
                del(p['used_addresses'])
                del(p['free_addresses'])

        elif isinstance(res, dict):
            # just one single prefix
            self.assertIn('added', res)
            self.assertIn('last_modified', res)
            self.assertIn('total_addresses', res)
            self.assertIn('used_addresses', res)
            self.assertIn('free_addresses', res)
            del(res['added'])
            del(res['last_modified'])
            del(res['total_addresses'])
            del(res['used_addresses'])
            del(res['free_addresses'])

        return res



    def _mangle_vrf_result(self, res):
        """ Mangle vrf result for easier testing

            We can never predict the values of things like the ID (okay, that
            one is actually kind of doable) or the added and last_modified
            timestamp. This function will make sure the values are present but
            then strip them to make it easier to test against an expected
            result.

            All testing of statistics is done in nipaptest.py so we strip that
            from the result here to make things simple.
        """

        if isinstance(res, list):
            # res from list_vrf
            for p in res:
                #self.assertIn('added', p)
                #self.assertIn('last_modified', p)
                self.assertIn('total_addresses_v4', p)
                self.assertIn('total_addresses_v6', p)
                self.assertIn('used_addresses_v4', p)
                self.assertIn('used_addresses_v6', p)
                self.assertIn('free_addresses_v4', p)
                self.assertIn('free_addresses_v6', p)
                self.assertIn('num_prefixes_v4', p)
                self.assertIn('num_prefixes_v6', p)
                #del(p['added'])
                #del(p['last_modified'])
                del(p['total_addresses_v4'])
                del(p['total_addresses_v6'])
                del(p['used_addresses_v4'])
                del(p['used_addresses_v6'])
                del(p['free_addresses_v4'])
                del(p['free_addresses_v6'])
                del(p['num_prefixes_v4'])
                del(p['num_prefixes_v6'])

        elif isinstance(res, dict) and 'result' in res:
            # res from smart search
            for p in res['result']:
                #self.assertIn('added', p)
                #self.assertIn('last_modified', p)
                self.assertIn('total_addresses_v4', p)
                self.assertIn('total_addresses_v6', p)
                self.assertIn('used_addresses_v4', p)
                self.assertIn('used_addresses_v6', p)
                self.assertIn('free_addresses_v4', p)
                self.assertIn('free_addresses_v6', p)
                self.assertIn('num_prefixes_v4', p)
                self.assertIn('num_prefixes_v6', p)
                #del(p['added'])
                #del(p['last_modified'])
                del(p['total_addresses_v4'])
                del(p['total_addresses_v6'])
                del(p['used_addresses_v4'])
                del(p['used_addresses_v6'])
                del(p['free_addresses_v4'])
                del(p['free_addresses_v6'])
                del(p['num_prefixes_v4'])
                del(p['num_prefixes_v6'])

        elif isinstance(res, dict):
            # just one single vrf
            #self.assertIn('added', res)
            #self.assertIn('last_modified', res)
            self.assertIn('total_addresses_v4', res)
            self.assertIn('total_addresses_v6', res)
            self.assertIn('used_addresses_v4', res)
            self.assertIn('used_addresses_v6', res)
            self.assertIn('free_addresses_v4', res)
            self.assertIn('free_addresses_v6', res)
            self.assertIn('num_prefixes_v4', res)
            self.assertIn('num_prefixes_v6', res)
            #del(res['added'])
            #del(res['last_modified'])
            del(res['total_addresses_v4'])
            del(res['total_addresses_v6'])
            del(res['used_addresses_v4'])
            del(res['used_addresses_v6'])
            del(res['free_addresses_v4'])
            del(res['free_addresses_v6'])
            del(res['num_prefixes_v4'])
            del(res['num_prefixes_v6'])

        return res




    def test_vrf_add_list(self):
        """ Add a VRF and verify result in database
        """
        attr = {}
        with self.assertRaisesRegexp(xmlrpclib.Fault, 'missing attribute rt'):
            s.add_vrf({ 'auth': ad, 'attr': attr })

        attr['rt'] = '123:456'
        with self.assertRaisesRegexp(xmlrpclib.Fault, 'missing attribute name'):
            s.add_vrf({ 'auth': ad, 'attr': attr })
        attr['name'] = 'test'
        attr['tags'] = []

        attr['description'] = 'my test vrf'
        attr['avps'] = {'foo': 'bar'}
        vrf = s.add_vrf({ 'auth': ad, 'attr': attr })

        self.assertGreater(vrf['id'], 0)

        ref = attr.copy()
        ref['id'] = vrf['id']
        self.assertEqual(self._mangle_vrf_result(vrf), ref)
        self.assertEqual(self._mangle_vrf_result(s.list_vrf({ 'auth': ad, 'vrf': { 'id': vrf['id'] } })), [ ref, ])

        attr['rt'] = '123:abc'
        with self.assertRaisesRegexp(xmlrpclib.Fault, '.'): # TODO: specify exception string
            s.add_vrf({ 'auth': ad, 'attr': attr })



    def test_vrf_edit_default(self):
        """ Edit the default VRF and verify the change
        """
        # try to set an RT, which should fail on the default VRF
        with self.assertRaisesRegexp(xmlrpclib.Fault, 'Invalid input for column rt, must be NULL for VRF id 0'):
            s.edit_vrf({ 'auth': ad, 'vrf': { 'id': 0 }, 'attr': { 'rt': '123:456a' }})

        res_edit = s.edit_vrf({ 'auth': ad, 'vrf': { 'id': 0 }, 'attr': {
            'name': 'FOO', 'description': 'BAR', 'tags': [] }})
        res_list = s.list_vrf({ 'auth': ad, 'vrf': { } })[0]
        del(res_list['id'])
        self.assertEqual(self._mangle_vrf_result(res_list), { 'rt': None,
            'name': 'FOO', 'description': 'BAR', 'tags': [], 'avps': {} }, 'VRF change incorrect')



    def test_vrf_edit(self):
        """ Edit VRF and verify the change
        """
        attr = {
            'rt': '65000:123',
            'name': '65k:123',
            'description': 'VRF 65000:123',
            'tags': [],
            'avps': {}
        }
        spec = { 'rt': '65000:123' }
        vrf = s.add_vrf({ 'auth': ad, 'attr': attr })

        # omitting VRF spec
        with self.assertRaisesRegexp(xmlrpclib.Fault, 'vrf specification must be a dict'):
            s.edit_vrf({ 'auth': ad, 'attr': { 'name': 'test_vrf_edit' } })

        # omitting VRF attributes
        with self.assertRaisesRegexp(xmlrpclib.Fault, 'invalid input type, must be dict'):
            s.edit_vrf({ 'auth': ad, 'vrf': spec })

        # specifying too many attributes in spec
        with self.assertRaisesRegexp(xmlrpclib.Fault, 'specification contains too many keys'):
            s.edit_vrf({ 'auth': ad, 'vrf': { 'rt': '65000:123', 'name': '65k:123' }, 'attr': {} })

        # test changing ID
        with self.assertRaisesRegexp(xmlrpclib.Fault, 'extraneous attribute'):
            s.edit_vrf({ 'auth': ad, 'vrf': spec, 'attr': { 'id': 1337 } })

        # empty attribute list
        with self.assertRaisesRegexp(xmlrpclib.Fault, "'attr' must not be empty."):
            s.edit_vrf({ 'auth': ad, 'vrf': spec, 'attr': {} })
        res = s.list_vrf({ 'auth': ad, 'vrf': spec })
        self.assertEquals(len(res), 1, 'wrong number of VRFs returned')
        res = res[0]
        del(res['id'])
        self.assertEqual(self._mangle_vrf_result(res), attr)

        # valid change
        attr['rt'] = '65000:1234'
        attr['name'] = '65k:1234'
        attr['description'] = 'VRF 65000:1234'
        attr['tags'] = []
        s.edit_vrf({ 'auth': ad, 'vrf': spec, 'attr': attr })

        # verify result of valid change
        res = s.list_vrf({ 'auth': ad, 'vrf': { 'rt': attr['rt'] } })
        self.assertEquals(len(res), 1, 'wrong number of VRFs returned')
        res = res[0]
        # ignore the ID
        del(res['id'])
        self.assertEqual(self._mangle_vrf_result(res), attr, 'VRF change incorrect')



    def test_vrf_add_search(self):
        """ Add VRF and search for it
        """

        # add VRF
        attr = {
            'rt': '65000:1235',
            'name': '65k:1235',
            'description': 'Virtual Routing and Forwarding instance 65000:123',
            'tags': [],
            'avps': {}
        }
        vrf = s.add_vrf({ 'auth': ad, 'attr': attr })
        attr['id'] = vrf['id']

        # equal match
        q = {
            'operator': 'equals',
            'val1': 'rt',
            'val2': attr['rt']
        }
        res = self._mangle_vrf_result(s.search_vrf({ 'auth': ad, 'query': q }))
        self.assertEquals(res['result'], [ attr, ], 'Search result from equal match did not match')

        # regex match
        q = {
            'operator': 'regex_match',
            'val1': 'description',
            'val2': 'instance 65000'
        }
        res = self._mangle_vrf_result(s.search_vrf({ 'auth': ad, 'query': q }))
        self.assertEquals(res['result'], [ attr, ], 'Search result from regex match did not match')

        # smart search
        res = self._mangle_vrf_result(s.smart_search_vrf({ 'auth': ad, 'query_string': 'forwarding instance' }))
        self.assertEquals(res['result'], [ attr, ], 'Smart search result did not match')



    def test_prefix_add(self):
        """ Add a prefix and list
        """
        # check that some error / sanity checking is there
        attr = {}
        with self.assertRaisesRegexp(xmlrpclib.Fault, "specify 'prefix' or 'from-prefix' or 'from-pool'"):
            s.add_prefix({ 'auth': ad, 'attr': attr })

        attr['prefix'] = '1.3.3.0/24'
        with self.assertRaisesRegexp(xmlrpclib.Fault, "Either description or node must be specified."):
            s.add_prefix({ 'auth': ad, 'attr': attr })

        attr['description'] = 'test prefix'
        with self.assertRaisesRegexp(xmlrpclib.Fault, "Unknown prefix type"):
            s.add_prefix({ 'auth': ad, 'attr': attr })

        attr['type'] = 'assignment'

        # add 1.3.3.0/24
        prefix = s.add_prefix({ 'auth': ad, 'attr': attr })
        attr['id'] = prefix['id']
        self.assertGreater(attr['id'], 0)

        # what we expect the above prefix to look like
        expected = {
                'alarm_priority': None,
                'authoritative_source': 'nipap',
                'avps': {},
                'comment': None,
                'country': None,
                'description': 'test prefix',
                'display_prefix': '1.3.3.0/24',
                'expires': None,
                'external_key': None,
                'family': 4,
                'id': 131,
                'indent': 0,
                'inherited_tags': [],
                'monitor': None,
                'node': None,
                'order_id': None,
                'customer_id': None,
                'pool_name': None,
                'pool_id': None,
                'tags': [],
                'status': 'assigned',
                'vrf_rt': None,
                'vrf_id': 0,
                'vrf_name': 'default',
                'vlan': None
            }
        expected.update(attr)
        self.assertEqual(
                self._mangle_prefix_result(s.list_prefix({ 'auth': ad })),
                [expected])

        attr = {
                'description': 'test for from-prefix 1.3.3.0/24',
                'type': 'host'
            }
        args = { 'from-prefix': ['1.3.3.0/24'], 'prefix_length': 32 }
        # add a host in 1.3.3.0/24
        res = s.add_prefix({ 'auth': ad, 'attr': attr, 'args': args })

        # copy expected from 1.3.3.0/24 since we expect most things to look the
        # same for the new prefix (1.3.3.1/32) from 1.3.3.0/24
        expected_host = expected.copy()
        expected_host.update(attr)
        expected_host['id'] = res['id']
        expected_host['prefix'] = '1.3.3.1/32'
        expected_host['display_prefix'] = '1.3.3.1/24'
        expected_host['indent'] = 1

        # build list of expected
        expected_list = []
        expected_list.append(expected)
        expected_list.append(expected_host)

        # add another prefix, try with vrf_id = None
        attr['vrf_id'] = None
        res = s.add_prefix({ 'auth': ad, 'attr': attr, 'args': args })
        # update expected list
        expected_host2 = expected_host.copy()
        expected_host2['id'] = res['id']
        expected_host2['prefix'] = '1.3.3.2/32'
        expected_host2['display_prefix'] = '1.3.3.2/24'
        expected_list.append(expected_host2)

        # add another prefix, this time completely without VRF info
        del(attr['vrf_id'])
        res = s.add_prefix({ 'auth': ad, 'attr': attr, 'args': args })
        # update expected list
        expected_host3 = expected_host.copy()
        expected_host3['id'] = res['id']
        expected_host3['prefix'] = '1.3.3.3/32'
        expected_host3['display_prefix'] = '1.3.3.3/24'
        expected_list.append(expected_host3)

        # add another prefix, based on VRF name
        attr['vrf_name'] = 'default'
        res = s.add_prefix({ 'auth': ad, 'attr': attr, 'args': args })
        # update expected list
        expected_host4 = expected_host.copy()
        expected_host4['id'] = res['id']
        expected_host4['prefix'] = '1.3.3.4/32'
        expected_host4['display_prefix'] = '1.3.3.4/24'
        expected_list.append(expected_host4)

        # make sure the result looks like we expect it too! :D
        self.assertEqual(
                self._mangle_prefix_result(s.list_prefix({ 'auth': ad })),
                expected_list)



    def test_prefix_add_vrf(self):
        """ Test adding prefixes to VRF
        """

        args = { 'from-prefix': ['1.3.3.0/24'], 'prefix_length': 32 }
        expected = {
                'alarm_priority': None,
                'authoritative_source': 'nipap',
                'avps': {},
                'comment': None,
                'country': None,
                'description': 'test prefix',
                'display_prefix': '1.3.3.0/24',
                'expires': None,
                'external_key': None,
                'family': 4,
                'id': 131,
                'indent': 0,
                'monitor': None,
                'node': None,
                'order_id': None,
                'customer_id': None,
                'pool_id': None,
                'pool_name': None,
                'vrf_id': 0,
                'vrf_rt': None,
                'vrf_name': None,
                'vlan': None,
                'inherited_tags': [],
                'tags': [],
                'status': 'assigned'
            }

        # add VRF
        vrf_attr = {
            'rt': '123:4567',
            'name': 'test_prefix_add_vrf1',
        }
        vrf = s.add_vrf({ 'auth': ad, 'attr': vrf_attr })
        vrf_attr['id'] = vrf['id']

        # add prefix to VRF by specifying ID
        vrf_pref_attr = {
            'prefix': '1.3.3.0/24',
            'vrf_id': vrf['id'],
            'type': 'assignment',
            'description': 'Test prefix 1.3.3.0/24 in vrf 123:4567'
        }
        prefix = s.add_prefix({ 'auth': ad, 'attr': vrf_pref_attr })
        expected['id'] = prefix['id']
        expected['vrf_rt'] = vrf_attr['rt']
        expected['vrf_name'] = vrf_attr['name']
        expected['display_prefix'] = '1.3.3.0/24'
        expected['indent'] = 0
        expected.update(vrf_pref_attr)

        vrf_pref = s.list_prefix({ 'auth': ad, 'prefix': { 'id': expected['id'] } })[0]
        vrf_pref = self._mangle_prefix_result(vrf_pref)
        self.assertEqual(vrf_pref, expected, 'Prefix added with VRF ID reference not equal')

        # add prefix to VRF by specifying VRF
        vrf_pref_attr = {
            'vrf_rt': vrf_attr['rt'],
            'type': 'host',
            'description': 'Test host 1.3.3.1/32 in vrf 123:4567'
        }
        prefix = s.add_prefix({ 'auth': ad, 'attr': vrf_pref_attr, 'args': args })
        expected['id'] = prefix['id']
        expected['vrf_id'] = vrf_attr['id']
        expected['vrf_name'] = vrf_attr['name']
        expected['display_prefix'] = '1.3.3.1/24'
        expected['prefix'] = '1.3.3.1/32'
        expected['indent'] = 1
        expected.update(vrf_pref_attr)

        vrf_pref = s.list_prefix({ 'auth': ad, 'prefix': { 'id': expected['id'] } })[0]
        vrf_pref = self._mangle_prefix_result(vrf_pref)
        self.assertEqual(vrf_pref, expected, 'Prefix added with VRF reference not equal')

        # add prefix to VRF by specifying VRF name
        vrf_pref_attr = {
            'vrf_name': vrf_attr['name'],
            'type': 'host',
            'description': 'Test host 1.3.3.2/32 in vrf 123:4567'
        }
        prefix = s.add_prefix({ 'auth': ad, 'attr': vrf_pref_attr, 'args': args })
        expected['id'] = prefix['id']
        expected['vrf_rt'] = vrf_attr['rt']
        expected['vrf_id'] = vrf_attr['id']
        expected['display_prefix'] = '1.3.3.2/24'
        expected['prefix'] = '1.3.3.2/32'
        expected['indent'] = 1
        expected.update(vrf_pref_attr)

        vrf_pref = s.list_prefix({ 'auth': ad, 'prefix': { 'id': expected['id'] } })[0]
        vrf_pref = self._mangle_prefix_result(vrf_pref)
        self.assertEqual(vrf_pref, expected, 'Prefix added with VRF name reference not equal')



    def test_prefix_add_tags(self):
        """ Verify tag inheritance works correctly
        """
        expected = []
        expected_top = {
                'alarm_priority': None,
                'authoritative_source': 'nipap',
                'avps': {},
                'comment': None,
                'country': None,
                'display_prefix': '1.0.0.0/8',
                'expires': None,
                'external_key': None,
                'family': 4,
                'id': 131,
                'indent': 0,
                'monitor': None,
                'node': None,
                'order_id': None,
                'customer_id': None,
                'pool_id': None,
                'pool_name': None,
                'vrf_id': 0,
                'vrf_rt': None,
                'vrf_name': 'default',
                'inherited_tags': [],
                'vlan': None,
                'status': 'assigned'
            }

        # add the "top" prefix - 1.0.0.0/8
        attr = {
                'prefix': '1.0.0.0/8',
                'description': 'top prefix',
                'type': 'reservation',
                'tags': ['top']
                }
        prefix = s.add_prefix({ 'auth': ad, 'attr': attr })
        expected_top.update(attr)
        expected_top['id'] = prefix['id']

        # add the "bottom" prefix 1.3.3.0/24
        attr = {
                'prefix': '1.3.3.0/24',
                'description': 'bottom prefix',
                'type': 'assignment',
                'tags': ['bottom'],
                }
        prefix = s.add_prefix({ 'auth': ad, 'attr': attr })
        expected_bottom = expected_top.copy()
        expected_bottom.update(attr)
        expected_bottom['id'] = prefix['id']
        expected_bottom['display_prefix'] = '1.3.3.0/24'
        expected_bottom['inherited_tags'] = ['top']
        expected_bottom['indent'] = 1

        # check the list is correct!
        expected = [ expected_top, expected_bottom ]
        self.assertEqual(
                self._mangle_prefix_result(s.list_prefix({ 'auth': ad })),
                expected)

        # add the "middle" prefix 1.3.0.0/16
        attr = {
                'prefix': '1.3.0.0/16',
                'description': 'middle prefix',
                'type': 'reservation',
                'tags': ['middle'],
                }
        prefix = s.add_prefix({ 'auth': ad, 'attr': attr })
        expected_middle = expected_top.copy()
        expected_middle.update(attr)
        expected_middle['id'] = prefix['id']
        expected_middle['display_prefix'] = '1.3.0.0/16'
        expected_middle['inherited_tags'] = ['top']
        expected_middle['indent'] = 1

        expected_bottom['inherited_tags'] = ['middle', 'top']
        expected_bottom['indent'] = 2

        # check the list is correct!
        expected = [ expected_top, expected_middle, expected_bottom ]
        self.assertEqual(
                self._mangle_prefix_result(s.list_prefix({ 'auth': ad })),
                expected)

        # remove middle prefix
        s.remove_prefix({ 'auth': ad, 'prefix': { 'id': expected_middle['id'] } })
        expected_bottom['inherited_tags'] = ['top']
        expected_bottom['indent'] = 1

        # check the list is correct!
        expected = [ expected_top, expected_bottom ]
        self.assertEqual(
                self._mangle_prefix_result(s.list_prefix({ 'auth': ad })),
                expected)

        # remove top prefix
        s.remove_prefix({ 'auth': ad, 'prefix': { 'id': expected_top['id'] } })
        expected_bottom['inherited_tags'] = []
        expected_bottom['indent'] = 0

        # check the list is correct!
        expected = [ expected_bottom ]
        self.assertEqual(
                self._mangle_prefix_result(s.list_prefix({ 'auth': ad })),
                expected)



    def test_prefix_node(self):
        """ Test node constraints

            Setting the node value is not allowed for all prefix types. Make
            sure the constraints are working correctly.
        """
        expected = {
                'alarm_priority': None,
                'authoritative_source': 'nipap',
                'avps': {},
                'comment': None,
                'country': None,
                'type': 'assignment',
                'description': 'test prefix',
                'display_prefix': '1.3.2.0/24',
                'expires': None,
                'external_key': None,
                'family': 4,
                'indent': 0,
                'inherited_tags': [],
                'monitor': None,
                'node': None,
                'order_id': None,
                'customer_id': None,
                'pool_name': None,
                'pool_id': None,
                'tags': [],
                'vrf_rt': None,
                'vrf_id': 0,
                'vrf_name': 'default',
                'vlan': None,
                'status': 'assigned'
            }
        expected_list = []

        attr = {}
        attr['prefix'] = '1.3.2.0/24'
        attr['description'] = 'test prefix'
        attr['type'] = 'assignment'
        # add an assignment which we need later on
        res = s.add_prefix({ 'auth': ad, 'attr': attr })
        exp1 = expected.copy()
        exp1.update(attr)
        exp1['id'] = res['id']

        attr['prefix'] = '1.3.3.0/24'

        # set node
        attr['node'] = 'test'

        # node value is not allowed at all for prefixes of type reservation
        attr['type'] = 'reservation'
        with self.assertRaisesRegexp(xmlrpclib.Fault, "Not allowed to set 'node' value for prefixes of type 'reservation'."):
            s.add_prefix({ 'auth': ad, 'attr': attr })

        # node value is only allowed for assignments when prefix-length is max
        # (/24 for IPv4 or /128 for IPv6).
        attr['type'] = 'assignment'
        with self.assertRaisesRegexp(xmlrpclib.Fault, "Not allowed to set 'node' value for prefixes of type 'assignment' which do not have all bits set in netmask."):
            s.add_prefix({ 'auth': ad, 'attr': attr })

        # correct prefix length
        attr['prefix'] = '1.3.3.0/32'
        res = s.add_prefix({ 'auth': ad, 'attr': attr })

        exp2 = expected.copy()
        exp2.update(attr)
        exp2['id'] = res['id']
        exp2['display_prefix'] = '1.3.3.0'

        # let's add a host too
        attr['type'] = 'host'
        attr['prefix'] = '1.3.2.1/32'
        res = s.add_prefix({ 'auth': ad, 'attr': attr })

        exp3 = expected.copy()
        exp3.update(attr)
        exp3['id'] = res['id']
        exp3['display_prefix'] = '1.3.2.1/24'
        exp3['indent'] = 1

        # note the non-intuitive order
        expected_list.append(exp1)
        expected_list.append(exp3)
        expected_list.append(exp2)

        res = self._mangle_prefix_result(s.list_prefix({ 'auth': ad }))
        self.assertEqual(res, expected_list)



    def test_prefix_add_to_pool(self):
        """ Test adding prefixes to a pool
        """
        # Add a pool
        pool_attr = {
            'name'          : 'pool_1',
            'description'   : 'Test pool #1',
            'default_type'  : 'assignment',
            'ipv4_default_prefix_length' : 24
        }
        pool = s.add_pool({ 'auth': ad, 'attr': pool_attr })

        # Add prefix to pool
        prefix_attr = {
                'prefix': '1.3.0.0/16',
                'type': 'reservation',
                'description': 'FOO',
                'pool_id': pool['id']
            }
        s.add_prefix({ 'auth': ad, 'attr': prefix_attr })

        # Add prefix to pool
        prefix_attr = {
                'prefix': '1.4.0.0/16',
                'type': 'reservation',
                'description': 'FOO',
                'pool_name': 'pool_1'
            }
        s.add_prefix({ 'auth': ad, 'attr': prefix_attr })

        # add a prefix
        prefix_attr = {
                'prefix': '1.5.0.0/16',
                'type': 'reservation',
                'description': 'FOO'
            }
        prefix = s.add_prefix({ 'auth': ad, 'attr': prefix_attr })
        # modify prefix so that it's part of pool
        s.edit_prefix({ 'auth': ad, 'prefix': { 'id': prefix['id'] }, 'attr': { 'pool_id': pool['id'] } })

        # add a prefix
        prefix_attr = {
                'prefix': '1.6.0.0/16',
                'type': 'reservation',
                'description': 'FOO'
            }
        prefix = s.add_prefix({ 'auth': ad, 'attr': prefix_attr })
        # modify prefix so that it's part of pool
        s.edit_prefix({ 'auth': ad, 'prefix': { 'id': prefix['id'] }, 'attr': { 'pool_name': 'pool_1' } })

        res = s.list_pool({ 'auth': ad, 'pool': { 'id': pool['id'] } })
        self.assertEquals(res[0]['prefixes'], ['1.3.0.0/16', '1.4.0.0/16',
        '1.5.0.0/16', '1.6.0.0/16'])



    def test_prefix_from_pool(self):
        """ Add a prefix from a pool
        """

        # Add a pool
        pool_attr = {
            'name'          : 'pool_1',
            'description'   : 'Test pool #1',
            'default_type'  : 'assignment',
            'ipv4_default_prefix_length' : 24
        }
        pool = s.add_pool({ 'auth': ad, 'attr': pool_attr })

        # Add prefix to pool
        parent_prefix_attr = {
                'prefix': '1.3.0.0/16',
                'type': 'reservation',
                'description': 'FOO',
                'pool_id': pool['id']
            }
        s.add_prefix({ 'auth': ad, 'attr': parent_prefix_attr })

        args = { 'from-pool': { 'name': 'pool_1' },
                'family': 4 }
        prefix_attr = {
                'description': 'BAR'
                }
        expected = {
                'prefix': '1.3.0.0/24',
                'display_prefix': '1.3.0.0/24',
                'description': 'BAR',
                'type': 'assignment',
                'comment': None,
                'country': None,
                'monitor': None,
                'node': None,
                'order_id': None,
                'customer_id': None,
                'pool_id': None,
                'pool_name': None,
                'vrf_id': 0,
                'vrf_rt': None,
                'vrf_name': 'default',
                'external_key': None,
                'family': 4,
                'indent': 1,
                'alarm_priority': None,
                'authoritative_source': 'nipap'
                }
        child = s.add_prefix({ 'auth': ad, 'attr': prefix_attr, 'args': args })
        #expected['id'] = child['id']
        #p = s.list_prefix({ 'auth': ad, 'attr': { 'id': child['id'] } })[1]
        #self.assertEquals(p, expected)



    def test_prefix_from_pool_vrf(self):
        """ Add a prefix from a pool in a VRF
        """

        # Add a VRF
        vrf_attr = {
            'name'          : 'vrf_1',
            'description'   : 'Test VRF #1',
            'rt'            : '123:123'
        }
        vrf = s.add_vrf({ 'auth': ad, 'attr': vrf_attr })

        # Add a pool
        pool_attr = {
            'name'          : 'pool_1',
            'description'   : 'Test pool for from-pool test',
            'default_type'  : 'assignment',
            'ipv4_default_prefix_length' : 24
        }
        pool = s.add_pool({ 'auth': ad, 'attr': pool_attr })

        # Add prefix to pool
        parent_prefix_attr = {
                'prefix': '1.3.0.0/16',
                'vrf_rt': '123:123',
                'type': 'reservation',
                'description': 'FOO',
                'pool_id': pool['id']
            }
        s.add_prefix({ 'auth': ad, 'attr': parent_prefix_attr })

        args = { 'from-pool': { 'name': 'pool_1' },
                'family': 4 }
        prefix_attr = {
                'description': 'BAR'
                }
        expected = {
                'prefix': '1.3.0.0/24',
                'display_prefix': '1.3.0.0/24',
                'description': 'BAR',
                'type': 'assignment',
                'comment': None,
                'country': None,
                'monitor': None,
                'node': None,
                'order_id': None,
                'customer_id': None,
                'pool_id': None,
                'pool_name': None,
                'vrf_id': vrf['id'],
                'vrf_rt': '123:123',
                'vrf_name': 'vrf_1',
                'expires': None,
                'external_key': None,
                'family': 4,
                'indent': 1,
                'alarm_priority': None,
                'authoritative_source': 'nipap',
                'avps': {},
                'vlan': None,
                'inherited_tags': [],
                'tags': [],
                'status': 'assigned'
                }
        child = s.add_prefix({ 'auth': ad, 'attr': prefix_attr, 'args': args })
        expected['id'] = child['id']
        p = s.list_prefix({ 'auth': ad, 'attr': { 'id': child['id'] } })[1]
        p = self._mangle_prefix_result(p)
        self.assertEquals(p, expected)



    def test_prefix_edit_return(self):
        """ Check return value of edit_prefix
        """
        p1 = s.add_prefix({ 'auth': ad, 'attr': {
                'prefix': '1.3.3.0/24',
                'type': 'assignment',
                'description': 'FOO'
            } })
        p2 = s.add_prefix({ 'auth': ad, 'attr': {
                'prefix': '1.3.3.1/32',
                'type': 'host',
                'description': 'child 1'
            } })
        p3 = s.add_prefix({ 'auth': ad, 'attr': {
                'prefix': '1.3.3.2/32',
                'type': 'host',
                'description': 'child 2'
            } })
        p4 = s.add_prefix({ 'auth': ad, 'attr': {
                'prefix': '1.3.3.3/32',
                'type': 'host',
                'description': 'child 3'
            } })

        ss_res = s.smart_search_prefix({ 'auth': ad, 'query_string': 'child 2'
            })['result'][0]
        edit_res = s.edit_prefix({ 'auth': ad,
            'prefix': { 'prefix': '1.3.3.2/32' },
            'attr': { 'description': 'Kid 2' } })[0]
        del(edit_res['added'])
        del(edit_res['last_modified'])
        del(ss_res['added'])
        del(ss_res['last_modified'])
        ss_res['description'] = 'Kid 2'
        self.assertEqual(ss_res, edit_res)



    def test_prefix_smart_search(self):
        """ Test the prefix smart search
        """
        p1 = s.add_prefix({ 'auth': ad, 'attr': {
                'prefix': '1.3.3.0/24',
                'type': 'assignment',
                'description': 'FOO'
            } })

        s.add_prefix({ 'auth': ad, 'attr': {
                'prefix': '1.3.3.0/32',
                'type': 'host',
                'description': 'BAR'
            } })

        res = s.smart_search_prefix({ 'auth': ad, 'query_string': 'F' })
        expected = {
                'interpretation': {
                    'interpretation': {
                        'operator': 'regex',
                        'attribute': 'description or comment or node or order_id or customer_id',
                        'interpretation': 'text',
                        'string': 'F'
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
                                    'val2': 'F'
                                },
                                'val2': {
                                    'operator': 'regex_match',
                                    'val1': 'description',
                                    'val2': 'F'
                                }
                            },
                            'val2': {
                                'operator': 'regex_match',
                                'val1': 'node',
                                'val2': 'F'
                            }
                        },
                        'val2': {
                            'operator': 'regex_match',
                            'val1': 'order_id',
                            'val2': 'F'
                        }
                    },
                    'val2': {
                        'operator': 'regex_match',
                        'val1': 'customer_id',
                        'val2': 'F'
                    }
                },
                'search_options': {'include_all_children':
                False, 'max_result': 50, 'include_all_parents': False,
                'parents_depth': 0, 'offset': 0, 'children_depth': 0,
                'parent_prefix': None, 'include_neighbors': False },
                'result': [
                    {'comment': None,
                        'expires': None,
                        'external_key': None,
                        'family': 4,
                        'prefix': '1.3.3.0/24',
                        'authoritative_source': 'nipap',
                        'avps': {},
                        'id': p1['id'],
                        'display_prefix': '1.3.3.0/24',
                        'monitor': None,
                        'children': 1,
                        'prefix_length': 24,
                        'type': 'assignment',
                        'match': True,
                        'node': None,
                        'description': 'FOO',
                        'order_id': None,
                        'customer_id': None,
                        'vrf_id': 0,
                        'vrf_rt': None,
                        'vrf_name': 'default',
                        'pool_id': None,
                        'pool_name': None,
                        'alarm_priority': None,
                        'indent': 0,
                        'country': None,
                        'display': True,
                        'vlan': None,
                        'inherited_tags': [],
                        'tags': [],
                        'status': 'assigned'
                        }
                    ]
            }
        res = self._mangle_prefix_result(res)
        self.assertEqual(res, expected)



    def test_asn_add_list(self):
        """ Add ASN to NIPAP and list it
        """

        attr = {
            'asn': 1,
            'name': 'Test ASN #1'
        }

        # add ASN
        self.assertEqual(s.add_asn({ 'auth': ad, 'attr': attr}), attr, "add_asn did not return correct ASN.")

        # make sure that it got added
        asn = s.list_asn({ 'auth': ad, 'asn': { 'asn': 1 } })
        self.assertEqual(len(asn), 1, "Wrong number of ASNs returned.")
        asn = asn[0]
        self.assertEquals(attr, asn, "ASN in database not equal to what was added.")

        # adding the same ASN again should result in duplicate key error
        with self.assertRaisesRegexp(xmlrpclib.Fault, 'Duplicate value for'):
            s.add_asn({ 'auth': ad, 'attr': attr })



    def test_remove_asn(self):
        """ Remove ASN from NIPAP
        """

        attr = {
            'asn': 2,
            'name': 'Test ASN #2'
        }

        asn = s.add_asn({ 'auth': ad, 'attr': attr })
        s.remove_asn({ 'auth': ad, 'asn': { 'asn': asn['asn'] } })
        self.assertEquals(0, len(s.list_asn({ 'auth': ad, 'asn': { 'asn': 2 } })), "Removed ASN still in database")



    def test_edit_asn(self):
        """ Edit ASNs
        """

        attr = {
            'asn': 3,
            'name': 'Test ASN #3'
        }

        asn = s.add_asn({ 'auth': ad, 'attr': attr })
        s.edit_asn({ 'auth': ad, 'asn': { 'asn': attr['asn'] }, 'attr': { 'name': 'b0rk' } })
        self.assertEquals(s.list_asn({ 'auth': ad, 'asn': { 'asn': 3 } })[0]['name'], 'b0rk', "Edited ASN still has it's old name.")
        with self.assertRaisesRegexp(xmlrpclib.Fault, 'extraneous attribute'):
            s.edit_asn({ 'auth': ad, 'asn': { 'asn': 3 }, 'attr': {'asn': 4, 'name': 'Test ASN #4'} })



    def test_search_asn(self):
        """ Search ASNs
        """

        attr = {
            'asn': 4,
            'name': 'This is AS number 4'
        }

        asn = s.add_asn({ 'auth': ad, 'attr': attr })

        # equal match
        q = {
            'operator': 'equals',
            'val1': 'asn',
            'val2': attr['asn']
        }
        res = s.search_asn({ 'auth': ad, 'query': q })
        self.assertEquals(len(res['result']), 1, "equal search resulted in wrong number of hits")
        self.assertEquals(res['result'][0]['name'], attr['name'], "search hit got wrong name")

        # regexp match
        q = {
            'operator': 'regex_match',
            'val1': 'name',
            'val2': 'number'
        }
        res = s.search_asn({ 'auth': ad, 'query': q })
        self.assertEquals(len(res['result']), 1, "regex search resulted in wrong number of hits")
        self.assertEquals(res['result'][0]['asn'], attr['asn'], "search hit got wrong asn")



    def test_smart_search_asn(self):
        """ Test smart_search_asn function.
        """

        attr = {
            'asn': 5,
            'name': 'Autonomous System Number 5'
        }

        asn = s.add_asn({ 'auth': ad, 'attr': attr })
        res = s.smart_search_asn({ 'auth': ad, 'query_string': "Autonomous" })
        self.assertEquals(len(res['result']), 1, "search resulted in wrong number of hits")
        self.assertEquals(res['result'][0]['asn'], attr['asn'], "search hit got wrong asn")
        self.assertEquals(res['interpretation']['interpretation']['attribute'], 'name', 'search term interpreted as wrong type')

        res = s.smart_search_asn({ 'auth': ad, 'query_string': "5" })
        self.assertEquals(len(res['result']), 1, "search resulted in wrong number of hits")
        self.assertEquals(res['result'][0]['asn'], attr['asn'], "search hit got wrong asn")
        self.assertEquals(res['interpretation']['interpretation']['attribute'], 'asn', "search term interpretated as wrong type")



    def test_pool_add_list(self):
        """ Test adding a pool and verifying it
        """

        # Add a pool
        attr = {
            'description': 'Test pool #1',
            'default_type': 'assignment',
            'ipv4_default_prefix_length': 31,
            'ipv6_default_prefix_length': 112
        }

        with self.assertRaisesRegexp(xmlrpclib.Fault, 'missing attribute name'):
            s.add_pool({ 'auth': ad, 'attr': attr })

        attr['name'] = 'pool_1'
        attr['ipv4_default_prefix_length'] = 50
        with self.assertRaisesRegexp(xmlrpclib.Fault, '1200: \'Default IPv4 prefix length must be an integer between 1 and 32.'):
            s.add_pool({ 'auth': ad, 'attr': attr })

        attr['ipv4_default_prefix_length'] = 31
        attr['ipv6_default_prefix_length'] = 'over 9000'
        with self.assertRaisesRegexp(xmlrpclib.Fault, '1200: \'Default IPv6 prefix length must be an integer between 1 and 128.'):
            s.add_pool({ 'auth': ad, 'attr': attr })

        attr['ipv6_default_prefix_length'] = 112

        res = s.add_pool({ 'auth': ad, 'attr': attr })
        expected = attr.copy()
        expected['id'] = res['id']
        expected['prefixes'] = []
        expected['vrf_id'] = None
        expected['vrf_rt'] = None
        expected['vrf_name'] = None
        expected['tags'] = []
        expected['avps'] = {}

        # list pool and verify data in NIPAP
        p = s.list_pool({ 'auth': ad, 'pool': { 'id': expected['id'] } })
        self.assertEquals(1, len(p), 'Wrong number of pools returned')
        p = p[0]

        self.assertEquals(self._mangle_pool_result(p), expected, 'Received pool differs from added pool')


    def test_edit_pool(self):
        """ Test editing a pool
        """

        # add a pool, we need something to edit
        attr = {
            'name': 'test_pool_2',
            'description': 'Test pool #2',
            'default_type': 'reservation',
            'ipv4_default_prefix_length': 31,
            'ipv6_default_prefix_length': 112
        }

        attr2 = {
            'name': 'test_pool_2_edit',
            'description': 'Test pool #2 edit',
            'default_type': 'assignment',
            'ipv4_default_prefix_length': 30,
            'ipv6_default_prefix_length': 96
        }

        res = s.add_pool({ 'auth': ad, 'attr': attr })
        s.edit_pool({ 'auth': ad, 'pool': { 'id': res['id'] }, 'attr': attr2 })

        expected = attr2.copy()
        expected['id'] = res['id']
        expected['prefixes'] = []
        expected['vrf_id'] = None
        expected['vrf_rt'] = None
        expected['vrf_name'] = None
        expected['tags'] = []
        expected['avps'] = {}

        self.assertEquals(self._mangle_pool_result(s.list_pool({ 'auth': ad,
            'pool': { 'id': res['id'] } })[0]), expected)


    def test_search_pool(self):
        """ Test searching pools
        """


    def test_smart_search_pool(self):
        """ Test smart searching among pools
        """


    def test_remove_pool(self):
        """ Test removing pools
        """


if __name__ == '__main__':

    # set up logging
    log = logging.getLogger()
    logging.basicConfig()
    log.setLevel(logging.INFO)

    if sys.version_info >= (2,7):
        unittest.main(verbosity=2)
    else:
        unittest.main()
