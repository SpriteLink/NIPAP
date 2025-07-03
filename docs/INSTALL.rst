Installation of NIPAP
=====================
NIPAP is officially supported on Debian and Debian derivatives. This includes
pre-built packages, an automated installation (using Debians post-installation
script) and above all, that it is tested.


Installation
------------
If you are running an older Debian system (7, Wheezy) or a Debian derivative, see
`installing on Debian <install-debian.rst>`_ for instructions.

If you are running Debian 12 (Bookworm), see `installing on Debian 12 <install-debian-12.rst>`_
for instructions.

NIPAP should be able to run on any Unix-like operating system but you will need
to install dependencies and NIPAP manually. See `installing on Unix systems
<install-unix.rst>`_ for instructions.


Upgrading
---------
For upgrading on Debian / Ubuntu make sure you use::

    apt-get dist-upgrade

The 'upgrade' command will not install any new dependencies and since it's
fairly common that we introduce new dependencies in NIPAP it's prudent to
always use dist-upgrade.


Configuration
-------------
Once you have NIPAP installed on your machine, read `nipap configuration
<config-nipapd.rst>`_ for a configuration guide of the NIPAP backend (nipapd).

Check out `CLI configuration <config-cli.rst>`_ and / or `configuration of
nipap-www <config-www.rst>`_ which covers the necessary configuration for
setting up the NIPAP web UI.
