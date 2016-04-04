#!/usr/bin/env python

from distutils.core import setup
import subprocess
import sys

import nipap


# return all the extra data files
def get_data_files():
    # generate man pages using rst2man
    try:
        subprocess.call(["rst2man", "nipapd.man.rst", "nipapd.8"])
        subprocess.call(["rst2man", "nipap-passwd.man.rst", "nipap-passwd.1"])
    except OSError as exc:
        print >> sys.stderr, "rst2man failed to run:", str(exc)
        sys.exit(1)

    files = [
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
            ('/usr/share/man/man8/', ['nipapd.8']),
            ('/usr/share/man/man1/', ['nipap-passwd.1'])
        ]

    return files


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
    data_files = get_data_files(),
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
