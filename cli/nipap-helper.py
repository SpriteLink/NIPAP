#! /usr/bin/python

import sys
import os
from command import Command
import nipap

if __name__ == '__main__':

    cmd = Command(nipap.cmds, sys.argv[1::])

    comp = sorted(cmd.complete())

    for val in comp:
        print val
