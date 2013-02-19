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

        # have to delete hosts before we can delete the rest
        self.nipap._execute("DELETE FROM ip_net_plan WHERE masklen(prefix) = 32")
        # the rest
        self.nipap._execute("DELETE FROM ip_net_plan")
        # delete all except for the default VRF with id 0
        self.nipap._execute("DELETE FROM ip_net_vrf WHERE id > 0")
        self.nipap._execute("DELETE FROM ip_net_pool")
        self.nipap._execute("DELETE FROM ip_net_asn")



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

        attr['description'] = 'my test vrf'
        attr['id'] = s.add_vrf({ 'auth': ad, 'attr': attr })

        self.assertGreater(attr['id'], 0)

        self.assertEqual(s.list_vrf({ 'auth': ad, 'vrf': {} }), [ attr, ])

        attr['rt'] = '123:abc'
        with self.assertRaisesRegexp(xmlrpclib.Fault, '.'): # TODO: specify exception string
            s.add_vrf({ 'auth': ad, 'attr': attr })



    def test_vrf_edit(self):
        """ Edit VRF and verify the change
        """
        attr = {
            'rt': '65000:123',
            'name': '65k:123',
            'description': 'VRF 65000:123'
        }
        spec = { 'rt': '65000:123' }
        s.add_vrf({ 'auth': ad, 'attr': attr })

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
        self.assertEqual(res, attr, 'VRF changed after empty edit_vrf operation')

        # valid change
        attr['rt'] = '65000:1234'
        attr['name'] = '65k:1234'
        attr['description'] = 'VRF 65000:1234'
        s.edit_vrf({ 'auth': ad, 'vrf': spec, 'attr': attr })

        # verify result of valid change
        res = s.list_vrf({ 'auth': ad, 'vrf': { 'rt': attr['rt'] } })
        self.assertEquals(len(res), 1, 'wrong number of VRFs returned')
        res = res[0]
        # ignore the ID
        del(res['id'])
        self.assertEqual(res, attr, 'VRF change incorrect')



    def test_vrf_add_search(self):
        """ Add VRF and search for it
        """

        # add VRF
        attr = {
            'rt': '65000:1235',
            'name': '65k:1235',
            'description': 'Virtual Routing and Forwarding instance 65000:123'
        }
        attr['id'] = s.add_vrf({ 'auth': ad, 'attr': attr })

        # equal match
        q = {
            'operator': 'equals',
            'val1': 'rt',
            'val2': attr['rt']
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
        with self.assertRaisesRegexp(xmlrpclib.Fault, "Either description or node must be specified."):
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
                'pool_name': None,
                'pool_id': None,
                'vrf_rt': None,
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



    def test_prefix_add_vrf(self):
        """ Test adding prefixes to VRF
        """

        args = { 'from-prefix': ['1.3.3.0/24'], 'prefix_length': 32 }
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
                'pool_id': None,
                'pool_name': None,
                'vrf_id': 0,
                'vrf_rt': None,
                'vrf_name': None
            }

        # add VRF
        vrf_attr = {
            'rt': '123:4567',
            'name': 'test_prefix_add_vrf1',
        }
        vrf_attr['id'] = s.add_vrf({ 'auth': ad, 'attr': vrf_attr })

        # add prefix to VRF by specifying ID
        vrf_pref_attr = {
            'prefix': '1.3.3.0/24',
            'vrf_id': vrf_attr['id'],
            'type': 'assignment',
            'description': 'Test prefix 1.3.3.0/24 in vrf 123:4567'
        }
        expected['id'] = s.add_prefix({ 'auth': ad, 'attr': vrf_pref_attr })
        expected['vrf_rt'] = vrf_attr['rt']
        expected['vrf_name'] = vrf_attr['name']
        expected['display_prefix'] = '1.3.3.0/24'
        expected['indent'] = 0
        expected.update(vrf_pref_attr)

        vrf_pref = s.list_prefix({ 'auth': ad, 'prefix': { 'id': expected['id'] } })[0]
        self.assertEqual(vrf_pref, expected, 'Prefix added with VRF ID reference not equal')

        # add prefix to VRF by specifying VRF
        vrf_pref_attr = {
            'vrf_rt': vrf_attr['rt'],
            'type': 'host',
            'description': 'Test host 1.3.3.1/32 in vrf 123:4567'
        }
        expected['id'] = s.add_prefix({ 'auth': ad, 'attr': vrf_pref_attr, 'args': args })
        expected['vrf_id'] = vrf_attr['id']
        expected['vrf_name'] = vrf_attr['name']
        expected['display_prefix'] = '1.3.3.1/24'
        expected['prefix'] = '1.3.3.1/32'
        expected['indent'] = 1
        expected.update(vrf_pref_attr)

        vrf_pref = s.list_prefix({ 'auth': ad, 'prefix': { 'id': expected['id'] } })[0]
        self.assertEqual(vrf_pref, expected, 'Prefix added with VRF reference not equal')

        # add prefix to VRF by specifying VRF name
        vrf_pref_attr = {
            'vrf_name': vrf_attr['name'],
            'type': 'host',
            'description': 'Test host 1.3.3.2/32 in vrf 123:4567'
        }
        expected['id'] = s.add_prefix({ 'auth': ad, 'attr': vrf_pref_attr, 'args': args })
        expected['vrf_rt'] = vrf_attr['rt']
        expected['vrf_id'] = vrf_attr['id']
        expected['display_prefix'] = '1.3.3.2/24'
        expected['prefix'] = '1.3.3.2/32'
        expected['indent'] = 1
        expected.update(vrf_pref_attr)

        vrf_pref = s.list_prefix({ 'auth': ad, 'prefix': { 'id': expected['id'] } })[0]
        self.assertEqual(vrf_pref, expected, 'Prefix added with VRF name reference not equal')



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
        pool_id = s.add_pool({ 'auth': ad, 'attr': pool_attr })

        # Add prefix to pool
        parent_prefix_attr = {
                'prefix': '1.3.0.0/16',
                'type': 'reservation',
                'description': 'FOO',
                'pool_id': pool_id
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
                'pool_id': None,
                'pool_name': None,
                'vrf_id': 0,
                'vrf_rt': None,
                'vrf_name': None,
                'external_key': None,
                'family': 4,
                'indent': 1,
                'alarm_priority': None,
                'authoritative_source': 'nipap'
                }
        child_id = s.add_prefix({ 'auth': ad, 'attr': prefix_attr, 'args': args })
        #expected['id'] = child_id
        #p = s.list_prefix({ 'auth': ad, 'attr': { 'id': child_id } })[1]
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
        vrf_id = s.add_vrf({ 'auth': ad, 'attr': vrf_attr })

        # Add a pool
        pool_attr = {
            'name'          : 'pool_1',
            'description'   : 'Test pool for from-pool test',
            'default_type'  : 'assignment',
            'ipv4_default_prefix_length' : 24
        }
        pool_id = s.add_pool({ 'auth': ad, 'attr': pool_attr })

        # Add prefix to pool
        parent_prefix_attr = {
                'prefix': '1.3.0.0/16',
                'vrf_rt': '123:123',
                'type': 'reservation',
                'description': 'FOO',
                'pool_id': pool_id
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
                'pool_id': None,
                'pool_name': None,
                'vrf_id': vrf_id,
                'vrf_rt': '123:123',
                'vrf_name': 'vrf_1',
                'external_key': None,
                'family': 4,
                'indent': 1,
                'alarm_priority': None,
                'authoritative_source': 'nipap'
                }
        child_id = s.add_prefix({ 'auth': ad, 'attr': prefix_attr, 'args': args })
        expected['id'] = child_id
        p = s.list_prefix({ 'auth': ad, 'attr': { 'id': child_id } })[1]
        self.assertEquals(p, expected)



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
                'parents_depth': 0, 'offset': 0, 'children_depth': 0,
                'parent_prefix': None },
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
                        'vrf_id': None,
                        'vrf_rt': None,
                        'vrf_name': None,
                        'pool_id': None,
                        'pool_name': None,
                        'alarm_priority': None,
                        'indent': 0,
                        'country': None,
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
        expected['id'] = res
        expected['prefixes'] = []
        expected['vrf_id'] = None
        expected['vrf_rt'] = None
        expected['vrf_name'] = None

        # list pool and verify data in NIPAP
        p = s.list_pool({ 'auth': ad, 'pool': { 'id': expected['id'] } })
        self.assertEquals(1, len(p), 'Wrong number of pools returned')
        p = p[0]

        self.assertEquals(p, expected, 'Received pool differs from added pool')


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
        s.edit_pool({ 'auth': ad, 'pool': { 'id': res }, 'attr': attr2 })

        expected = attr2.copy()
        expected['id'] = res
        expected['prefixes'] = []
        expected['vrf_id'] = None
        expected['vrf_rt'] = None
        expected['vrf_name'] = None

        self.assertEquals(s.list_pool({ 'auth': ad, 'pool': { 'id': res } })[0], expected)


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
