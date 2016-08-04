#!/usr/bin/env python
# vim: et :

import re

import sys
sys.path.append('../pynipap/')
import pynipap
from pynipap import AuthOptions, Schema, Pool, Prefix, NipapNonExistentError, NipapDuplicateError, NipapValueError

import logging

pynipap.xmlrpc_uri = 'http://web_ui@local:PngeOJctzUyM@127.0.0.1:1337'

o = AuthOptions({
    'authoritative_source': 'nipap'
})


class CommentLine(Exception):
    pass


class Importer:
    def __init__(self, url, schema_name):
        self._logger = logging.getLogger(self.__class__.__name__)

        import pynipap
        pynipap.xmlrpc_uri = url

        # import nap class and stuff
        sl = Schema.list({ 'name': schema_name })
        try:
            sl = Schema.list({ 'name': schema_name })
        except:
            # TODO: handle this?
            pass

        if len(sl) == 0:
            raise Exception("Non-existant schema specified: " + schema_name)

        s = sl[0]

        self.schema = Schema.get(int(s.id))



class TextImporter(Importer):
    """ A text importer

        This one is made for a tab-separated file format where there are seven
        columns with different information.

        A line would typically look like this:
        10.0.0.0/8  H   DE  CORE    123456  MY-CORE-ROUTER  This is a test prefix

        Where the first column is a prefix, then the priority (High in this
        case), the country code where it's at, what "type" it is (not the same
        type as in NIPAP), the order number, hostname of the router and last a
        free format description

        A link network is typically documented as follows:
        10.0.1.0/30 H   DE  CORE    .       CORE-1          CORE-1 <-> CORE-2

        And so the first address in 10.0.1.0/30 is assigned to the router CORE-1
        while the second address (10.0.1.2) is assigned to CORE-2. We try to
        make some clever parsing to determine what is link addresses and so
        forth.
    """


    def parse_file(self, filename):
        f = open(filename)
        for line in f.readlines():
            try:
                params = self.parse_line(line)
            except NipapDuplicateError:
                pass
            except TypeError:
                pass
            except ValueError:
                pass


        f.close()



    def parse_line(self, line):
        """ Parse one line
        """

        try:
            # text params, ie params from the text file
            tp = self.split_columns(line)
        except CommentLine:
            # just ignore comments
            return

        if tp['prefix_type'] == 'reservation':  # reservations / aggregates
            print "Reservation:", tp['prefix'], tp['description']
            p = Prefix()
            p.schema = self.schema
            p.prefix = tp['prefix']
            p.type = 'reservation'
            p.description = tp['description']
            p.monitor = True
            p.alarm_priority = 'low'
            p.authoritative_source = 'nw'
            p.save({})
            return

        elif tp['node'] == '.' and tp['description'] == '.':
            # ignore prefixes without description or node set
            return

        elif tp['prefix_length'] == 32:   # loopback
            # if it's a loopback, the covering prefix will be a reservation and we can just insert an assignment.
            # if this insert fails, it means the parent prefix is an assignment and we instead insert a host
            try:
                p = Prefix()
                p.schema = self.schema
                p.prefix = tp['prefix']
                # loopbacks are always of type 'assignment'
                p.type = 'assignment'
                p.node = tp['node']
                p.description = tp['description']
                p.monitor = True
                p.alarm_priority = tp['alarm_priority']
                p.authoritative_source = 'nw'
                p.save({})
                print "Loopback:", tp['prefix']
                return
            except:
                p = Prefix()
                p.schema = self.schema
                p.prefix = tp['prefix']
                # loopbacks are always of type 'assignment'
                p.type = 'host'
                p.node = tp['node']
                p.description = tp['description']
                p.monitor = True
                p.alarm_priority = tp['alarm_priority']
                p.authoritative_source = 'nw'
                p.save({})
                print "Host:", tp['prefix']
                return

        elif tp['prefix_length'] == 30 or tp['prefix_length'] == 31:   # link network
            octets = tp['address'].split('.')
            prefix_node1 = None
            prefix_node2 = None
            if tp['prefix_length'] == 30:
                prefix_node1 = '.'.join(octets[:3] + [str( int(octets[3]) + 1 )] ) + '/32'
                prefix_node2 = '.'.join(octets[:3] + [str( int(octets[3]) + 2 )] ) + '/32'
            else:
                prefix_node1 = '.'.join(octets) + '/32'
                prefix_node2 = '.'.join(octets[:3] + [str( int(octets[3]) + 1 )] ) + '/32'

            #m = re.match('(ETHER_KAP|ETHER_PORT|IP-KAP|IP-PORT|IP-SIPNET|IP-SNIX|IPSUR|L2L|RED-IPPORT|SNIX|SWIP|T2V-@|T2V-DIGTV|T2V-SUR)[0-9]{4,}', tp['order_id'])
            m = re.match('.*[0-9]{6}$', tp['order_id'])
            if m is not None or tp['type'] == 'CUSTOMER':
                print "Customer link", tp['prefix'], ':', tp['description']
                p = Prefix()
                p.schema = self.schema
                p.prefix = tp['prefix']
                p.type = 'assignment'
                p.description = tp['description']
                p.alarm_priority = tp['alarm_priority']
                p.authoritative_source = 'nw'
                if tp['order_id'] != '.':
                    p.order_id = tp['order_id']
                p.save({})

                # insert node1 and node2
                p1 = Prefix()
                p1.schema = self.schema
                p1.prefix = prefix_node1
                p1.type = 'host'
                p1.description = 'Some PE router'
                p1.authoritative_source = 'nw'
                p1.save({})

                p2 = Prefix()
                p2.schema = self.schema
                p2.prefix = prefix_node2
                p2.type = 'host'
                p2.node = tp['node']
                p2.description = 'CPE'
                p2.authoritative_source = 'nw'
                p2.save({})

                return


            m = re.match(r'([^\s]+)\s*<->\s*([^\s]+)', tp['description'])
            if m is not None:
                node1 = m.group(1)
                node2 = m.group(2)
                print "Link network: ", tp['prefix'], "  ", node1, "<->", node2

                p = Prefix()
                p.schema = self.schema
                p.prefix = tp['prefix']
                p.type = 'assignment'
                p.description = node1 + ' <-> ' + node2
                p.monitor = True
                p.alarm_priority = tp['alarm_priority']
                p.authoritative_source = 'nw'
                p.save({})

                # insert node1 and node2
                p1 = Prefix()
                p1.schema = self.schema
                p1.prefix = prefix_node1
                p1.type = 'host'
                p1.node = node1
                p1.description = node1
                p1.authoritative_source = 'nw'
                p1.save({})

                p2 = Prefix()
                p2.schema = self.schema
                p2.prefix = prefix_node2
                p2.type = 'host'
                p2.node = node2
                p2.description = node2
                p2.authoritative_source = 'nw'
                p2.save({})

                return

            m = re.match('(DN)[0-9]{4,}', tp['order_id'])
            if m is not None:
                print "Internal order link network", tp['prefix'], ':', tp['description']
                p = Prefix()
                p.schema = self.schema
                p.prefix = tp['prefix']
                p.type = 'assignment'
                p.description = tp['description']
                p.monitor = True
                p.alarm_priority = tp['alarm_priority']
                p.authoritative_source = 'nw'
                p.save({})
                return

            print "Other link network", tp['prefix'], ':', tp['description']
            p = Prefix()
            p.schema = self.schema
            p.prefix = tp['prefix']
            p.type = 'assignment'
            p.description = tp['description']
            p.monitor = True
            p.alarm_priority = tp['alarm_priority']
            p.authoritative_source = 'nw'
            p.save({})
            return

        else:
            try:
                p = Prefix()
                p.schema = self.schema
                p.prefix = tp['prefix']
                p.type = 'assignment'
                p.description = tp['description']
                p.monitor = True
                p.alarm_priority = 'low'
                p.authoritative_source = 'nw'
                p.save({})
                print "Other:", tp['prefix']
            except NipapValueError, e:
                print tp['prefix'], ':', e
                sys.exit(1)

            return



    def split_columns(self, line):

        m = re.match(r'^! (((2(5[0-5]|[0-4][0-9])|[01]?[0-9][0-9]?)\.){3}(2(5[0-5]|[0-4][0-9])|[01]?[0-9][0-9]?)(/(3[12]|[12]?[0-9])))[\t\s]+([^\t]+)$', line)
        if m is not None:
            params = {}
            params['prefix'] = m.group(1)
            params['address'] = m.group(2)
            params['prefix_length'] = int(m.group(8))
            params['description'] = m.group(9).rstrip()
            params['prefix_type'] = 'reservation'
            return params

        # ignore comments, that is lines starting with one of ; # !
        if re.match(r'^$', line) or re.match(' *[;#!]', line):
            raise CommentLine("Comment line")

        params = {}
        params['prefix_type'] = 'assorhost'
        (prefix, priority, country, type, order_id, node, description) = re.split(r'[\t\s]+', line.rstrip(), 6)

        # one of those silly lines for documenting L2 circuits
        if prefix == '.':
            raise TypeError('. is not a valid prefix, line: ' + line)

        # is it a real IP prefix?
        m = re.match('!?((((2(5[0-5]|[0-4][0-9])|[01]?[0-9][0-9]?)\.){3}(2(5[0-5]|[0-4][0-9])|[01]?[0-9][0-9]?))(/(3[012]|[12]?[0-9])))', prefix)
        if m is None:
            raise TypeError("Incorrect prefix on line: " + line)

        params['prefix'] = prefix
        params['address'] = m.group(2)
        params['prefix_length'] = int(m.group(9))

        if priority == 'H':
            params['alarm_priority'] = 'high'
        elif priority == 'M':
            params['alarm_priority'] = 'medium'
        else:
            params['alarm_priority'] = 'low'

        params['country'] = country
        params['node'] = node
        #m = re.search(r'([0-9]{4,})', order_id)
        #if m is not None:
        #    params['order_id'] = m.group(1)
        #else:
        #    params['order_id'] = None
        params['order_id'] = order_id

        params['description'] = description.decode('latin1')
        params['description'] = description

        params['type'] = type

        return params





if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--schema', help = 'Name of schema to import into')
    parser.add_argument('--url', default='http://127.0.0.1:1337/', help = 'the NIPAP XML-RPC server url')

    args = parser.parse_args()

    if args.schema is None:
        print >> sys.stderr, "You must specify a schema"
        sys.exit(1)

    ti = TextImporter(args.url, args.schema)
    for filename in args:
        ti.parse_file(filename)




