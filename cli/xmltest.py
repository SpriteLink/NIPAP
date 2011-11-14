#!/usr/bin/python

from StringIO import StringIO
from lxml import etree

regexpNS = "http://exslt.org/regular-expressions"
x = """
	<branch>
		<branch>
			<name>request</name>
			<branch>
				<name>system</name>
				<argument>
					<name>prefix</name>
				</argument>
			</branch>
		</branch>
		<branch>
			<name>show</name>
			<branch>
				<name>route</name>
				<command>show_route</command>
				<option>
					<name>exact</name>
					<type>flag</type>
					<value_type>boolean</value_type>
				</option>
				<option>
					<name>community</name>
					<type>value</type>
					<value_type>community</value_type>
					<argument>
						<name>prefix</name>
						<value_type>community</value_type>
						<order>1</order>
					</argument>
				</option>
				<argument>
					<name>prefix</name>
					<value_type>prefix46</value_type>
					<order>1</order>
				</argument>
			</branch>
		</branch>
	</branch>"""

xml_tree = etree.parse(StringIO(x))


class Completer:
	def __init__(self, xml_tree):
		self.tree = xml_tree.getroot()
		self.cur_tree = self.tree
		self.cur_cmd = ''


	def find_node(self, tree, ntype, name, return_one = True):
		""" Find a node in the XML tree
		"""
		ss = ntype + "/name[starts-with(text(), '" + name + "')]"
		matches = tree.xpath(ss)
		if len(matches) == 0:
			if not return_one:
				return matches
			raise ValueError("Unknown input: " + name)
		elif len(matches) == 1:
			if return_one:
				return matches[0]
			return matches
		elif len(matches) > 1:
			if not return_one:
				return matches
			# it's an error if we have more than 1 matcha dn return_one is set
			raise ValueError("Ambiguous input: " + name)



	def parse_args(self, remain):
		arg = remain.split()[0]

		print "Trying to parse arguments, input:", remain
		match = self.find_node(self.cur_tree, 'option', arg)

		return {'test': 'foo'}



	def find_cmd(self, remain):

		arg = remain.split()[0]
		self.cur_cmd += ' ' + arg
		self.cur_cmd = self.cur_cmd.strip()

		match = self.find_node(self.cur_tree, 'branch', arg)
		self.cur_tree = match.getparent()
		if not self.cur_tree.xpath("command"):
			# this is not the command we are looking for, keep searching!
			return self.find_cmd(' '.join(remain.split()[1:]))

		self.command = self.cur_tree
		# we got our command, let's parse arguments
		return self.command, self.parse_args(' '.join(remain.split()[1:]))


	



test_string = "show route 1.3.3.7 detail exact"
t = Completer(xml_tree)
cmd, args = t.find_cmd(test_string)
print "Command:", cmd.find('command').text
print "Arguments:"
for a in args:
	print "  ", a + ":", args[a]



