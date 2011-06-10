#!/usr/bin/python

import unittest
import sys
sys.path.append('../napd/')

import nap

class NapSql(unittest.TestCase):
	def __init__(self):
		pass

	def test_calc_indent(self):
		""" Test automatic calculation of indent level
			
			Insert baseline data, namely 192.0.2.0/24
			Verify indent level is 0, since it should be a root prefix
			Insert 192.0.2.0/27
			Verify indent level is 1 for 192.0.2.0/27
			Insert 192.0.2.0/32
			Insert 192.0.2.1/32
			Insert 192.0.2.2/32
			Insert 192.0.2.3/32
			Verify indent level is 2 for 192.0.2.[0-3]/32
			Insert 192.0.2.32/32
			Insert 192.0.2.33/32
			Insert 192.0.2.34/32
			Insert 192.0.2.35/32
			Verify indent level is 1 for 192.0.2.3[2-5]/32
			Insert 192.0.2.32/27
			Verify indent level is 1 for 192.0.2.32/27
			Verify indent level is 2 for 192.0.2.3[2-5]/32
			Remove 192.0.2.0/27
			Verify indent level is 1 for 192.0.2.[0-3]/32
		"""


if __name__ == '__main__':
	unittest.main()

