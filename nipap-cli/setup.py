#!/usr/bin/env python3

from distutils.core import setup
import subprocess
import sys

import nipap_cli

# return all the extra data files
def get_data_files():

    # This is a bloody hack to circumvent a lack of feature with Python distutils.
    # Files specified in the data_files list cannot be renamed upon installation
    # and we don't want to keep two copies of the .nipaprc file in git
    import shutil
    shutil.copyfile('nipaprc', '.nipaprc')

    # generate man pages using rst2man
    try:
        subprocess.call(["rst2man", "nipap.man.rst", "nipap.1"])
    except OSError as exc:
        print("rst2man failed to run:", str(exc), file=sys.stderr)
        sys.exit(1)

    files = [
            ('/etc/skel/', ['.nipaprc']),
            ('/usr/local/bin/', ['helper-nipap', 'nipap']),
            ('/usr/local/share/doc/nipap-cli/', ['bash_complete', 'nipaprc']),
            ('/usr/local/share/man/man1/', ['nipap.1'])
        ]

    return files


setup(
    name = 'nipap-cli',
    version = nipap_cli.__version__,
    description = "NIPAP shell command",
    long_description = "A shell command to interact with NIPAP.",
    author = nipap_cli.__author__,
    author_email = nipap_cli.__author_email__,
    license = nipap_cli.__license__,
    url = nipap_cli.__url__,
    packages = ['nipap_cli'],
    keywords = ['nipap_cli'],
    requires = ['IPy', 'pynipap'],
    data_files = get_data_files(),
    classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Telecommunications Industry',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Internet'
    ]
)

# Remove the .nipaprc put the by the above hack.
import os
os.remove('.nipaprc')
