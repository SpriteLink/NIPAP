NIPAP release handling
======================
This document tries to describe most aspects of the release handling of NIPAP.

Packaging
---------
NIPAP is packaged into a number of packages. There is the backend parts in form
of the NIPAP XML-RPC daemon (hereinafter referred to as nipapd) that is just
the actual daemon. Since it depends on PostgreSQL it has its own package while
most of its actual code lies in the shared 'nipap' Python module which is
packaged into nipap-common. The same Python module is used by the web frontend
and it is for this reason it is packaged into the nipap-common package. nipapd
and nipap-common share a common source directory (nipap) and thus also share
version number.

The client library/module in pynipap is packaged into a package with the same
name and has its own version number, ie it is not correlated in any way with
the version of the backend parts.


Version numbering
-----------------
Version numbering of NIPAP is in the form of major.minor.patch. Major releases
are milestones for when a number of large improvements have been implemented
and are stable while minor releases will increment for most features. Patch
releases will only include smaller bug fixes or other similarily small changes.

Major releases should generally be released after a number of features have
proven to be stable and fairly bug free. For example, we are at 1.0.0. A couple
of features are implemented over a period of time and for each, a new minor
version is released so we are now at 1.7.0. After some time in production and
seeing that these features behave as expect it, version 2.0.0 can be released
as a "trusted release" with basically the same feature set as 1.7.0 but now
marked as a stable and major version.

This implies that major version can be trusted, while the risk for bugs are
higher in minor versions and again smaller with patch releases.


NEWS / Changelog
----------------
There is a NEWS file outlining the differences with every version. It can
either be updated as changes are made or just before a new release is rolled by
going through the git log since the last version and making sure everything
worth mentioning is in the NEWS file.

Note how a NEWS file is usually used to document changes between versions of a
package while a Changelog file is used to convey information about changes
between commits. The Debian changelog included with packages normally do not
follow this "changelog principle" but rather they are usually used to document
changes to the actual packaging or to patches and changes made by the
maintainer of a package.

As documented on http://www.debian.org/doc/debian-policy/footnotes.html#f16, it
is under certain circumstances perfectly fine to essentially have the same file
as Debian changelog and the project "changelog" (or NEWS file as is more correct).
One such instance is when the Debian package closely follows the project, as is
the case with NIPAP. Thus, the NEWS file will be very similar to the Debian
changelog.

Debian style package managers are able to fetch the Debian changelog file from
repositories and can thus display the changes between versions before
installing a package.


Rolling a new version
---------------------
The different packages are first built as Python easy_install / distutils
packages which are later mangled into a debian package. To roll a new version
there are thus two places that need updating; the first is where easy_install
gets its version number. You can look into setup.py and see the version line.
For nipapd/nipap-common it is imported from the nipap library and stored in a
variable called __version__, you'll find it in nipap/__init__.py. For pynipap,
it is directly in the pynipap.py file.

To roll a new release, update the Python file with the new version number
according to the above instructions. After that, run 'dch -v <version>', where
version is the version number previously entered into the Python file postfixed
with -1. Ie, if you want to release 1.0.0, set that in the Python file and use
1.0.0-1 for dch. The -1 is the version of the debian package for non-native
packages. Non-native packages are all packages that are not exlusively packaged
for debian. If you want to release a new debian release, for example if you
made changes to the actual packagin but not the source of the project, just
increment the -x number.

When dch launches an editor for editing the changelog. Copy the content of the
NEWS file into the Debian changelog (see previous chapten "NEWS / Changelog"
for more information). Make sure the formatting aligns and save the file.
