#!/usr/bin/env python

from distutils.command.build import build
from distutils.core import setup

import subprocess
import sys

import nipap

data_files = [
        ('/etc/nipap/', ['nipap.conf.dist']),
        ('/usr/sbin/', ['nipapd', 'nipap-passwd']),
        ('/usr/share/nipap/sql/', [
            'sql/upgrade-1-2.plsql',
            'sql/upgrade-2-3.plsql',
            'sql/upgrade-3-4.plsql',
            'sql/upgrade-4-5.plsql',
            'sql/upgrade-5-6.plsql',
            'sql/functions.plsql',
            'sql/triggers.plsql',
            'sql/ip_net.plsql'
            ]),
    ]

class MyBuild(build):
    """ Customized build command - build manpages.
    """
    def run(self):
        try:
            print('Generating manpages...')
            subprocess.call(["rst2man", "nipapd.man.rst", "nipapd.8"])
            subprocess.call(["rst2man", "nipap-passwd.man.rst", "nipap-passwd.1"])
            data_files.append(('/usr/share/man/man8/', ['nipapd.8']))
            data_files.append(('/usr/share/man/man1/', ['nipap-passwd.1']))

        except OSError:
            print('Warning: rst2man was not found, skipping the manpage generation.')
        build.run(self)


long_desc = open('README.rst').read()
short_desc = long_desc.split('\n')[0].split(' - ')[1].strip()

setup(
    name = 'nipap',
    version = nipap.__version__,
    description = short_desc,
    long_description = long_desc,
    author = nipap.__author__,
    author_email = nipap.__author_email__,
    license = nipap.__license__,
    url = nipap.__url__,
    packages = ['nipap'],
    keywords = ['nipap'],
    requires = ['ldap', 'sqlite3', 'IPy', 'psycopg2', 'parsedatetime'],
    data_files = data_files,
    cmdclass = {'build': MyBuild},
    classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Telecommunications Industry',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.6',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware'
    ]
)
