#!/usr/bin/env python3

from setuptools import setup
from docutils.core import publish_cmdline
from docutils.writers import manpage
import sys
import re
import nipap


# return all the extra data files
def get_data_files():
    # generate man pages using rst2man
    try:
        publish_cmdline(writer=manpage.Writer(), argv=["nipapd.man.rst", "nipapd.8"])
        publish_cmdline(writer=manpage.Writer(), argv=["nipap-passwd.man.rst", "nipap-passwd.1"])
    except OSError as exc:
        print("rst2man failed to run: %s" % str(exc), file=sys.stderr)
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
            'sql/upgrade-6-7.plsql',
            'sql/functions.plsql',
            'sql/triggers.plsql',
            'sql/ip_net.plsql',
        ],
         ),
        ('/usr/share/man/man8/', ['nipapd.8']),
        ('/usr/share/man/man1/', ['nipap-passwd.1']),
    ]

    return files


long_desc = open('README.rst').read()
short_desc = long_desc.split('\n')[0].split(' - ')[1].strip()
with open('requirements.txt', 'r') as f:

    requires = [re.sub(r'\s*([\w_\-\.\d]+([<>=]+\S+|)).*', r'\1', x.strip()) for x in f if
                x.strip() and re.match(r'^\s*\w+', x.strip())]

setup(
    name='nipap',
    version=nipap.__version__,
    description=short_desc,
    long_description=long_desc,
    author=nipap.__author__,
    author_email=nipap.__author_email__,
    license=nipap.__license__,
    url=nipap.__url__,
    packages=['nipap'],
    keywords=['nipap'],
    install_requires=requires,
    data_files=get_data_files(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Telecommunications Industry',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware',
    ],
)
