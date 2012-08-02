#!/usr/bin/python

import unittest

import sys
sys.path.append('../')
from nipap_cli import nipap_cli
from nipap_cli.command import Command

class CliCheck(unittest.TestCase):
    def cli_test(self, command):
        """
        """
        cmd = Command(nipap_cli.cmds, command)
        comp = cmd.complete()

        return cmd.exe, cmd.arg, cmd.exe_options, comp



    def test_basic(self):
        """ Run some basic tests
        """

        # top level completion of possible command branches
        self.assertEqual(self.cli_test(('',)),
                (None, None, {},
                    ['address', 'pool', 'schema']
                )
            )



    def test_cmd_stop(self):
        """ should not return anything as we should already have found the command (view) and have an argument to it
        """
        self.assertEqual(self.cli_test(('address', 'view', 'FOO', '',)),
                (nipap_cli.view_prefix, 'FOO', {},
                    []
                )
            )





if __name__ == '__main__':
    unittest.main()
