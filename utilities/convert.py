#! /usr/bin/env python
#
# Converts schema-based NIPAP database to VRF-based.
#
# To work, it needs the NIPAP database containing the old data in the database
# nipap_old, readable by the user set in nipap.conf
#

import re
import gc
import sys
import time
import psycopg2
import psycopg2.extras

from nipap.nipapconfig import NipapConfig
import pynipap
from pynipap import VRF, Pool, Prefix, NipapError

nipap_cfg_path = "/etc/nipap/nipap.conf"
nipapd_xmlrpc_uri = "http://dev:dev@127.0.0.1:1337"


sql_log = """INSERT INTO ip_net_log
(
    vrf_id,
    vrf_rt,
    vrf_name,
    prefix_prefix,
    prefix_id,
    pool_name,
    pool_id,
    timestamp,
    username,
    authenticated_as,
    authoritative_source,
    full_name,
    description
) VALUES
(
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
)"""


class Inet(object):
    """ This works around a bug in psycopg2 version somewhere before 2.4.  The
        __init__ function in the original class is broken and so this is merely
        a copy with the bug fixed.

        Wrap a string to allow for correct SQL-quoting of inet values.

        Note that this adapter does NOT check the passed value to make sure it
        really is an inet-compatible address but DOES call adapt() on it to make
        sure it is impossible to execute an SQL-injection by passing an evil
        value to the initializer.
    """
    def __init__(self, addr):
        self.addr = addr

    def prepare(self, conn):
        self._conn = conn

    def getquoted(self):
        obj = adapt(self.addr)
        if hasattr(obj, 'prepare'):
            obj.prepare(self._conn)
        return obj.getquoted()+"::inet"

    def __str__(self):
        return str(self.addr)
         
def _register_inet(oid=None, conn_or_curs=None):
    """Create the INET type and an Inet adapter."""
    from psycopg2 import extensions as _ext
    if not oid: oid = 869
    _ext.INET = _ext.new_type((oid, ), "INET",
            lambda data, cursor: data and Inet(data) or None)
    _ext.register_type(_ext.INET, conn_or_curs)
    return _ext.INET



if __name__ == '__main__':

    # connect to old database
    # Get database configuration
    cfg = NipapConfig(nipap_cfg_path)
    db_args = {}
    db_args['host'] = cfg.get('nipapd', 'db_host')
    db_args['database'] = 'nipap_old'
    db_args['user'] = cfg.get('nipapd', 'db_user')
    db_args['password'] = cfg.get('nipapd', 'db_pass')
    db_args['sslmode'] = cfg.get('nipapd', 'db_sslmode')
    # delete keys that are None, for example if we want to connect over a
    # UNIX socket, the 'host' argument should not be passed into the DSN
    if db_args['host'] is not None and db_args['host'] == '':
        db_args['host'] = None
    for key in db_args.copy():
        if db_args[key] is None:
            del(db_args[key])

    # Create database connection to old db
    con_pg_old = None
    curs_pg_old = None
    curs_pg_old2 = None
    try:
        con_pg_old = psycopg2.connect(**db_args)
        con_pg_old.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        curs_pg_old = con_pg_old.cursor(cursor_factory=psycopg2.extras.DictCursor)
        curs_pg_old2 = con_pg_old.cursor(cursor_factory=psycopg2.extras.DictCursor)
    except Exception, e:
        print 'pgsql: %s' % e
        sys.exit(1)

    _register_inet(conn_or_curs = con_pg_old)

    # Create database connection to new db
    db_args['database'] = cfg.get('nipapd', 'db_name')
    con_pg_new = None
    curs_pg_new = None
    curs_pg_new2 = None
    try:
        con_pg_new = psycopg2.connect(**db_args)
        con_pg_new.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        curs_pg_new = con_pg_new.cursor(cursor_factory=psycopg2.extras.DictCursor)
        curs_pg_new2 = con_pg_new.cursor(cursor_factory=psycopg2.extras.DictCursor)
    except Exception, e:
        print 'pgsql: %s' % e
        sys.exit(1)

    _register_inet(conn_or_curs = con_pg_new)

    # set up pynipap
    aopts = pynipap.AuthOptions({ 'authoritative_source': 'nipap' })
    pynipap.xmlrpc_uri = nipapd_xmlrpc_uri


    #
    # Create pools
    #
    print "Creating pools... ",
    sql = "SELECT * FROM ip_net_pool"
    curs_pg_old.execute(sql)
    pools = {}
    for r in curs_pg_old:
        p = Pool()
        p.name = r['name']
        p.description = r['description']
        p.default_type = r['default_type']
        p.ipv4_default_prefix_length = r['ipv4_default_prefix_length']
        p.ipv6_default_prefix_length = r['ipv6_default_prefix_length']
        try:
            p.save()
        except NipapError, e:
            print "ERR: %s" % str(e)
        pools[r['id']] = p

        # remove new audit log entries
        sql = "DELETE FROM ip_net_log WHERE pool_id = %s"
        curs_pg_new.execute(sql, ( p.id, ))

        # fetch old audit log entries
        sql = "SELECT * FROM ip_net_log WHERE pool = %s AND prefix IS NULL"
        curs_pg_old2.execute(sql, ( r['id'], ))
        for ar in curs_pg_old2:
            curs_pg_new.execute(sql_log, (None, None, None, None, None, p.name, p.id, ar['timestamp'], ar['username'], ar['authenticated_as'], ar['authoritative_source'], ar['full_name'], ar['description']))

    print "done"

    # Create VRFs from Schemas
    print "Creating VRFs from Schemas... ",
    sql = "SELECT * FROM ip_net_schema"
    curs_pg_old.execute(sql)
    vrfs = {}
    s_vrfs = {}
    for r in curs_pg_old:
        if r['vrf'] is None:
            continue

        if re.match('\d+:\d+', r['vrf'].strip()):
            v = VRF()
            v.rt = r['vrf'].strip()
            v.name = r['name'].strip()
            try:
                v.save()
            except NipapError, e:
                print "ERR: %s" % str(e)
            vrfs[v.rt] = v
            s_vrfs[r['id']] = v
    print "done"


    # Create VRFs from prefixes
    print "Creating VRFs from Prefixes... ",
    sql = "SELECT DISTINCT(vrf) FROM ip_net_plan WHERE vrf IS NOT NULL"
    curs_pg_old.execute(sql)
    for r in curs_pg_old:
        if re.match('^\d+:\d+$', r['vrf'].strip()):

            print "Found VRF %s" % r['vrf']
            
            # skip if VRF already added
            if r['vrf'].strip() in vrfs:
                continue

            v = VRF()
            v.rt = r['vrf'].strip()
            v.name = r['vrf'].strip()
            try:
                v.save()
            except NipapError, e:
                print "ERR: %s" % str(e)
            vrfs[v.rt] = v

        elif re.match('^\d+$', r['vrf'].strip()):

            print "Found VRF %s" % r['vrf']

            # skip if VRF already added
            if '1257:' + r['vrf'].strip() in vrfs:
                if r['vrf'].strip() not in vrfs:
                    vrfs[r['vrf'].strip()] = vrfs['1257:' + r['vrf'].strip()]
                continue

            v = VRF()
            v.rt = '1257:' + r['vrf'].strip()
            v.name = '1257:' + r['vrf'].strip()
            try:
                v.save()
            except NipapError, e:
                print "ERR: %s" % str(e)
            vrfs[v.rt] = v
            vrfs[r['vrf'].strip()] = v

        else:
            print "Found invalid VRF %s" % str(r['vrf'])

    print "done"


    # Create prefixes
    print "Creating prefixes... "
    sql = "SELECT * FROM ip_net_plan order by schema, prefix"
    curs_pg_old.execute(sql)
    i = 0
    t = time.time()
    for r in curs_pg_old:
        p = Prefix()

        # find VRF
        if r['vrf'] is not None:
            p.vrf = vrfs[r['vrf'].strip()]
        elif r['schema'] in s_vrfs:
            p.vrf = s_vrfs[r['schema']]
        
        # the rest of the prefix attributes...
        p.prefix = r['prefix']
        p.description = r['description']
        p.comment = r['comment']
        p.node = r['node']
        if r['pool'] is not None:
            p.pool = pools[r['pool']]
        p.type = r['type']
        p.country = r['country']
        p.order_id = r['order_id']
        p.customer_id = r['customer_id']
        p.external_key = r['external_key']
        p.alarm_priority = r['alarm_priority']
        p.monitor = r['monitor']

        try:
            p.save()
        except NipapError, e:
            print "ERR: %s" % str(e),
            print "Prefix: pref: %s old_id: %d" % (p.prefix, r['id'])

        i += 1
        if i % 500 == 0:
            print "%.1f pps" % (500/(time.time() - t))
            t = time.time()

        # update audit log

        # remove new entries
        sql = "DELETE FROM ip_net_log WHERE prefix_id = %s"
        curs_pg_new.execute(sql, ( p.id, ))

        # fetch old entries
        sql = "SELECT * FROM ip_net_log WHERE prefix = %s"
        curs_pg_old2.execute(sql, ( r['id'], ))
        for ar in curs_pg_old2:

            # figure out pool stuff
            pool_name = None
            pool_id = None

            if ar['pool'] is not None:
                if ar['pool'] in pools:
                    pool_name = pools[r['pool']].name
                    pool_id = pools[r['pool']].id
                else:
                    print "Pool %s not found" % str(ar['pool'])
 
            # figure out VRF stuff
            vrf_id = 0
            vrf_rt = None
            vrf_name = None

            if p.vrf is not None:
                vrf_id = p.vrf.id
                vrf_rt = p.vrf.rt
                vrf_name = p.vrf.name

            params = (
                vrf_id,
                vrf_rt,
                vrf_name,
                ar['prefix_prefix'],
                p.id,
                pool_name,
                pool_id,
                ar['timestamp'],
                ar['username'],
                ar['authenticated_as'],
                ar['authoritative_source'],
                ar['full_name'],
                ar['description']
            )
            curs_pg_new.execute(sql_log, params)

        con_pg_new.commit()

    print "done"
