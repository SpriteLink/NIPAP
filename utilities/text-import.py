#!/usr/bin/python
# vim: et :

import re

import sys
sys.path.append('../nap-www')
from napwww.model.napmodel import Schema, Pool, Prefix, NapNonExistentError, NapDuplicateError

import logging


class CommentLine(Exception):
    pass


class Importer:
    def __init__(self, schema_name):
        self._logger = logging.getLogger(self.__class__.__name__)

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
            except NapDuplicateError:
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
            p.alarm_priority = 'low'
            p.authoritative_source = 'nw'
            p.save({})

        elif tp['prefix_length'] == 32:   # loopback
            print "Loopback:", tp['prefix']
            p = Prefix()
            p.schema = self.schema
            p.prefix = tp['prefix']
            # loopbacks are always of type 'assignment'
            p.type = 'assignment'
            p.node = tp['node']
            p.description = tp['description']
            p.alarm_priority = tp['alarm_priority']
            p.authoritative_source = 'nw'
            p.save({})

        elif tp['prefix_length'] == 30 or tp['prefix_length'] == 31:   # link network
            return



    def split_columns(self, line):

        m = re.match(r'^! (((2(5[0-5]|[0-4][0-9])|[01]?[0-9][0-9]?)\.){3}(2(5[0-5]|[0-4][0-9])|[01]?[0-9][0-9]?)(/(3[12]|[12]?[0-9])))[\t\s]+([^\t]+)$', line)
        if m is not None:
            params = {}
            params['prefix'] = m.group(1)
            params['address'] = m.group(1)
            params['prefix_length'] = int(m.group(8))
            params['description'] = m.group(9).rstrip()
            params['prefix_type'] = 'reservation'
            return params

        # ignore comments, that is lines starting with one of ; # !
        if re.match(r'^$', line) or re.match(' *[;#!]', line):
            raise CommentLine("Comment line")

        params = {}
        params['prefix_type'] = 'assorhost'
        (prefix, priority, country, type, span_order, node, description) = re.split(r'[\t\s]+', line.rstrip(), 6)

        # one of those silly lines for documenting L2 circuits
        if prefix == '.':
            raise TypeError('. is not a valid prefix, line: ' + line)

        # is it a real IP prefix?
        m = re.match('!?(((2(5[0-5]|[0-4][0-9])|[01]?[0-9][0-9]?)\.){3}(2(5[0-5]|[0-4][0-9])|[01]?[0-9][0-9]?)(/(3[12]|[12]?[0-9])))', prefix)
        if m is None:
            raise TypeError("Incorrect prefix on line: " + line)

        params['prefix'] = prefix
        params['address'] = m.group(1)
        params['prefix_length'] = int(m.group(8))

        if priority == 'H':
            params['alarm_priority'] = 'high'
        elif priority == 'M':
            params['alarm_priority'] = 'medium'
        else:
            params['alarm_priority'] = 'low'

        params['country'] = country
        params['node'] = node
        m = re.search(r'([0-9]{4,})', span_order)
        if m is not None:
            params['span_order'] = m.group(1)
        else:
            params['span_order'] = None

        params['description'] = description.decode('latin1')

        params['type'] = type

        return params





if __name__ == '__main__':
    import optparse
    parser = optparse.OptionParser()
    parser.add_option('--schema', help = 'Name of schema to import into')

    options, args = parser.parse_args()

    if options.schema is None:
        print >> sys.stderr, "You must specify a schema"
        sys.exit(1)

    ti = TextImporter(options.schema)
    for filename in args:
        ti.parse_file(filename)




