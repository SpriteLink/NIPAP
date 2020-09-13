#!/usr/bin/env python3

import re
from setuptools import setup
from docutils.core import publish_cmdline
from docutils.writers import manpage
import sys

import nipap_whoisd


# return all the extra data files
def get_data_files():
    # generate man pages using rst2man
    try:
        publish_cmdline(writer=manpage.Writer(),
                        argv=["nipap-whoisd.man.rst", "nipap-whoisd.8"])
    except OSError as exc:
        print("rst2man failed to run:", str(exc), file=sys.stderr)
        sys.exit(1)

    files = [
        ('/etc/nipap/', ['whoisd.conf.dist']),
        ('/usr/sbin/', ['nipap-whoisd']),
        ('/usr/share/man/man8/', ['nipap-whoisd.8'])
    ]

    return files


with open('requirements.txt', 'r') as f:
    requires = [re.sub(r'\s*([\w_\-\.\d]+([<>=]+\S+|)).*', r'\1', x.strip())
                for x in f if
                x.strip() and re.match(r'^\s*\w+', x.strip())]

long_desc = open('README.rst').read()
short_desc = long_desc.split('\n')[0].split(' - ')[1].strip()

setup(
    name='nipap-whoisd',
    version=nipap_whoisd.__version__,
    description=short_desc,
    long_description=long_desc,
    author=nipap_whoisd.__author__,
    author_email=nipap_whoisd.__author_email__,
    license=nipap_whoisd.__license__,
    url=nipap_whoisd.__url__,
    py_modules=['nipap_whoisd'],
    keywords=['nipap-whoisd'],
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
        'Programming Language :: Python :: 3.6'
    ]
)
