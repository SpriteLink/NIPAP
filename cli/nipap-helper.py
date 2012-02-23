#! /usr/bin/python

""" CLI command completion helper

    nipap-helper.py is used to provide tab completion capabilities of nipap
    commands to for example bash.
"""

import sys
import os
from command import Command
import nipap
from pynipap import NipapError

if __name__ == '__main__':

    cmd = Command(nipap.cmds, sys.argv[1::])

    comp = []

    try:
        comp = sorted(cmd.complete())
    except NipapError:
        # handle errors silently
        pass

    for val in comp:
        print val
