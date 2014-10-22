#!/usr/bin/env python
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

nipap_bin = '../nipap-cli/nipap'

class NipapCliTest(unittest.TestCase):
    """ Tests the NIPAP CLI

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
                del(p['added'])
                del(p['last_modified'])
                del(p['total_addresses'])
                del(p['used_addresses'])
                del(p['free_addresses'])

        elif isinstance(res, dict):
            # just one single prefix
            self.assertIn('added', p)
            self.assertIn('last_modified', p)
            del(p['added'])
            del(p['last_modified'])
            del(res['total_addresses'])
            del(res['used_addresses'])
            del(res['free_addresses'])

        return res


    def _run_cmd(self, cmd):
        """ Run a command
        """
        import subprocess
        return subprocess.check_output(cmd)


    def test_prefix_add_list(self):
        """ Add a prefix and verify result in database
        """
        ref = {
                'prefix': '1.3.3.0/24',
                'type': 'assignment',
                'status': 'assigned',
                'description': 'foo description',
                'comment': 'comment bar',
                'country': 'AB',
                'alarm_priority': 'high',
                'monitor': 'true',
                'order_id': '123',
                'customer_id': '66'
                }

        cmd = [nipap_bin, 'address', 'add']
        for key in ref:
            cmd.append(key)
            cmd.append(ref[key])

        ref['display_prefix'] = '1.3.3.0/24'
        ref['indent'] = 0
        ref['family'] = 4
        ref['monitor'] = True
        ref['pool_id'] = None
        ref['pool_name'] = None
        ref['vrf_id'] = 0
        ref['vrf_name'] = 'default'
        ref['vrf_rt'] = None
        ref['external_key'] = None
        ref['node'] = None
        ref['authoritative_source'] = 'nipap'
        ref['vlan'] = None
        ref['inherited_tags'] = []
        ref['tags'] = []
        ref['avps'] = {}
        ref['expires'] = None

        self._run_cmd(cmd)

        res = self._mangle_prefix_result(s.list_prefix({ 'auth': ad, 'spec': {} }))
        del(res[0]['id'])

        self.assertEqual(res, [ ref, ])




if __name__ == '__main__':

    # set up logging
    log = logging.getLogger()
    logging.basicConfig()
    log.setLevel(logging.INFO)

    if sys.version_info >= (2,7):
        unittest.main(verbosity=2)
    else:
        unittest.main()
