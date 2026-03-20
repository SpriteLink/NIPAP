#!/usr/bin/env python3

from setuptools import setup
from docutils.core import publish_cmdline
from docutils.writers import manpage
import sys


def generate_manpages():
    """Generate man pages from RST sources."""
    try:
        publish_cmdline(writer=manpage.Writer(), argv=["nipapd.man.rst", "nipapd.8"])
        publish_cmdline(writer=manpage.Writer(), argv=["nipap-passwd.man.rst", "nipap-passwd.1"])
    except OSError as exc:
        print("rst2man failed to run: %s" % str(exc), file=sys.stderr)
        sys.exit(1)


# Generate man pages before packaging
generate_manpages()

long_desc = open('README.rst').read()
short_desc = long_desc.split('\n')[0].split(' - ')[1].strip()

setup(
    description=short_desc,
    long_description=long_desc,
    packages=['nipap'],
    keywords=['nipap'],
)
