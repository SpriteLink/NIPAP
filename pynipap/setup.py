#!/usr/bin/env python

from distutils.core import setup
import sys

import pynipap

requirements = []
if sys.version_info[0] < 3:
    requirements = ['xmlrpclib']

long_desc = open('README.rst').read()
short_desc = long_desc.split('\n')[0].split(' - ')[1].strip()

setup(
        name = 'pynipap',
        version = pynipap.__version__,
        description = short_desc,
        long_description = long_desc,
        author = pynipap.__author__,
        author_email = pynipap.__author_email__,
        license = pynipap.__license__,
        url = pynipap.__url__,
        py_modules = ['pynipap'],
        keywords = ['nipap'],
        requires = requirements,
        classifiers = [
            'Development Status :: 4 - Beta',
            'Intended Audience :: Developers',
            'Intended Audience :: System Administrators',
            'License :: OSI Approved :: MIT License',
            'Natural Language :: English',
            'Operating System :: POSIX :: Linux',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
            'Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware'
            ]
)
