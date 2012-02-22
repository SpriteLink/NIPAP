import re

class Command:


    """ Contains the current value
    """
    key = {}
    key_complete = True

    """ Contains the next valid values
    """
    params = {}

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


    def __init__(self, tree, inp_cmd):

        self.inp_cmd = inp_cmd
        self.parse_cmd(tree, inp_cmd)


    def parse_cmd(self, tree, inp_cmd):
        """ Extract command and options from string.
        """

        self.exe = None
        self.arg = None
        self.exe_options = {}

        self.params = tree['params']
        self.key = {}

        # iterate the list of inputted commands
        i = 0
        while i < len(inp_cmd):
            p = inp_cmd[i]
            self.key = {}

            # Find which of the valid commands matches the current element of inp_cmd
            if self.params is not None:
                self.key_complete = False
                for param, content in self.params.items():

                    # match string to command
                    if re.match(p, param):
                        self.key[param] = content

                        # If we have an exact match, make sure that
                        # is the only element in self.key
                        if p == param and len(inp_cmd) > i+1:
                            self.key_complete = True
                            self.key = { param: content }
                            break
#                        else:
#                            self.key_complete = False

            else:
                raise Exception('Out of params')

            for key, val in self.key.items():

                # if the element we reached has an executable registered, save it!
                if 'exec' in val:
                    self.exe = val['exec']

                # Elements wich takes arguments need special attention
                if 'argument' in val:

                    # is there an argument (the next element)?
                    if len(inp_cmd) > i+1:

                        self.key = { 'argumemt': val['argument'] }

                        # there is - save it
                        if val['type'] == 'option':
                            self.exe_options[key] = inp_cmd[i+1]
                        else:
                            self.arg = inp_cmd[i+1]

                        # Validate the argument if possible
                        if 'validator' in val['argument']:
                            self.key_complete = val['argument']['validator'](inp_cmd[i+1])

                        else:
                            self.key_complete = True

                        # if there are sub parameters, add them
                        if 'params' in val:
                            self.params = val['params']

                        # if the command is finished (there is an element after the argument) and
                        # there is an exec_imemdiately-function, execute it now
                        if 'exec_immediately' in val and len(inp_cmd) > i+2:
                            val['exec_immediately'](inp_cmd[i+1], self.exe_options)

                        i += 1

                    else:
                        # if there is no next element, let key_complete be true
                        # and set params to the option argument
                        self.params = { 'argument': val['argument'] }


                # otherwise we are handling a command without arguments
                else:
                    self.params = val.get('params')

            i += 1


    def complete(self):
        """ Get a list of valid completions on the current level
        """

        comp = []
        for k, v in self.key.items():

            # if we have reached a value, try to fetch valid values from it
            if v['type'] == 'value':
                if 'complete' in v:
                    comp += v['complete'](self.inp_cmd[-1])

            # otherwise, k is our valid completion
            else:
                comp.append(k)

        return comp


    def next_values(self):
        """ Get a list of valid next values
        """


        for k, v in self.params.items():
            if v['type'] == 'value':
                if 'complete' in v:
                    return v['complete']('')
                else:
                    return []

        return self.params.keys()


    def get_complete_string(self):
        s = ''
        for k, v in self.params.items():
            if v['type'] != 'value':
                s += " %s" % k

        return s

