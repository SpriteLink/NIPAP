#!/usr/bin/python

import unittest

import sys
sys.path.insert(0, '..')
from nipap_cli import nipap_cli
from nipap_cli.command import Command, CommandError, InvalidCommand

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
        """ Should raise an InvalidCommand exception as the command is too long
        """
        self.assertRaises(InvalidCommand, self.cli_test, ('address', 'view', 'FOO', ''))





if __name__ == '__main__':
    unittest.main()
