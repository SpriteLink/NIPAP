#!/usr/bin/python

import re
import sys


class Importer:
    def __init__:
        # import nap class and stuff



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
            self.parse_line(line)
        f.close()



    def parse_line(self, line):
        """ Parse one line
        """

        # ignore comments, that is lines starting with one of ; # !
        if re.match(r'^$', line) or re.match(' *[;#!]', line):
            continue

        params = self.split_columns(line)



    def split_columns(self, line):

        params = {}
        (prefix, priority, country, type, span_order, node, description) = re.split(r'[\t\s]+', line.rstrip(), 6)

        # one of those silly lines for documenting L2 circuits
        if prefix == '.':
            continue
        # is it a real IP prefix?
        m = re.match('(((2(5[0-5]|[0-4][0-9])|[01]?[0-9][0-9]?)\.){3}(2(5[0-5]|[0-4][0-9])|[01]?[0-9][0-9]?)(/(3[12]|[12]?[0-9])))', prefix)
        if m is None:
            print >> sys.stderr, "Incorrect prefix on line:", line
            continue

        prefix_len = m.group(8)

        # -----------------

        params['prefix'] = prefix

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

        if prefix_len == '32':
            params['type'] = 'host'
        elif prefix_len > '26':
            params['type'] = 'assignment'
        else:
            params['type'] = 'reservation'

        params['authoritative_source'] = 'nw'





if __name__ == '__main__':
    import optparse
    parser = optparse.OptionParser()
    options, args = parser.parse_args()

    ti = TextImporter()
    for filename in args:
        ti.parse_file(filename)




