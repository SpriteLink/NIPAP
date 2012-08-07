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


if __name__ == '__main__':
    if sys.version_info >= (2,7):
        unittest.main(verbosity=2)
    else:
        unittest.main()
