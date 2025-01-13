#!/usr/bin/env python3

from setuptools import setup
from docutils.core import publish_cmdline
from docutils.writers import manpage
import sys
import re


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
        ('share/nipap/sql/', [
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
        ('share/man/man8/', ['nipapd.8']),
        ('share/man/man1/', ['nipap-passwd.1']),
    ]

    return files


long_desc = open('README.rst').read()
short_desc = long_desc.split('\n')[0].split(' - ')[1].strip()

setup(
    description=short_desc,
    long_description=long_desc,
    packages=['nipap'],
    keywords=['nipap'],
    data_files=get_data_files(),
)
