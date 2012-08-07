#!/usr/bin/python
# vim: et :

import logging
import unittest
import sys
sys.path.append('../nipap/')

import nipap.nipap
from nipap.authlib import SqliteAuth
from nipap.nipapconfig import NipapConfig

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
log_format = "%(levelname)-8s %(message)s"

import xmlrpclib

server_url = "http://guest:guest@127.0.0.1:1337/XMLRPC"
s = xmlrpclib.Server(server_url, allow_none=1);

ad = { 'authoritative_source': 'nipap' }

class NipapXmlTest(unittest.TestCase):
    """ Tests the NIPAP XML-RPC daemon

        We presume the database is empty
    """
    maxDiff = None

    logger = logging.getLogger()
    cfg = NipapConfig('/etc/nipap/nipap.conf')
    nipap = nipap.nipap.Nipap()

    def setUp(self):
        # create dummy auth object
        # As the authentication is performed before the query hits the Nipap
        # class, it does not matter what user we use here
        self.auth = SqliteAuth('local', 'unittest', 'unittest', 'unittest')
        self.auth.authenticated_as = 'unittest'
        self.auth.full_name = 'Unit test'

        self.nipap._execute("DELETE FROM ip_net_vrf WHERE id > 0")
        self.nipap._execute("DELETE FROM ip_net_plan WHERE masklen(prefix) = 32")
        self.nipap._execute("DELETE FROM ip_net_plan")



    def test_vrf_add_list(self):
        """ Add a VRF and verify correct input
        """
        attr = {}
        with self.assertRaisesRegexp(xmlrpclib.Fault, 'missing attribute vrf'):
            s.add_vrf({ 'auth': ad, 'attr': attr })

        attr['vrf'] = '123:456'
        with self.assertRaisesRegexp(xmlrpclib.Fault, 'missing attribute name'):
            s.add_vrf({ 'auth': ad, 'attr': attr })

        attr['name'] = 'test'
        with self.assertRaisesRegexp(xmlrpclib.Fault, 'missing attribute description'):
            s.add_vrf({ 'auth': ad, 'attr': attr })

        attr['description'] = 'my test vrf'
        attr['id'] = s.add_vrf({ 'auth': ad, 'attr': attr })

        self.assertGreater(attr['id'], 0)

        expected = [{
            'id': 0,
            'name': None,
            'vrf': None,
            'description': None
            }]
        expected.append(attr)
        self.assertEqual(s.list_vrf({ 'auth': ad, 'vrf': {} }), expected)

        attr['vrf'] = '123:abc'
        with self.assertRaisesRegexp(xmlrpclib.Fault, '.'): # TODO: specify exception string
            s.add_vrf({ 'auth': ad, 'attr': attr })



    def test_vrf_edit(self):
        """ Edit VRF and verify the change
        """
        attr = {
            'vrf': '65000:123',
            'name': '65k:123',
            'description': 'VRF 65000:123'
        }
        spec = { 'vrf': '65000:123' }
        s.add_vrf({ 'auth': ad, 'attr': attr })

        # omitting VRF spec
        with self.assertRaisesRegexp(xmlrpclib.Fault, 'vrf specification must be a dict'):
            s.edit_vrf({ 'auth': ad, 'attr': { 'name': 'test_vrf_edit' } })

        # omitting VRF attributes
        with self.assertRaisesRegexp(xmlrpclib.Fault, 'invalid input type, must be dict'):
            s.edit_vrf({ 'auth': ad, 'vrf': spec })

        # specifying too many attributes in spec
        with self.assertRaisesRegexp(xmlrpclib.Fault, 'specification contains too many keys'):
            s.edit_vrf({ 'auth': ad, 'vrf': { 'vrf': '65000:123', 'name': '65k:123' }, 'attr': {} })

        # test changing ID
        with self.assertRaisesRegexp(xmlrpclib.Fault, 'extraneous attribute'):
            s.edit_vrf({ 'auth': ad, 'vrf': spec, 'attr': { 'id': 1337 } })

        # empty attribute list
        s.edit_vrf({ 'auth': ad, 'vrf': spec, 'attr': {} })
        res = s.list_vrf({ 'auth': ad, 'vrf': spec })
        self.assertEquals(len(res), 1, 'wrong number of VRFs returned')
        res = res[0]
        self.assertEqual(res, attr, 'VRF changed after empty edit_vrf operation')

        # valid change
        attr['vrf'] = '65000:1234'
        attr['name'] = '65k:1234'
        attr['description'] = 'VRF 65000:1234'
        s.edit_vrf({ 'auth': ad, 'vrf': spec, 'attr': attr })

        # verify result of valid change
        res = s.list_vrf({ 'auth': ad, 'vrf': { 'vrf': attr['vrf'] } })
        self.assertEquals(len(res), 1, 'wrong number of VRFs returned')
        res = res[0]
        self.assertEqual(res, attr, 'VRF change incorrect')



    def test_vrf_add_search(self):
        """ Add VRF and search for it
        """

        # add VRF
        attr = {
            'vrf': '65000:1235',
            'name': '65k:1235',
            'description': 'Virtual Routing and Forwarding instance 65000:123'
        }
        attr['id'] = s.add_vrf({ 'auth': ad, 'attr': attr })

        # equal match
        q = {
            'operator': 'equals',
            'val1': 'vrf',
            'val2': attr['vrf']
        }
        res = s.search_vrf({ 'auth': ad, 'query': q })
        self.assertEquals(res['result'], [ attr, ], 'Search result from equal match did not match')

        # regex match
        q = {
            'operator': 'regex_match',
            'val1': 'description',
            'val2': 'instance 65000'
        }
        res = s.search_vrf({ 'auth': ad, 'query': q })
        self.assertEquals(res['result'], [ attr, ], 'Search result from regex match did not match')

        # smart search
        res = s.smart_search_vrf({ 'auth': ad, 'query_string': 'forwarding instance' })
        self.assertEquals(res['result'], [ attr, ], 'Smart search result did not match')



    def test_prefix_add(self):
        """ Add a prefix and list
        """
        attr = {}
        with self.assertRaisesRegexp(xmlrpclib.Fault, "specify 'prefix' or 'from-prefix' or 'from-pool'"):
            s.add_prefix({ 'auth': ad, 'attr': attr })

        attr['prefix'] = '1.3.3.0/24'
        with self.assertRaisesRegexp(xmlrpclib.Fault, "Either description or host must be specified."):
            s.add_prefix({ 'auth': ad, 'attr': attr })

        attr['description'] = 'test prefix'
        with self.assertRaisesRegexp(xmlrpclib.Fault, "Unknown prefix type"):
            s.add_prefix({ 'auth': ad, 'attr': attr })

        attr['type'] = 'assignment'

        attr['id'] = s.add_prefix({ 'auth': ad, 'attr': attr })
        self.assertGreater(attr['id'], 0)

        expected = {
                'alarm_priority': None,
                'authoritative_source': 'nipap',
                'comment': None,
                'country': None,
                'description': 'test prefix',
                'display_prefix': '1.3.3.0/24',
                'external_key': None,
                'family': 4,
                'id': 131,
                'indent': 0,
                'monitor': None,
                'node': None,
                'order_id': None,
                'pool': None,
                'vrf': None,
                'vrf_name': None
            }
        expected.update(attr)
        self.assertEqual(s.list_prefix({ 'auth': ad }), [expected])

        attr = {
                'description': 'test for from-prefix 1.3.3.0/24',
                'type': 'host'
            }
        args = { 'from-prefix': ['1.3.3.0/24'], 'prefix_length': 32 }
        res = s.add_prefix({ 'auth': ad, 'attr': attr, 'args': args })

        expected_host = expected.copy()
        expected_host.update(attr)
        expected_host['id'] = res
        expected_host['prefix'] = '1.3.3.1/32'
        expected_host['display_prefix'] = '1.3.3.1/24'
        expected_host['indent'] = 1
        expected_list = []
        expected_list.append(expected)
        expected_list.append(expected_host)
        self.assertEqual(s.list_prefix({ 'auth': ad }), expected_list)



if __name__ == '__main__':
    if sys.version_info >= (2,7):
        unittest.main(verbosity=2)
    else:
        unittest.main()
