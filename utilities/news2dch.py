#!/usr/bin/env python
"""
Copy content of NEWS file into dch file.

This is a bit of a hack but it works :)
"""

import re
import sys
from distutils.version import StrictVersion


class NewsFile:
    def __init__(self, filename):
        self.latest_version = None
        self.raw_content = []
        # list of versions
        self.versions = []
        # entries indexed by version
        self.entries = {}

        self._readfile(filename)
        self._parse()


    def _readfile(self, filename):
        """ Read content of specified NEWS file
        """
        f = open(filename)
        self.content = f.readlines()
        f.close()


    def _parse(self):
        """ Parse content of NEWS file
        """
        cur_ver = None
        cur_line = None
        for line in self.content:
            m = re.match('Version ([0-9]+\.[0-9]+\.[0-9]+)', line)
            if m:
                cur_ver = m.group(1)
                self.versions.append(cur_ver)
                self.entries[cur_ver] = []
                cur_entry = self.entries[cur_ver]
                if self.latest_version is None or StrictVersion(m.group(1)) > StrictVersion(self.latest_version):
                    self.latest_version = m.group(1)
            elif cur_ver:
                m = re.match(' \* (.*)', line)
                if m:
                    cur_entry.append(m.group(1).strip())
                elif not re.match('-------', line) and re.match(' *[^$]+', line):
                    cur_entry[-1] += " " + line.strip()


import subprocess
class DchFile(NewsFile):
    def _parse(self):
        """ Parse content of DCH file
        """
        cur_ver = None
        cur_line = None
        for line in self.content:
            m = re.match('[^ ]+ \(([0-9]+\.[0-9]+\.[0-9]+)-[0-9]+\) [^ ]+; urgency=[^ ]+', line)
            if m:
                cur_ver = m.group(1)
                self.versions.append(cur_ver)
                self.entries[cur_ver] = []
                cur_entry = self.entries[cur_ver]
                if self.latest_version is None or StrictVersion(cur_ver) > StrictVersion(self.latest_version):
                    self.latest_version = m.group(1)
            elif cur_ver:
                m = re.match('  \* (.*)', line)
                if m:
                    cur_entry.append(m.group(1).strip())
                elif not re.match('$', line) and re.match(' *[^$]+', line):
                    cur_entry[-1] += " " + line.strip()


    def remove_last_entry(self):
        # hehehe, calling sed from python <3
        subprocess.call(['sed', '-i', 'debian/changelog', '-e', '1,/--/d', '-e', '1,1d'])


    def add_entry(self, version, entry):
        """
        """
        if version in self.entries:
            subprocess.call(['dch', '-D', 'stable', '--force-distribution', '--append', entry])
            self.entries[version].append(entry)
        else:
            subprocess.call(['dch', '-D', 'stable', '--force-distribution', '-v', version, entry])
            self.entries[version] = []
            self.entries[version].append(entry)


if __name__ == '__main__':
    df = DchFile(sys.argv[2])
    nf = NewsFile(sys.argv[1])
    # if latest version in DCH is same as in NEWS, remove whole block from DCH
    # so we can readd entries
    if nf.latest_version == df.versions[0]:
        df.remove_last_entry()

    # add entries to DCH from latest version in NEWS file
    for entry in nf.entries[nf.latest_version]:
        df.add_entry(nf.latest_version + "-1", entry)
