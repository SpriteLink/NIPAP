Getting started for sysadmins
-----------------------------
This guide will walk you through the setup process to get NIPAP up and running
on a Debian 7.0 (wheezy) or Ubuntu 12.04 or later system. With no prior
experience it should take about 15 minutes. If you are running Debian 12 (Bookworm),
see `installing on Debian 12 <install-debian-12.rst>`_ for instructions.

Debian and Debian derivatives (primarily Ubuntu) are the only distributions
supported at this time. It is certainly possible to install on other Linux
flavours or other UNIX-style operating systems, but there are no prebuilt
packages. Please see `install-unix <install-unix.rst>`_ for installation
instructions on non-Debian like Unix systems.

Debian installation
-------------------
Start by installing PostgreSQL, the contrib package and the ip4r extension.
Depending on which Debian or Ubuntu release you are running, different versions
are available. Anything after PostgreSQL 9.0 will do. Make sure you install
ip4r and the contrib package for your version of Postgres or if this is a fresh
install you can specify the version you want of ip4r and it will pull in the
same version of postgresql::

    root@debian:~# apt-cache search ip4r
    postgresql-9.1-ip4r - IPv4 and IPv6 types for PostgreSQL 9.1
    postgresql-8.4-ip4r - IPv4 and IPv4 range index types for PostgreSQL 8.4
    root@debian:~# apt-cache search postgres contrib
    postgresql-contrib-9.1 - additional facilities for PostgreSQL
    root@debian:~# apt-get install postgresql-9.1-ip4r postgresql-contrib-9.1

Add the NIPAP repo to your package sources, add our public key for proper
authentication of our packages and update your lists::

    echo "deb http://spritelink.github.io/NIPAP/repos/apt stable main extra" | sudo tee /etc/apt/sources.list.d/nipap.list
    wget -O - https://spritelink.github.io/NIPAP/nipap.gpg.key | sudo apt-key add -
    sudo apt-get update

There are now five new packages::

    root@debian:~# apt-cache search nipap
    nipap-cli - Neat IP Address Planner
    nipap-common - Neat IP Address Planner
    nipap-www - web frontend for NIPAP
    nipapd - Neat IP Address Planner XML-RPC daemon
    python-pynipap - Python module for accessing NIPAP
    root@debian:~#

The 'nipapd' package contains the XML-RPC backend daemon which is a required
component of the NIPAP system. It essentially represents the content of the
database over an XML-RPC interface, allowing additions, deletions and
modifications. 'nipap-common' is a library with common stuff needed by all the
other components, so regardless which one you choose, you will get this one.
'nipap-cli' is, not very surprisingly, a CLI client for NIPAP while 'nipap-www'
is the web GUI. Choose your favourite interface or both and install it, you
will automatically get 'python-pynipap' which is the client-side library for
Python applications and since both the web GUI and CLI client is written in
Python, you will need 'python-pynipap'. If you want, you can install the nipapd
backend on one machine and the CLI and/or web on another.

Let's install the backend::

    sudo apt-get install nipapd

During installation, the nipapd package will ask if you want to automatically
load the needed database structure and start nipapd on startup - answer Yes to
both questions. After the installation is done, you will have the PostgreSQL
database server and all the other necessary dependencies installed.


Web UI
------
The nipap-www package comes with an automagic configuration guide that will
help you setup the needed user and configure it if, and only if, you are
running nipapd on the same machine. Install nipap-www with::

    sudo apt-get install nipap-www

When you are asked whether you want to add a user automatically and configure
it, answer yes. If you tried to install nipap-www at the same time as nipapd,
you might not be prompted with the quetion to automatically add a user. Try
doing 'sudo dpkg-reconfigure nipap-www' in the case.

The user added to the local authentication database by the installation script
is merely used by the web interface to talk to the backend.

See `config-www <config-www.rst>`_ for configuration of the web UI and how to
serve it using a web server.
