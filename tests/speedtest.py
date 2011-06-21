#!/usr/bin/python

# speedtest of find_free_prefix()

import time

import sys
import logging

sys.path.append('../napd/')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

log_format = "%(levelname)-8s %(message)s"
log_stream = logging.StreamHandler()
log_stream.setFormatter(logging.Formatter("%(asctime)s: " + log_format))
log_stream.setLevel(logging.WARNING)
logger.addHandler(log_stream)


import nap

class bonk:
    def __init__(self):
        self.n = nap.Nap()

        #self.n.remove_prefix({ 'name': 'test-schema' }, { 'prefix': '2.0.0.0/8' })
        #self.n.add_prefix({'name': 'test-schema' }, { 'authoritative_source': 'nap', 'prefix': '2.0.0.0/8', 'description': 'test' })



    def clear_db(self):
        """ Clear out everything in the database
        """
        self.nap._execute("TRUNCATE ip_net_plan CASCADE")



    def init_db(self):
        """ Initialise a few things we need in the db, a schema, a pool, a truck
        """



    def prefix_insert(self, argp):
        """ Insert a /16 into the DB
        """
        t0 = time.time()
        for i in xrange(0, 255):
            t2 = time.time()
            for j in xrange(0, 255):
                prefix = argp + str(i) + "." + str(j)
                self.n.add_prefix({'name': 'test-schema' }, { 'authoritative_source': 'nap', 'prefix': prefix, 'description': 'test' })
            t3 = time.time()
            print i, (t3-t2)/256
        t1 = time.time()
        print "One /16 inserted in:", t1-t0



    def test1(self):

        t0 = time.time()
        res = self.n.find_free_prefix({ 'schema_name': 'test-schema', 'from-prefix': ['1.0.0.0/8'] }, 32, 1)
        t1 = time.time()
        res = self.n.find_free_prefix({ 'schema_name': 'test-schema', 'from-prefix': ['1.0.0.0/8'] }, 32, 500)
        t2 = time.time()
        for prefix in res:
            self.n.add_prefix({ 'authoritative_source': 'nap', 'schema_name': 'test-schema', 'prefix': prefix, 'description': 'test' })
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
    parser.add_option('--prefix-insert', help='insert prefixes!')
    b = bonk()

    options, args = parser.parse_args()

    if options.prefix_insert is not None:
        b.prefix_insert(options.prefix_insert)


