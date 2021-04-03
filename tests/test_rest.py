#!/usr/bin/env python
# vim: et :

#
# All of the tests in this test suite runs directly against the REST API
# interfaces of NIPAP to check return data and so forth.
#

import logging
import unittest
import sys
import os

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(MODULE_DIR + '/../nipap/')

from nipap.backend import Nipap
from nipap.authlib import SqliteAuth
from nipap.nipapconfig import NipapConfig

import requests
import json

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
log_format = "%(levelname)-8s %(message)s"


class NipapRestTest(unittest.TestCase):
    """ Tests the NIPAP REST API

        We presume the database is empty
    """
    maxDiff = None

    logger = None
    cfg = None
    nipap = None

    server_url = "http://unittest:gottatest@127.0.0.1:1337/rest/v1/prefixes"
    headers = {"NIPAP-Authoritative-Source": "nipap", "NIPAP-Username": "unittest", "NIPAP-Full-Name": "unit tester"}

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
                self.assertIn('expires', p)
                del(p['added'])
                del(p['last_modified'])
                del(p['total_addresses'])
                del(p['used_addresses'])
                del(p['free_addresses'])
                del(p['expires'])

        elif isinstance(res, dict) and 'result' in res:
            # res from smart search
            for p in res['result']:
                self.assertIn('added', p)
                self.assertIn('last_modified', p)
                self.assertIn('total_addresses', p)
                self.assertIn('used_addresses', p)
                self.assertIn('free_addresses', p)
                self.assertIn('expires', p)
                del(p['added'])
                del(p['last_modified'])
                del(p['total_addresses'])
                del(p['used_addresses'])
                del(p['free_addresses'])
                del(res['expires'])

        if isinstance(res, dict):
            # just one single prefix
            self.assertIn('added', res)
            self.assertIn('last_modified', res)
            self.assertIn('total_addresses', res)
            self.assertIn('used_addresses', res)
            self.assertIn('free_addresses', res)
            self.assertIn('expires', res)
            del(res['added'])
            del(res['last_modified'])
            del(res['total_addresses'])
            del(res['used_addresses'])
            del(res['free_addresses'])
            del(res['expires'])

        return res


    def _convert_list_of_unicode_to_str(self, list_of_items):
        """ Converts list of unicode values to string

            This helper function converts keys and values in unicode to string for a list containing nested dictionaries.

            When converting JSON respons back to Python dict the keys and values are
            added as unicode. This helper function handles the problem, but all types get replaced to strings. Is used for assertEqual.
        """
        result = []
        for item in list_of_items:
            item = dict([(str(k), str(v)) for k, v in item.items()])
            result.append(item)

        return result


    def test_prefix_add(self):
        """ Add a prefix and list
        """

        # check that some error / sanity checking is there
        attr = {}

        request = requests.post(self.server_url, headers=self.headers, json = attr)
        text = request.text
        self.assertRegexpMatches(text,"'attr' must be a dict")

        attr['prefix'] = '1.3.3.0/24'
        request = requests.post(self.server_url, headers=self.headers, json = attr)
        text = request.text
        self.assertRegexpMatches(text, "Either description or node must be specified.")

        attr['description'] = 'test prefix'
        request = requests.post(self.server_url, headers=self.headers, json = attr)
        text = request.text
        self.assertRegexpMatches(text, "Unknown prefix type")

        attr['type'] = 'assignment'
        attr['order_id'] = 'test'


        # add 1.3.3.0/24
        request = requests.post(self.server_url, headers=self.headers, json = attr)
        text = request.text
        result = json.loads(text)
        result = dict([(str(k), str(v)) for k, v in result.items()])
        attr['id'] = result['id']
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
                'external_key': None,
                'family': 4,
                'id': int(attr['id']),
                'indent': 0,
                'inherited_tags': [],
                'monitor': None,
                'node': None,
                'order_id': 'test',
                'customer_id': None,
                'pool_name': None,
                'pool_id': None,
                'tags':[],
                'status': 'assigned',
                'vrf_rt': None,
                'vrf_id': 0,
                'vrf_name': 'default',
                'vlan': None
            }

        expected = dict([(str(k), str(v)) for k, v in expected.items()])
        expected.update(attr)

        # list of prefixes through GET request
        parameters = {'order_id': 'test'}
        list_prefix_request = request = requests.get(self.server_url, headers=self.headers, params=parameters)
        list_prefix = json.loads(list_prefix_request.text)
        list_prefix = self._convert_list_of_unicode_to_str(list_prefix)

        self.assertEqual(
                self._mangle_prefix_result(list_prefix),
                [expected])

        attr = {}
        attr['description'] = 'test for from-prefix 1.3.3.0/24'
        attr['type'] = 'host'
        attr['order_id'] = 'test'

        parameters = {'fromPrefix': '1.3.3.0/24', 'prefixLength': 32}

        # add a host in 1.3.3.0/24
        request = requests.post(self.server_url, headers=self.headers, json = attr, params = parameters)
        text = request.text
        result = json.loads(text)
        result = dict([(str(k), str(v)) for k, v in result.items()])

        # copy expected from 1.3.3.0/24 since we expect most things to look the
        # same for the new prefix (1.3.3.1/32) from 1.3.3.0/24
        expected_host = expected.copy()
        expected_host.update(attr)
        expected_host['id'] = result['id']
        expected_host['prefix'] = '1.3.3.1/32'
        expected_host['display_prefix'] = '1.3.3.1/24'
        expected_host['indent'] = 1

        # build list of expected
        expected_list = []
        expected_list.append(expected)
        expected_list.append(expected_host)
        expected_list = self._convert_list_of_unicode_to_str(expected_list)

        # add another prefix, try with vrf_id = None
        attr['vrf_id'] = None
        request = requests.post(self.server_url, headers=self.headers, json = attr, params = parameters)
        text = request.text
        result = json.loads(text)
        result = dict([(str(k), str(v)) for k, v in result.items()])
        # update expected list
        expected_host2 = expected_host.copy()
        expected_host2['id'] = result['id']
        expected_host2['prefix'] = '1.3.3.2/32'
        expected_host2['display_prefix'] = '1.3.3.2/24'
        expected_list.append(expected_host2)
        expected_list = self._convert_list_of_unicode_to_str(expected_list)

        # add another prefix, this time completely without VRF info
        del(attr['vrf_id'])
        request = requests.post(self.server_url, headers=self.headers, json = attr, params = parameters)
        text = request.text
        result = json.loads(text)
        result = dict([(str(k), str(v)) for k, v in result.items()])
        # update expected list
        expected_host3 = expected_host.copy()
        expected_host3['id'] = result['id']
        expected_host3['prefix'] = '1.3.3.3/32'
        expected_host3['display_prefix'] = '1.3.3.3/24'
        expected_list.append(expected_host3)
        expected_list = self._convert_list_of_unicode_to_str(expected_list)

        # list of prefixes through GET request
        parameters = {'order_id': 'test'}
        list_prefix_request = request = requests.get(self.server_url, headers=self.headers, params=parameters)
        list_prefix = json.loads(list_prefix_request.text)
        list_prefix = self._convert_list_of_unicode_to_str(list_prefix)

        mangled_result = self._mangle_prefix_result(list_prefix)

        # make sure the result looks like we expect it too! :D
        self.assertEqual(
                mangled_result,
                expected_list)

    def test_prefix_remove(self):
        """ Removes a prefix
        """

        # add 1.3.3.4/24
        attr = {}
        attr['prefix'] = '1.3.4.0/24'
        attr['description'] = 'test delete prefix'
        attr['type'] = 'assignment'
        attr['order_id'] = 'test'

        request = requests.post(self.server_url, headers=self.headers, json = attr)
        text = request.text
        result = json.loads(text)
        result = dict([(str(k), str(v)) for k, v in result.items()])

        prefix_id = result['id']

        # delete prefix
        parameters = {'id': prefix_id}
        request = requests.delete(self.server_url, headers=self.headers, params=parameters)
        text = request.text
        result = json.loads(text)
        result = dict([(str(k), str(v)) for k, v in result.items()])

        expected = {
                'prefix': '1.3.4.0/24',
                'vrf_id': '0',
            }

        self.assertEqual(result, expected)



if __name__ == '__main__':

    # set up logging
    log = logging.getLogger()
    logging.basicConfig()
    log.setLevel(logging.INFO)

    if sys.version_info >= (2,7):
        unittest.main(verbosity=2)
    else:
        unittest.main()
