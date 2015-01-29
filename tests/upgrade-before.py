#!/usr/bin/env python
#
# This is run by Travis-CI before an upgrade to load some data into the
# database. After the upgrade is complete, the data is verified by
# upgrade-after.py to make sure that the upgrade of the database went smoothly.
#

import logging
import unittest
import sys
sys.path.insert(0, '..')
sys.path.insert(0, '../pynipap')
sys.path.insert(0, '../nipap')
sys.path.insert(0, '../nipap-cli')

from nipap.backend import Nipap
from nipap.authlib import SqliteAuth
from nipap.nipapconfig import NipapConfig

from pynipap import AuthOptions, VRF, Pool, Prefix, NipapNonExistentError, NipapDuplicateError, NipapValueError
import pynipap

pynipap.xmlrpc_uri = 'http://unittest:gottatest@127.0.0.1:1337'
o = AuthOptions({
        'authoritative_source': 'nipap'
        })


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


    def add_prefix(self, prefix, type, description, tags=None):
        if tags is None:
            tags = []
        p = Prefix()
        p.prefix = prefix
        p.type = type
        p.description = description
        p.tags = tags
        p.save()
        return p


class TestLoad(unittest.TestCase):
    """ Load some data into the database
    """
    def test_load_data(self):
        """
        """
        th = TestHelper()
        p1 = th.add_prefix('192.168.0.0/16', 'reservation', 'test')
        p2 = th.add_prefix('192.168.0.0/20', 'reservation', 'test')
        p3 = th.add_prefix('192.168.0.0/24', 'reservation', 'test')
        p4 = th.add_prefix('192.168.1.0/24', 'reservation', 'test')
        p5 = th.add_prefix('192.168.2.0/24', 'reservation', 'test')
        p6 = th.add_prefix('192.168.32.0/20', 'reservation', 'test')
        p7 = th.add_prefix('192.168.32.0/24', 'reservation', 'test')
        p8 = th.add_prefix('192.168.32.1/32', 'reservation', 'test')

        ps1 = th.add_prefix('2001:db8:1::/48', 'reservation', 'test')
        ps2 = th.add_prefix('2001:db8:1::/64', 'reservation', 'test')
        ps3 = th.add_prefix('2001:db8:2::/48', 'reservation', 'test')

        pool1 = Pool()
        pool1.name = 'upgrade-test'
        pool1.ipv4_default_prefix_length = 31
        pool1.ipv6_default_prefix_length = 112
        pool1.save()
        p2.pool = pool1
        p2.save()
        ps1.pool = pool1
        ps1.save()

        pool2 = Pool()
        pool2.name = 'upgrade-test2'
        pool2.save()

        vrf1 = VRF()
        vrf1.name = 'foo'
        vrf1.rt = '123:123'
        vrf1.save()



if __name__ == '__main__':

    # set up logging
    log = logging.getLogger()
    logging.basicConfig()
    log.setLevel(logging.INFO)

    if sys.version_info >= (2,7):
        unittest.main(verbosity=2)
    else:
        unittest.main()


