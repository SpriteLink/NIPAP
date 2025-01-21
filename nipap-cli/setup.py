#!/usr/bin/env python3

from docutils.core import publish_cmdline
from docutils.writers import manpage
from setuptools import setup
import sys

# return all the extra data files
def get_data_files():

    # generate man pages from .rst-file
    try:
        publish_cmdline(writer=manpage.Writer(), argv=["nipap.man.rst", "nipap.1"])
    except Exception as exc:
        print("rst2man failed to run: %s" % str(exc), file=sys.stderr)
        sys.exit(1)

    files = [
            ('bin/', ['helper-nipap', 'nipap']),
            ('share/doc/nipap-cli/', ['bash_complete', 'nipaprc']),
            ('share/man/man1/', ['nipap.1'])
        ]

    return files


long_desc = open('README.rst').read()
short_desc = long_desc.split('\n')[0]

setup(
    description = short_desc,
    long_description = long_desc,
    packages = ['nipap_cli'],
    data_files = get_data_files(),
)
