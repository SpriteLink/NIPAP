#!/usr/bin/env python
#
# Unit tests for the NIPAP CLI parser
#

import unittest
import string

import sys
sys.path.insert(0, '..')
from nipap_cli import nipap_cli
from nipap_cli.command import Command, CommandError, InvalidCommand

#
# command functions
#
def test_a():
    pass

def test_b():
    pass

def test_c():
    pass


#
# completion functions
#
def complete_a_option1(arg):
    """ Complete a_option1
        Valid values: FOO, FOD and BAR.
    """

    match = []
    for straw in [ 'FOO', 'FOD', 'BAR' ]:
        if string.find(straw, arg) == 0:
            match.append(straw)

    return match



example_tree = {
    'type': 'command',
    'children': {
        'a': {
            'type': 'command',
            'exec': test_a,
            'argument': {
                'type': 'value',
                'content_type': unicode,
                'description': 'Text'
            },
            'children': {
                'a_option1': {
                    'type': 'option',
                    'argument': {
                        'type': 'value',
                        'content_type': unicode,
                        'description': 'A_Option1',
                        'complete': complete_a_option1
                    }
                },
                'a_option2': {
                    'type': 'option',
                    'argument': {
                        'type': 'value',
                        'content_type': unicode,
                        'description': 'A_Option2'
                    }
                },
                'a_optaon3': {
                    'type': 'option',
                    'argument': {
                        'type': 'value',
                        'content_type': unicode,
                        'description': 'A_Option3'
                    }
                }
            }
        },
        'b': {
            'type': 'command',
            'exec': test_b,
            'argument': {
                'type': 'value',
                'content_type': unicode,
                'description': 'Text'
            },
            'children': {
                'b_bool1': {
                    'type': 'bool'
                }
            }
        },
        'ca': {
            'type': 'command',
            'children': {
                'ca_a': {
                    'type': 'command',
                    'exec': test_c,
                    'children': {
                        'ca_a_option1': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                                'description': 'Text'
                            },
                        },
                        'ca_a_option2': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                                'description': 'Text'
                            }
                        }
                    }
                }
            }
        },
        'cb': {
            'type': 'command',
            'children': {
                'cb_a': {
                    'type': 'command',
                    'exec': test_c,
                    'rest_argument': {
                        'type': 'value',
                        'content_type': unicode,
                        'description': 'test rest argument'
                    },
                    'children': {
                        'cb_a_option1': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                                'description': 'Text'
                            },
                        },
                        'cb_a_option2': {
                            'type': 'option',
                            'argument': {
                                'type': 'value',
                                'content_type': unicode,
                                'description': 'Text'
                            },
                        }
                    }
                }
            }
        },
        'd': {
            'type': 'command',
            'exec': test_c
        }
    }
}

class CliCheck(unittest.TestCase):

    def cli_test(self, cmd_tree, command):
        """ A small helper function to test CLI parsing
        """
        cmd = Command(cmd_tree, command)
        comp = cmd.complete()

        return cmd.exe, cmd.arg, cmd.exe_options, set(comp)



    def test_basic(self):
        """ Run some basic tests
        """

        # Complete empty command. Should return a list of the entries at the lowest level, but does not.
        # Fix by setting self.key = tree['children'] in command.py
        self.assertEqual(self.cli_test(example_tree, ()),
                (None, None, {},
                    set(['a', 'b', 'ca', 'cb', 'd'])
                )
            )

        # here the command should be none, but we get test_b returned
        # XXX: commented out to avoid test failure...
        # TODO: Fix this!
        self.assertEqual(self.cli_test(example_tree, ('',)),
                (None, None, {},
                    set(['a', 'b', 'ca', 'cb', 'd'])
                )
            )

        # test that command and argument gets set correctly
        self.assertEqual(self.cli_test(example_tree, ('a', 'INPUT TEXT', '')),
                (test_a, 'INPUT TEXT', {},
                    set(['a_option1', 'a_option2', 'a_optaon3'])
                )
            )



    def test_complete_options(self):
        """ Test to complete query options
        """

        # Show all options for command
        self.assertEqual(self.cli_test(example_tree, ('a', 'FOO', '')),
            (test_a, 'FOO', {}, set(['a_option1', 'a_option2', 'a_optaon3']))
        )

        # Matching something
        self.assertEqual(self.cli_test(example_tree, ('a', 'FOO', 'a_')),
            (test_a, 'FOO', {}, set(['a_option1', 'a_option2', 'a_optaon3']))
        )

        # Matching something, limit to some options
        self.assertEqual(self.cli_test(example_tree, ('a', 'FOO', 'a_opti')),
            (test_a, 'FOO', {}, set(['a_option1', 'a_option2']))
        )

        # Complete a fully defined option without argument. Should return the option.
        self.assertEqual(self.cli_test(example_tree, ('a', 'FOO', 'a_option1')),
            (test_a, 'FOO', {}, set(['a_option1',]))
        )



    def test_complete_errors(self):
        """ Make sure erroneous completions raise exceptions
        """

        # Start on following option before current is unique
        self.assertRaises(CommandError, self.cli_test, example_tree, ('c', 'c'))

        # Add invalid options to command
        self.assertRaises(CommandError, self.cli_test, example_tree, ('b0rk',))



    def test_complete_option_argument(self):
        """ Test the option argument completion functionality
        """

        # Show all valid arguments
        self.assertEqual(self.cli_test(example_tree, ('a', 'FOO', 'a_option1', '')),
            (test_a, 'FOO', { 'a_option1': '' }, set(['FOO', 'FOD', 'BAR']))
        )

        # Complete two arguments
        self.assertEqual(self.cli_test(example_tree, ('a', 'FOO', 'a_option1', 'F')),
            (test_a, 'FOO', { 'a_option1': 'F' }, set(['FOO', 'FOD']))
        )

        # Complete complete argument
        self.assertEqual(self.cli_test(example_tree, ('a', 'FOO', 'a_option1', 'FOO')),
            (test_a, 'FOO', { 'a_option1': 'FOO' }, set(['FOO', ]))
        )



    def test_bool(self):
        """ Test bool options
        """
        # XXX: seems broken, exceptions include 'b_bool1' set to True, which it
        # shouldn't be..
        self.assertEqual(self.cli_test(example_tree, ('b', 'FOO', '')),
                (test_b, 'FOO', {},
                    set(['b_bool1'])
                )
            )



    def test_overflow(self):
        """ Should raise an InvalidCommand exception as the command is too long
        """

        # Add too many options to command
        self.assertRaises(InvalidCommand, self.cli_test, example_tree, ('a', 'FOO', 'a_option1', 'b', 'a_option2', 'c', 'BAR'))

        # Add too manny commands to command
        self.assertRaises(InvalidCommand, self.cli_test, example_tree, ('d', 'BAR'))



    def test_rest_argument(self):
        """ Test rest arguments
        """

        self.assertEqual(
            self.cli_test(
                example_tree, ('cb', 'cb_a', 'FOO', 'cb_a_option1', 'BAR', 'HAR')
            ),
            (test_c, ['FOO', 'HAR'], { 'cb_a_option1': 'BAR' }, set())
        )


if __name__ == '__main__':
    unittest.main()
