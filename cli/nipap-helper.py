#! /usr/bin/python

import sys
import os
from command import Command
import nipap

if __name__ == '__main__':

    cmd = Command(nipap.cmds, sys.argv[1::])

    if cmd.key_complete == True:
        print "key complete"
        print ' '.join(sorted(cmd.next_values()))
    else:
        print "key not complete"
        print ' '.join(sorted(cmd.complete()))

