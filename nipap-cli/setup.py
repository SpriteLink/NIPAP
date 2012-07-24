#!/usr/bin/env python

from distutils.core import setup

import nipap_cli

setup(
    name = 'nipap-cli',
    version = nipap_cli.__version__,
    description = "NIPAP shell command",
    long_description = "A shell command to interact with NIPAP.",
    author = nipap_cli.__author__,
    author_email = nipap_cli.__author_email__,
    license = nipap_cli.__license__,
    url = nipap_cli.__url__,
    packages = [ 'nipap_cli', ],
    keywords = ['nipap_cli', ],
    requires = ['pynipap', ],
    data_files = [
				('/usr/bin/', ['helper-nipap', 'nipap']),
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
