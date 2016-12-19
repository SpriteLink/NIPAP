#!/usr/bin/env python
""" NIPAP Audit searcher
    ====================
    This is a quick and dirty script to search the audit log db
    for specific IP addresses and subnets, and in that way, get the audit trail
    for it.
"""

import psycopg2
import psycopg2.extras
import re
import IPy
import nipap
import ConfigParser
import datetime
import sys

class AuditLog:

    _con_pg = None
    _curs_pg = None

    def __init__(self):
        self._cfg = ConfigParser.ConfigParser()
        self._cfg.read("/etc/nipap/nipap.conf")
        self._connect_db()


    def _is_ipv4(self, ip):
        """ Return true if given arg is a valid IPv4 address
        """
        try:
            p = IPy.IP(ip)
        except ValueError:
            return False

        if p.version() == 4:
            return True
        return False



    def _is_ipv6(self, ip):
        """ Return true if given arg is a valid IPv6 address
        """
        try:
            p = IPy.IP(ip)
        except ValueError:
            return False

        if p.version() == 6:
            return True
        return False



    def _get_afi(self, ip):
        """ Return address-family (4 or 6) for IP or None if invalid address
        """

        parts = unicode(ip).split("/")
        if len(parts) == 1:
            # just an address
            if self._is_ipv4(ip):
                return 4
            elif self._is_ipv6(ip):
                return 6
            else:
                return None
        elif len(parts) == 2:
            # a prefix!
            try:
                pl = int(parts[1])
            except ValueError:
                # if casting parts[1] to int failes, this is not a prefix..
                return None

            if self._is_ipv4(parts[0]):
                if pl >= 0 and pl <= 32:
                    # prefix mask must be between 0 and 32
                    return 4
                # otherwise error
                return None
            elif self._is_ipv6(parts[0]):
                if pl >= 0 and pl <= 128:
                    # prefix mask must be between 0 and 128
                    return 6
                # otherwise error
                return None
            else:
                return None
        else:
            # more than two parts.. this is neither an address or a prefix
            return None



    def _connect_db(self):
        # Open the database

        db_args = {}
        db_args['host'] = self._cfg.get('nipapd', 'db_host')
        db_args['database'] = self._cfg.get('nipapd', 'db_name')
        db_args['user'] = self._cfg.get('nipapd', 'db_user')
        db_args['password'] = self._cfg.get('nipapd', 'db_pass')
        db_args['sslmode'] = self._cfg.get('nipapd', 'db_sslmode')
        db_args['port'] = self._cfg.get('nipapd', 'db_port')
        if db_args['host'] is not None and db_args['host'] == '':
            db_args['host'] = None
        for key in db_args.copy():
            if db_args[key] is None:
                del(db_args[key])

        while True:
            try:
                self._con_pg = psycopg2.connect(**db_args)
                self._curs_pg = self._con_pg.cursor(cursor_factory=psycopg2.extras.DictCursor)
                self._register_inet()
                psycopg2.extras.register_hstore(self._con_pg, globally=True, unicode=True)
            except psycopg2.Error as exc:
                raise "Error"
            except psycopg2.Warning as warn:
                raise "Warning: %s" % warn

            break


    def _register_inet(self, oid=None, conn_or_curs=None):
        """ Create the INET type and an Inet adapter."""
        from psycopg2 import extensions as _ext
        if not oid:
            oid = 869
        _ext.INET = _ext.new_type((oid, ), "INET",
                lambda data, cursor: data and Inet(data) or None)
        _ext.register_type(_ext.INET, self._con_pg)
        return _ext.INET


    def _format_log_prefix(self, data):
        if type(data) is not dict:
            print("Not a dict")
            raise
        output = "{:<15} {}\n".format("Log id", data['id'])
        output += "{:<15} {}\n".format("Author:", data['username'])
        output += "{:<15} {}\n".format("Date:", data['timestamp'].strftime('%c'))
        if re.search(".*attr:.*", data['description']):
            res = re.match(r'(.*\d\b).*attr: (\{.*\})', data['description'])
            description = res.group(1)
            dataset = res.group(2)
            output += "{:<15} {}\n".format("Description:", description)
            parsed = eval(dataset)
            output += "New data:\n"
            for k,v in parsed.items():
                output += "{:<16}{:<20}: {:<32}\n".format("",k, v)
        else:
            output += "{:<15} {}\n".format("Description:", data['description'])
        return output


    def search_log_prefix(self, prefix):
        if self._get_afi(prefix) is None:
            raise ValueError("Invalid Prefix")

        sql = "SELECT * FROM ip_net_log"

        sql += " WHERE prefix_prefix <<= %s"
        data = (prefix,)

        self._curs_pg.execute(sql, data)
        res = list()
        for row in self._curs_pg:
            res.append(dict(row))

        output = "Audit log for prefix {}\n".format(prefix)
        for entry in res:
            output += self._format_log_prefix(entry)
            output += "\n"

        return output



a = AuditLog()

if len(sys.argv) == 1:
    print "Use with prefix to search in audit log"
    sys.exit()

prefix = sys.argv[1]
print(a.search_log_prefix(prefix))
