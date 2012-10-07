#!/usr/bin/env python

from distutils.core import setup

import nipap

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
    requires = ['twisted', 'ldap', 'sqlite3', 'IPy', 'psycopg2'],
    data_files = [
				('/etc/nipap/', ['local_auth.db', 'nipap.conf']),
				('/usr/sbin/', ['nipapd', 'nipap-passwd']),
				('/usr/share/nipap/sql/', [
					'sql/functions.plsql',
					'sql/ip_net.plsql',
					'sql/clean.plsql'
				])
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
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware'
    ]
)
