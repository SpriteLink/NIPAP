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
            # 
            if self.params is not None:
                for param, content in self.params.items():

                    # match string to command
                    if re.match(p, param):
                        self.key[param] = content
                        if p == param:
                            self.key_complete = True
                        else:
                            self.key_complete = False
            else:
                raise Exception('Out of params')

#            if len(self.key) == 0:
#                raise ValueError("No matches")
#            elif len(self.key) > 1:
#                raise ValueError("Multiple matches: %s" % ', '.join(self.key.keys()))

            # there should only be one element, is there an easier
            # way to extract it than looping?
            for key, val in self.key.items():

                # if the element we reached has an executable registered, save it!
                if 'exec' in val:
                    self.exe = val['exec']

                # Options need special attention as they have an argument
                if val['type'] == 'option':

                    # is there an argument (the next element)?
                    if len(inp_cmd) > i+1:

                        # there is - add it to the exec arguments
                        self.exe_options[key] = inp_cmd[i+1]

                        # Validate the argument if possible
                        if 'validator' in val['argument']:
                            self.key_complete = val['argument']['validator'](inp_cmd[i+1])

                            # if the validation failed, this is handled in the same way as an 
                            # incomplete command and should cause the caller to ask for completions
                            if not self.key_complete:
                                # set the key (current element) to the option argument
                                self.key = { 'argumemt': val['argument'] }
                        else:
                            self.key_complete = True

                        # set params to the previous level parameters, before the option argument
                        self.params = self.top_param
                        i += 1

                    else:
                        # if there is no next element, let key_complete be true and set params to the option argument
                        self.params = { 'argument': val['argument'] }

                # Or are we handling a command with an argument?
                elif val['type'] == 'command' and 'argument' in val:
                    if len(inp_cmd) > i+1:
                        self.arg = inp_cmd[i+1]
                        i += 1
                    else:
                        self.params[key] = val.get('argument')

                # otherwise we are handling a command
                else:
                    self.params = val.get('params')
                    self.top_param = self.params

            i += 1


    def complete(self):
        """ Get a list of valid completions on the current level
        """

        print "running complete function %s " % self.key

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

        print "finding next values: %s" % self.key

        for k, v in self.params.items():
            if v['type'] == 'value':
                print "found a value!"
                if 'complete' in v:
                    return v['complete']('')
                else:
                    return []

        print "no fisk: %s" % self.key
        return self.params.keys()


    def get_complete_string(self):
        s = ''
#        print  "smack: %s" % str(self.params)
        for k, v in self.params.items():
            if v['type'] != 'value':
                s += " %s" % k

        return s

