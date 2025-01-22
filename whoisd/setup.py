#!/usr/bin/env python3

from setuptools import setup
import sys

from docutils.core import publish_cmdline
from docutils.writers import manpage


# return all the extra data files
def get_data_files():
    # generate man pages using rst2man
    try:
        publish_cmdline(writer=manpage.Writer(), argv=["nipap-whoisd.man.rst", "nipap-whoisd.8"])
    except Exception as exc:
        print("Failed to compile man file: {}".format(str(exc)), file=sys.stderr)
        sys.exit(1)

    files = [
            ('share/nipap/', ['whoisd.conf.dist']),
            ('bin/', ['nipap-whoisd']),
            ('share/man/man8/', ['nipap-whoisd.8'])
        ]

    return files


long_desc = open('README.rst').read()
short_desc = long_desc.split('\n')[0].split(' - ')[1].strip()

setup(
    description = short_desc,
    long_description = long_desc,
    py_modules = ['nipap_whoisd'],
    data_files = get_data_files(),
)
