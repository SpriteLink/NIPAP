Getting started for sysadmins
---
This guide will walk you through the setup process to get NIPAP up and running
on a Debian 12.0 (Bookworm). With no prior experience of NIPAP, it should take
about 10 minutes.

The instructions assume you are logged in as 'root', however NIPAP will
run as user 'nipap'. If you would rather run the installation process as a
user other than root, add 'sudo' commands where appropriate.

Please see `install-unix <install-unix.rst>`_ for installation instructions
on non-Debian like Unix systems.

Debian 12 (Bookworm) installation
---
Start by bringing the system up to date::

 apt update && apt -y upgrade

And then install the dependencies::

 apt -y install gnupg curl postgresql postgresql-common postgresql-ip4r apache2 libapache2-mod-wsgi-py3

We're going to use the NIPAP repository, so we need to install the key, update sources and then update apt.::

 curl -fsSL https://spritelink.github.io/NIPAP/nipap.gpg.key | gpg --dearmor > /usr/share/keyrings/nipap-keyring.gpg
 echo "deb [signed-by=/usr/share/keyrings/nipap-keyring.gpg] http://spritelink.github.io/NIPAP/repos/apt stable main extra" > /etc/apt/sources.list.d/nipap.list
 apt update

There are now seven new packages::

 root@debian:~# apt-cache search nipap
 nipap-cli - Neat IP Address Planner
 nipap-common - Neat IP Address Planner
 nipap-whoisd - Neat IP Address Planner
 nipap-www - web frontend for NIPAP
 nipapd - Neat IP Address Planner XML-RPC daemon
 python-pynipap - Python module for accessing NIPAP
 python3-pynipap - Python 3 module for accessing NIPAP
 root@debian:~#

The 'nipapd' package contains the XML-RPC backend daemon which is a required
component of the NIPAP system. It essentially represents the content of the
database over an XML-RPC interface, allowing additions, deletions and
modifications. 'nipap-common' is a library with common stuff needed by all the
other components, so regardless which one you choose, you will get this one.
'nipap-cli' is, not very surprisingly, a CLI client for NIPAP while 'nipap-www'
is the web GUI. 'nipap-whoisd' is a whois frontend to the NIPAP backend.
Choose your favourite interface (cli or web or both) and install it, you
will automatically get 'python-pynipap' which is the client-side library for
Python applications and since both the web GUI and CLI client is written in
Python, you will need 'python-pynipap'. If you want, you can install the nipapd
backend on one machine and the CLI and/or web on another.

If you don't install the packages in the order below, you will have to manually
'dpkg-reconfigure nipap-www'.

Install everything apart from nipap-www::

 apt -y install nipapd nipap-common nipap-whoisd nipap-cli nipap-www

During installation, the packages will prompt you for various values. Answer
'Yes' to all the Yes/No questions and accept any other defaults.

Finally, install nipap-www, selecting 'Yes' to all the questions asked.::

 apt -y install nipap-www

After the installation is done, you will have the PostgreSQL
database server and all the other necessary dependencies installed.

Web UI
------

The user added to the local authentication database by the installation script
is merely used by the web interface to talk to the backend.

See `config-www <config-www.rst>`_ for configuration of the web UI and how to
serve it using a web server.
