#!/usr/bin/env python

from distutils.core import setup

import nipap_cli

long_desc = nipap_cli.__doc__
short_desc = long_desc.split('\n')[0].strip()

setup(
    name = 'nipap-cli',
    version = nipap_cli.__version__,
    description = short_desc,
    long_description = long_desc,
    author = nipap_cli.__author__,
    author_email = nipap_cli.__author_email__,
    license = nipap_cli.__license__,
    url = nipap_cli.__url__,
    py_modules = ['nipap_cli', 'command' ],
    keywords = ['nipap_cli' ],
    requires = ['pynipap', ],
    data_files = [
				('/usr/bin/', ['nipap_helper', 'nipap']),
                ('/usr/share/doc/nipap-cli/', ['bash_complete', 'nipaprc'])
    ],
    classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Telecommunications Industry',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.6',
        'Topic :: Internet'
    ]
)
