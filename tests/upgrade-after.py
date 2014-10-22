#!/usr/bin/env python
# vim: et :
#
# This is run by Travis-CI after an upgrade to verify that the data loaded by
# upgrade-before.py has been correctly updated in the upgrade process. For
# example, new columns might have been added and the value of those columns
# should be automatically updated. This test should be used to verify such
# things.
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


class TestCheckdata(unittest.TestCase):
    """ Tests the NIPAP XML-RPC daemon
    """
    maxDiff = None

    def _mangle_pool_result(self, res):
        """ Mangle pool result for easier testing

            We can never predict the values of things like the ID (okay, that
            one is actually kind of doable) or the added and last_modified
            timestamp. This function will make sure the values are present but
            then strip them to make it easier to test against an expected
            result.
        """

        if isinstance(res, list):
            # res from list_prefix
            for p in res:
                self.assertIn('id', p)
                del(p['id'])

        elif isinstance(res, dict) and 'result' in res:
            # res from smart search
            for p in res['result']:
                self.assertIn('id', p)
                del(p['id'])

        elif isinstance(res, dict):
            # just one single prefix
            self.assertIn('id', res)
            del(res['id'])

        return res



    def _mangle_prefix_result(self, res):
        """ Mangle prefix result for easier testing

            We can never predict the values of things like the ID (okay, that
            one is actually kind of doable) or the added and last_modified
            timestamp. This function will make sure the values are present but
            then strip them to make it easier to test against an expected
            result.
        """

        if isinstance(res, list):
            # res from list_prefix
            for p in res:
                self.assertIn('added', p)
                self.assertIn('last_modified', p)
                self.assertIn('id', p)
                self.assertIn('pool_id', p)
                del(p['added'])
                del(p['last_modified'])
                del(p['id'])
                del(p['pool_id'])

        elif isinstance(res, dict) and 'result' in res:
            # res from smart search
            for p in res['result']:
                self.assertIn('added', p)
                self.assertIn('last_modified', p)
                self.assertIn('id', p)
                self.assertIn('pool_id', p)
                del(p['added'])
                del(p['last_modified'])
                del(p['id'])
                del(p['pool_id'])

        elif isinstance(res, dict):
            # just one single prefix
            self.assertIn('added', res)
            self.assertIn('last_modified', res)
            self.assertIn('id', res)
            self.assertIn('pool_id', res)
            del(res['added'])
            del(res['last_modified'])
            del(res['id'])
            del(res['pool_id'])

        return res



    def _mangle_vrf_result(self, res):
        """ Mangle vrf result for easier testing

            We can never predict the values of things like the ID (okay, that
            one is actually kind of doable) or the added and last_modified
            timestamp. This function will make sure the values are present but
            then strip them to make it easier to test against an expected
            result.
        """

        if isinstance(res, list):
            # res from list_prefix
            for p in res:
                self.assertIn('id', p)
                del(p['id'])

        elif isinstance(res, dict) and 'result' in res:
            # res from smart search
            for p in res['result']:
                self.assertIn('id', p)
                del(p['id'])

        elif isinstance(res, dict):
            # just one single prefix
            self.assertIn('id', res)
            del(res['id'])

        return res



    def test_verify_prefix(self):
        """ Verify data after upgrade
        """
        expected_base = {
                'alarm_priority': None,
                'authoritative_source': 'nipap',
                'avps': {},
                'comment': None,
                'country': None,
                'description': 'test',
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
                'tags': [],
                'type': 'reservation',
                'vrf_rt': None,
                'vrf_id': 0,
                'vrf_name': 'default',
                'vlan': None,
                'status': 'assigned'
            }
        expected_prefixes = [
                { 'prefix': '192.168.0.0/16', 'indent': 0, 'total_addresses':
                    '65536', 'used_addresses': '8192', 'free_addresses': '57344' },
                { 'prefix': '192.168.0.0/20', 'indent': 1, 'total_addresses':
                    '4096', 'used_addresses': '768', 'free_addresses': '3328',
                    'pool_name': 'upgrade-test' },
                { 'prefix': '192.168.0.0/24', 'indent': 2, 'total_addresses':
                    '256', 'used_addresses': '0', 'free_addresses': '256' },
                { 'prefix': '192.168.1.0/24', 'indent': 2, 'total_addresses':
                    '256', 'used_addresses': '0', 'free_addresses': '256' },
                { 'prefix': '192.168.2.0/24', 'indent': 2, 'total_addresses':
                    '256', 'used_addresses': '0', 'free_addresses': '256' },
                { 'prefix': '192.168.32.0/20', 'indent': 1, 'total_addresses':
                    '4096', 'used_addresses': '256', 'free_addresses': '3840' },
                { 'prefix': '192.168.32.0/24', 'indent': 2, 'total_addresses':
                    '256', 'used_addresses': '1', 'free_addresses': '255' },
                { 'prefix': '192.168.32.1/32', 'display_prefix': '192.168.32.1',
                    'indent': 3, 'total_addresses': '1', 'used_addresses': '1',
                    'free_addresses': '0' },
                { 'prefix': '2001:db8:1::/48', 'indent': 0, 'family': 6,
                    'pool_name': 'upgrade-test',
                    'total_addresses': '1208925819614629174706176',
                    'used_addresses': '18446744073709551616',
                    'free_addresses': '1208907372870555465154560' },
                { 'prefix': '2001:db8:1::/64', 'indent': 1, 'family': 6,
                    'total_addresses': '18446744073709551616', 'used_addresses': '0',
                    'free_addresses': '18446744073709551616' },
                { 'prefix': '2001:db8:2::/48', 'indent': 0, 'family': 6,
                    'total_addresses': '1208925819614629174706176',
                    'used_addresses': '0',
                    'free_addresses': '1208925819614629174706176' },
                ]
        expected = []
        for p in expected_prefixes:
            pexp = expected_base.copy()
            for key in p:
                pexp[key] = p[key]
            if 'display_prefix' not in pexp:
                pexp['display_prefix'] = p['prefix']
            expected.append(pexp)

        self.assertEqual(expected, self._mangle_prefix_result(s.list_prefix({ 'auth': ad, })))



    def test_pool1(self):
        """ Verify data after upgrade
        """
        expected = [{
            'used_prefixes_v4': '3',
            'used_prefixes_v6': '1',
            'free_prefixes_v4': '1664',
            'free_prefixes_v6': '18446462598732840960',
            'total_prefixes_v4': '1667',
            'total_prefixes_v6': '18446462598732840961',
            'default_type': None,
            'description': None,
            'free_addresses_v4': '3328',
            'free_addresses_v6': '1208907372870555465154560',
            'ipv4_default_prefix_length': 31,
            'ipv6_default_prefix_length': 112,
            'member_prefixes_v4': '1',
            'member_prefixes_v6': '1',
            'name': 'upgrade-test',
            'prefixes': [ '192.168.0.0/20', '2001:db8:1::/48' ],
            'total_addresses_v4': '4096',
            'total_addresses_v6': '1208925819614629174706176',
            'used_addresses_v4': '768',
            'used_addresses_v6': '18446744073709551616',
            'vrf_id': 0,
            'vrf_name': 'default',
            'vrf_rt': None,
            'tags': [],
            'avps': {}
            }]
        self.assertEqual(expected, self._mangle_pool_result(s.list_pool({ 'auth': ad, 'pool': { 'name': 'upgrade-test' } })))



    def test_pool2(self):
        """ Verify data after upgrade
        """
        expected = [{
            'used_prefixes_v4': '0',
            'used_prefixes_v6': '0',
            'free_prefixes_v4': None,
            'free_prefixes_v6': None,
            'total_prefixes_v4': None,
            'total_prefixes_v6': None,
            'default_type': None,
            'description': None,
            'free_addresses_v4': '0',
            'free_addresses_v6': '0',
            'ipv4_default_prefix_length': None,
            'ipv6_default_prefix_length': None,
            'member_prefixes_v4': '0',
            'member_prefixes_v6': '0',
            'name': 'upgrade-test2',
            'prefixes': [ ],
            'total_addresses_v4': '0',
            'total_addresses_v6': '0',
            'used_addresses_v4': '0',
            'used_addresses_v6': '0',
            'vrf_id': None,
            'vrf_name': None,
            'vrf_rt': None,
            'tags': [],
            'avps': {}
            }]
        self.assertEqual(expected, self._mangle_pool_result(s.list_pool({ 'auth': ad, 'pool': { 'name': 'upgrade-test2' } })))



    def test_vrf1(self):
        """ Verify empty VRF looks good
        """
        expected = [
            {'description': None,
            'free_addresses_v4': '0',
            'free_addresses_v6': '0',
            'name': 'foo',
            'num_prefixes_v4': '0',
            'num_prefixes_v6': '0',
            'rt': '123:123',
            'total_addresses_v4': '0',
            'total_addresses_v6': '0',
            'used_addresses_v4': '0',
            'used_addresses_v6': '0',
            'tags': [],
            'avps': {}
            }]

        self.assertEqual(expected, self._mangle_vrf_result(s.list_vrf({ 'auth':
            ad, 'vrf': { 'name': 'foo' } })))



    def test_vrf2(self):
        """ Verify default VRF looks good with prefixes
        """
        expected = [
            {
            'description': 'The default VRF, typically the Internet.',
            'free_addresses_v4': '57344',
            'free_addresses_v6': '2417833192485184639860736',
            'name': 'default',
            'num_prefixes_v4': '8',
            'num_prefixes_v6': '3',
            'rt': None,
            'total_addresses_v4': '65536',
            'total_addresses_v6': '2417851639229258349412352',
            'used_addresses_v4': '8192',
            'used_addresses_v6': '18446744073709551616',
            'tags': [],
            'avps': {}
            }]

        self.assertEqual(expected, self._mangle_vrf_result(s.list_vrf({ 'auth':
            ad, 'vrf': { 'name': 'default' } })))



if __name__ == '__main__':

    # set up logging
    log = logging.getLogger()
    logging.basicConfig()
    log.setLevel(logging.INFO)

    if sys.version_info >= (2,7):
        unittest.main(verbosity=2)
    else:
        unittest.main()
