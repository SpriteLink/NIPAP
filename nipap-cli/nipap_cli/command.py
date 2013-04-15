""" A module for command parsing

    The command module deals with parsing a cli command properly. It supports
    abbreviated commands ("a" is parsed as the command "add" if there is no
    other command beginning with "a" on that level) and has methods useful for
    tab completion of both commands and external values.
"""

import re
import string


class Command:
    """ A command parser and handler

        The Command class can be used to extract a command from a list of
        strings (such as sys.argv).

        The main method is the :func:`parse_cmd` which handles all the parsing
        and sets appropriate instance variables. It is automatically called
        from the constructor :func:`__init__`.
    """


    """ Contains the current value
    """
    key = {}
    key_complete = True


    """ Contains the next valid values
    """
    children = {}


    """ Pointer to function to execute
    """
    exe = None


    """ Function argument - a single argument passed to the function
    """
    arg = None


    """ Function options - a dict of options passed to the function
    """
    exe_options = {}


    """ List of the commands inputed
    """
    inp_cmd = []

    """ Set when we're scooping up all unknown arguments
    """
    _scoop_rest_arguments = False



    def __init__(self, tree, inp_cmd):
        """ Create instance of the Command class

            The tree argument should contain a specifically formatted dict
            which describes the available commands, options, arguments and
            callbacks to methods for completion of arguments.
            TODO: document dict format

            The inp_cmd argument should contain a list of strings containing
            the complete command to parse, such as sys.argv (without the first
            element which specified the command itself).
        """

        self.inp_cmd = inp_cmd
        self.parse_cmd(tree)



    def _examine_key(self, key_name, key_val, p, i, option_parsing):
        """ Examine the current matching key

            Extracts information, such as function to execute and command
            options, from the current key (passed to function as 'key_name' and
            'key_val').
        """

        # if the element we reached has an executable registered, save it!
        if 'exec' in key_val:
            self.exe = key_val['exec']

        # simple bool options, save value
        if 'type' in key_val and key_val['type'] == 'bool':
            self.exe_options[key_name] = True

        # Elements wich takes arguments need special attention
        if 'argument' in key_val:

            # is there an argument (the next element)?
            if len(self.inp_cmd) > i+1:

                self.key = { 'argument': key_val['argument'] }

                # there is - save it
                if key_val['type'] == 'option':
                    self.exe_options[key_name] = self.inp_cmd[i+1]
                else:
                    self.arg = self.inp_cmd[i+1]

                # Validate the argument if possible
                if 'validator' in key_val['argument']:
                    self.key_complete = key_val['argument']['validator'](self.inp_cmd[i+1])
                else:
                    self.key_complete = True

                # if there are sub parameters, add them
                if 'children' in key_val:
                    self.children = key_val['children']

                # If we reached a command without parameters (which
                # should be the end of the command), unset the children
                # dict.
                elif key_val['type'] == 'command':
                    self.children = None

                # if the command is finished (there is an element after the argument) and
                # there is an exec_immediately-function, execute it now
                if 'exec_immediately' in key_val and len(self.inp_cmd) > i+2:
                    key_val['exec_immediately'](self.inp_cmd[i+1], self.exe_options)
                    # clear exe_options as these were options for exec_immediately
                    self.exe_options = {}

                i += 1

            else:
                # if there is no next element, let key_complete be true
                # and set children to the option argument
                self.children = { 'argument': key_val['argument'] }

            if option_parsing and p == key_name:
                del self.children[key_name]


        # otherwise we are handling a command without arguments
        else:

            # Rest arguments?
            if 'rest_argument' in key_val:

                self._scoop_rest_arguments = True
                self.arg = []

            self.children = key_val.get('children')
            if self.exe is not None:
                option_parsing = True

        return i, option_parsing



    def parse_cmd(self, tree, inp_cmd = None):
        """ Extract command and options from string.

            The tree argument should contain a specifically formatted dict
            which describes the available commands, options, arguments and
            callbacks to methods for completion of arguments.
            TODO: document dict format

            The inp_cmd argument should contain a list of strings containing
            the complete command to parse, such as sys.argv (without the first
            element which specified the command itself).
        """

        # reset state from previous execution
        self.exe = None
        self.arg = None
        self.exe_options = {}

        self.children = tree['children']
        self.key = tree['children']
        option_parsing = False
        self._scoop_rest_arguments = False

        if inp_cmd != None:
            self.inp_cmd = inp_cmd

        # iterate the list of inputted commands
        i = 0
        while i < len(self.inp_cmd):
            p = self.inp_cmd[i]
            self.key = {}

            # Find which of the valid commands matches the current element of inp_cmd
            if self.children is not None:
                self.key_complete = False
                match = False
                for param, content in self.children.items():

                    # match string to command
                    if string.find(param, p) == 0:
                        self.key[param] = content
                        match = True

                        # If we have an exact match, make sure that
                        # is the only element in self.key
                        if p == param and len(self.inp_cmd) > i+1:
                            self.key_complete = True
                            self.key = { param: content }
                            break

                # if we are in scoop-rest-mode, place elements not matching
                # anything in argument-array
                if not match:
                    if self._scoop_rest_arguments:
                        self.arg.append(p)
                    else:
                        raise InvalidCommand("Invalid argument: " + p)

            else:
                raise InvalidCommand('ran out of parameters; command too long')

            # Note that there are two reasons self.key can contain entries:
            # 1) The current string (p) contained something and matched a param
            # 2) The current string (p) is empty and matches all children
            # If p is empty we don't really have a match but still need to
            # have data in self.key to show all possible completions at this
            # level. Therefore, we skip the command matching stuff when
            # len(p) == 0

            if len(p) != 0 and len(self.key) == 1:
                key, val = self.key.items()[0]
                i, option_parsing = self._examine_key(key, val, p, i, option_parsing)

            i += 1



    def complete(self):
        """ Return list of valid completions

            Returns a list of valid completions on the current level in the
            tree. If an element of type 'value' is found, its complete callback
            function is called (if set).
        """

        comp = []
        for k, v in self.key.items():

            # if we have reached a value, try to fetch valid completions
            if v['type'] == 'value':
                if 'complete' in v:
                    comp += v['complete'](self.inp_cmd[-1])

            # otherwise, k is our valid completion
            else:
                comp.append(k)

        return comp



    def next_values(self):
        """ Return list of valid next values
        """

        nval = []

        for k, v in self.children.items():

            # if we have reached a value, try to fetch valid completions
            if v['type'] == 'value':
                if 'complete' in v:
                    nval += v['complete']('')

            # otherwise, k is our valid completion
            else:
                nval.append(k)

        return nval


class CommandError(Exception):
    """ A base error class for the command module
    """

class InvalidCommand(CommandError):
    """ Raised when an invalid command is parsed
    """
