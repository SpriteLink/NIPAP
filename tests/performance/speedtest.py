#!/usr/bin/env python
# vim: et :

import logging
import re
import sys
import time

sys.path.append('../../nipap/')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

log_format = "%(levelname)-8s %(message)s"
log_stream = logging.StreamHandler()
log_stream.setFormatter(logging.Formatter("%(asctime)s: " + log_format))
log_stream.setLevel(logging.WARNING)
logger.addHandler(log_stream)


import nipap.backend

class bonk:
    def __init__(self):
        self.n = nipap.backend.Nipap()

        #self.n.remove_prefix({ 'name': 'test-schema' }, { 'prefix': '2.0.0.0/8' })
        #self.n.add_prefix({'name': 'test-schema' }, { 'prefix': '2.0.0.0/8', 'description': 'test' })



    def clear_db(self):
        """ Clear out everything in the database
        """
        self.n._execute("TRUNCATE ip_net_plan CASCADE")



    def init_db(self):
        """ Initialise a few things we need in the db, a schema, a pool, a truck
        """

    def find_prefix(self, argp):
        """
        """
        arg_prefix = argp.split("/")[0]
        arg_pl = argp.split("/")[1]
        if self.n._is_ipv4(arg_prefix):
            m = re.match("([0-9]+)\.([0-9]+)\.([0-9]+)\.([0-9]+)", arg_prefix)
            os1 = int(m.group(1))
            os2 = int(m.group(2))
            os3 = int(m.group(3))
            os4 = int(m.group(4))
            count = 2**(32-int(arg_pl))
            i = 0
            t0 = time.time()
            try:
                for o1 in xrange(os1, 255):
                    for o2 in xrange(os2, 255):
                        for o3 in xrange(os3, 255):
                            t2 = time.time()
                            for o4 in xrange(os4, 255):
                                prefix = "%s.%s.%s.%s" % (o1, o2, o3, o4)
                                self.n.list_prefix({ 'name': 'test-schema'}, { 'prefix': prefix })
                                i += 1
                                if i >= count:
                                    raise StopIteration()
                            t3 = time.time()
                            print o3, (t3-t2)/256
            except StopIteration:
                pass
            t1 = time.time()
            print count, "prefixes found in:", t1-t0


        elif self.n._is_ipv6(argp):
            print >> sys.stderr, "IPv6 is currently unsupported"



    def fill_prefix(self, argp):
        """ Fill the specified prefix with hosts (/32s or /128s for IPv[46])
        """
        arg_prefix = argp.split("/")[0]
        arg_pl = argp.split("/")[1]
        netcount = 0
        if self.n._is_ipv4(arg_prefix):
            m = re.match("([0-9]+)\.([0-9]+)\.([0-9]+)\.([0-9]+)", arg_prefix)
            os1 = int(m.group(1))
            os2 = int(m.group(2))
            os3 = int(m.group(3))
            os4 = int(m.group(4))
            count = 2**(32-int(arg_pl))
            i = 0
            t0 = time.time()
            try:
                for o1 in xrange(os1, 255):
                    for o2 in xrange(os2, 255):
                        for o3 in xrange(os3, 255):
                            t2 = time.time()
                            for o4 in xrange(os4, 255):
                                prefix = "%s.%s.%s.%s" % (o1, o2, o3, o4)
                                self.n.add_prefix({'name': 'test-schema' }, { 'prefix': prefix, 'description': 'test' })
                                i += 1
                                if i >= count:
                                    raise StopIteration()
                            t3 = time.time()
                            print netcount, (t3-t2)/256
                            netcount += 1
            except StopIteration:
                pass
            t1 = time.time()
            print count, "prefixes added in:", t1-t0


        elif self.n._is_ipv6(argp):
            print >> sys.stderr, "IPv6 is currently unsupported"


    def find_free_prefix(self, argp):
        t0 = time.time()
        prefix = self.n.find_free_prefix({ 'name': 'test-schema' }, { 'from-prefix': [argp], 'prefix_length': 32 })
        t1 = time.time()
        d1 = t1-t0
        print "First free prefix:", prefix, "found in", d1, "seconds"



    def add_prefix(self, argp):
        t0 = time.time()
        prefix = self.n.add_prefix({ 'name': 'test-schema' }, { 'prefix': argp, 'description': 'test' })
        t1 = time.time()
        d1 = t1-t0
        print "Add prefix:", argp, "took", d1, "seconds"



    def remove_prefix(self, argp):
        t0 = time.time()
        prefix = self.n.remove_prefix({ 'name': 'test-schema' }, { 'prefix': argp })
        t1 = time.time()
        d1 = t1-t0
        print "Delete prefix:", argp, "took", d1, "seconds"




    def prefix_insert(self, argp):
        pass


    def test1(self):
        t0 = time.time()
        res = self.n.find_free_prefix({ 'schema_name': 'test-schema', 'from-prefix': ['1.0.0.0/8'] }, 32, 1)
        t1 = time.time()
        res = self.n.find_free_prefix({ 'schema_name': 'test-schema', 'from-prefix': ['1.0.0.0/8'] }, 32, 500)
        t2 = time.time()
        for prefix in res:
            self.n.add_prefix({ 'schema_name': 'test-schema', 'prefix': prefix, 'description': 'test' })
        t3 = time.time()
        res = self.n.find_free_prefix({ 'schema_name': 'test-schema', 'from-prefix': ['1.0.0.0/8'] }, 32, 1)
        t4 = time.time()
        d1 = t1-t0
        d2 = t2-t1
        d3 = t3-t2
        d4 = t4-t3
        d5 = d4-d1
        print "First find free prefix:", d1
        print "First find of 500 prefixes:", d2
        print "Adding 500 prefixes", d3
        print "Find one prefix after", d4
        print "Diff", d5

    def test2(self):
        t0 = time.time()
        res = self.n.find_free_prefix({ 'schema_name': 'test-schema', 'from-prefix': ['2.0.0.0/8'] }, 32, 1)
        t1 = time.time()
        d1 = t1-t0
        print "Find free prefix:", d1

    def test3(self):
        self.n.find_free_prefix({ 'schema_name': 'test-schema', 'from-prefix': ['2.0.0.0/8'] }, 32, 1)



if __name__ == '__main__':
    import optparse
    parser = optparse.OptionParser()
    parser.add_option('--add-prefix', metavar = 'PREFIX', help='Add PREFIX')
    parser.add_option('--fill-prefix', metavar = 'PREFIX', help='fill PREFIX with hosts')
    parser.add_option('--find-free-prefix', metavar = 'PREFIX', help='try to find the next free /32 in PREFIX')
    parser.add_option('--remove-prefix', metavar = 'PREFIX', help='delete PREFIX')
    b = bonk()

    options, args = parser.parse_args()

    if options.fill_prefix is not None:
        if not b.n._get_afi(options.fill_prefix):
            print >> sys.stderr, "Please enter a valid prefix"
            sys.exit(1)
        b.fill_prefix(options.fill_prefix)


    if options.find_free_prefix is not None:
        b.find_free_prefix(options.find_free_prefix)

    if options.add_prefix is not None:
        b.add_prefix(options.add_prefix)

    if options.remove_prefix is not None:
        b.remove_prefix(options.remove_prefix)
