#!/usr/bin/env python3

from setuptools import setup

long_desc = open('README.rst').read()
short_desc = long_desc.split('\n')[0].split(' - ')[1].strip()

setup(
        description = short_desc,
        long_description = long_desc
)
