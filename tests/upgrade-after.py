#!/usr/bin/python
# vim: et :

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
                del(p['added'])
                del(p['last_modified'])
                del(p['id'])

        elif isinstance(res, dict) and 'result' in res:
            # res from smart search
            for p in res['result']:
                self.assertIn('added', p)
                self.assertIn('last_modified', p)
                self.assertIn('id', p)
                del(p['added'])
                del(p['last_modified'])
                del(p['id'])

        elif isinstance(res, dict):
            # just one single prefix
            self.assertIn('added', res)
            self.assertIn('last_modified', res)
            self.assertIn('id', res)
            del(res['added'])
            del(res['last_modified'])
            del(res['id'])

        return res


    def test_verify_prefix(self):
        """ Verify data after upgrade
        """
        expected_base = {
                'alarm_priority': None,
                'authoritative_source': 'nipap',
                'comment': None,
                'country': None,
                'description': 'test',
                'display_prefix': '1.3.3.0/24',
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
                'type': 'reservation',
                'vrf_rt': None,
                'vrf_id': 0,
                'vrf_name': 'default',
                'vlan': None
            }
        expected_prefixes = [
                { 'prefix': '192.168.0.0/16', 'indent': 0, },
                { 'prefix': '192.168.0.0/20', 'indent': 1, },
                { 'prefix': '192.168.0.0/24', 'indent': 2, },
                { 'prefix': '192.168.1.0/24', 'indent': 2, },
                { 'prefix': '192.168.2.0/24', 'indent': 2, },
                { 'prefix': '192.168.32.0/20', 'indent': 1 },
                { 'prefix': '192.168.32.0/24', 'indent': 2 },
                ]
        expected = []
        for p in expected_prefixes:
            pexp = expected_base.copy()
            for key in p:
                pexp[key] = p[key]
            pexp['display_prefix'] = p['prefix']
            expected.append(pexp)

        self.maxDiff = None
        self.assertEqual(expected, self._mangle_prefix_result(s.list_prefix({ 'auth': ad, })))




if __name__ == '__main__':

    # set up logging
    log = logging.getLogger()
    logging.basicConfig()
    log.setLevel(logging.INFO)

    if sys.version_info >= (2,7):
        unittest.main(verbosity=2)
    else:
        unittest.main()
