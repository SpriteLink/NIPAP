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
				<argument>
					<name>prefix</name>
					<type>default</type>
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


	def find_cmd(self, remain):

		arg = remain.split()[0]
		self.cur_cmd += ' ' + arg
		self.cur_cmd = self.cur_cmd.strip()

		ss = "branch/name[starts-with(text(), '" + arg + "')]"
		matches = self.cur_tree.xpath(ss)
		if len(matches) == 0:
			print "Unknown command:", self.cur_cmd
			return
		elif len(matches) > 1:
			print "Ambiguous command:", self.cur_cmd
			return

		self.cur_tree = matches[0].getparent()
		if not self.cur_tree.xpath("command"):
			# this is not the command we are looking for, keep searching!
			self.find_cmd(' '.join(remain.split()[1:]))

		self.command = self.cur_tree
		# we got our command, let's parse arguments
		return self.command, self.parse_args(remain)


	
	def parse_args(self, remain):
		pass





test_string = "show route 1.3.3.7 detail exact"
t = Completer(xml_tree)
cmd, args = t.find_cmd(test_string)
print cmd.tag('command')
#print etree.tostring(t.command)



