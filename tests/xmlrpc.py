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

    logger = None
    cfg = None
    nipap = None

    def setUp(self):

        # logging
        self.logger = logging.getLogger(self.__class__.__name__)

        # NIPAP
        self.cfg = NipapConfig('/etc/nipap/nipap.conf')
        self.nipap = nipap.nipap.Nipap()

        # create dummy auth object
        # As the authentication is performed before the query hits the Nipap
        # class, it does not matter what user we use here
        self.auth = SqliteAuth('local', 'unittest', 'unittest', 'unittest')
        self.auth.authenticated_as = 'unittest'
        self.auth.full_name = 'Unit test'

        self.nipap._execute("DELETE FROM ip_net_vrf WHERE id > 0")
        self.nipap._execute("DELETE FROM ip_net_plan WHERE masklen(prefix) = 32")
        self.nipap._execute("DELETE FROM ip_net_plan")
        self.nipap._execute("DELETE FROM ip_net_asn")



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
                'pool_id': None,
                'vrf': None,
                'vrf_name': None,
                'vrf_id': 0
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



    def test_prefix_smart_search(self):
        """ Add a prefix and list
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
                'interpretation': [{'operator': 'regex', 'attribute':
                    'description or comment or node or order id', 'interpretation':
                    'text', 'string': 'F'}],
                'search_options': {'include_all_children':
                False, 'max_result': 50, 'include_all_parents': False,
                'parents_depth': 0, 'offset': 0, 'children_depth': 0},
                'result': [
                    {'comment': None,
                        'external_key': None,
                        'family': 4,
                        'prefix': '1.3.3.0/24',
                        'authoritative_source': 'nipap',
                        'id': p1,
                        'display_prefix': '1.3.3.0/24',
                        'monitor': None,
                        'children': -2,
                        'prefix_length': 24,
                        'type': 'assignment',
                        'match': True,
                        'node': None,
                        'description': 'FOO',
                        'order_id': None,
                        'vrf': None,
                        'vrf_id': 0,
                        'pool': None,
                        'pool_id': None,
                        'alarm_priority': None,
                        'indent': 0,
                        'country': None,
                        'vrf_name': None,
                        'display': True
                        }
                    ]
            }
        self.assertEqual(res, expected)



    def test_asn_add_list(self):
        """ Add ASN to NIPAP and list it
        """

        attr = {
            'asn': 1,
            'name': 'Test ASN #1'
        }

        # add ASN
        self.assertEqual(s.add_asn({ 'auth': ad, 'attr': attr}), 1, "add_asn did not return correct ASN.")

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
        s.remove_asn({ 'auth': ad, 'asn': { 'asn': asn } })
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
        self.assertEquals(res['interpretation'][0]['attribute'], 'name', "search term interpretated as wrong type")

        res = s.smart_search_asn({ 'auth': ad, 'query_string': "5" })
        self.assertEquals(len(res['result']), 1, "search resulted in wrong number of hits")
        self.assertEquals(res['result'][0]['asn'], attr['asn'], "search hit got wrong asn")
        self.assertEquals(res['interpretation'][0]['attribute'], 'asn', "search term interpretated as wrong type")



if __name__ == '__main__':

    # set up logging
    log = logging.getLogger()
    logging.basicConfig()
    log.setLevel(logging.INFO)

    if sys.version_info >= (2,7):
        unittest.main(verbosity=2)
    else:
        unittest.main()
