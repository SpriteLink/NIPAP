#!/usr/bin/env python

from distutils.core import setup
import subprocess
import sys

import nipapwhoisd


# return all the extra data files
def get_data_files():
    # generate man pages using rst2man
    try:
        subprocess.call(["rst2man", "nipapwhoisd.man.rst", "nipapwhoisd.8"])
    except OSError as exc:
        print >> sys.stderr, "rst2man failed to run:", str(exc)
        sys.exit(1)

    files = [
            ('/etc/nipap/', ['nipapwhoisd.conf.dist']),
            ('/usr/sbin/', ['nipapwhoisd']),
            ('/usr/share/man/man8/', ['nipapwhoisd.8'])
        ]

    return files


long_desc = open('README.rst').read()
short_desc = long_desc.split('\n')[0].split(' - ')[1].strip()

setup(
    name = 'nipapwhoisd',
    version = nipapwhoisd.__version__,
    description = short_desc,
    long_description = long_desc,
    author = nipapwhoisd.__author__,
    author_email = nipapwhoisd.__author_email__,
    license = nipapwhoisd.__license__,
    url = nipapwhoisd.__url__,
    packages = ['nipapwhoisd'],
    keywords = ['nipapwhoisd'],
    requires = ['pynipap'],
    data_files = get_data_files(),
    classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Telecommunications Industry',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.6'
    ]
)
