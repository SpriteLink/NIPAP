Installing NIPAP on Debian 12 (Bookworm)
========================================

Introduction
------------

This guide will walk you through the setup process to get NIPAP up and running
on a Debian 12.0 (Bookworm). With no prior experience of NIPAP, the base installation
detailed here should take a couple of minutes (plus the time to download and install
the required packages).

After installation, NIPAP will run as user 'nipap', however these instructions assume you
are logged in as 'root'. If you would rather run the installation process as a user other
than root, log in as that user and add 'sudo' commands where appropriate.

Please see `install-unix <install-unix.rst>`_ for installation instructions
on non-Debian like Unix systems or `install-debian <install-debian.rst>`_ for older
Debian systems.

Installation
============

Step 1 - Bring system up to date and install dependencies
---------------------------------------------------------

Bring system up to date::

 apt update && apt -y upgrade

And then install the dependencies::

 # PostgreSQL
 apt -y install gnupg curl postgresql postgresql-common postgresql-contrib postgresql-ip4r
 
Step 2 - Add NIPAP repository
-----------------------------

As we're going to install from the NIPAP repository, we need to add the key, update sources and then update apt::

 # Download key, put it in a format 'apt' can understand and put it in the keyrings directory
 curl -fsSL https://spritelink.github.io/NIPAP/nipap.gpg.key | gpg --dearmor > /usr/share/keyrings/nipap-keyring.gpg
 # Add the repository to our sources
 echo "deb [signed-by=/usr/share/keyrings/nipap-keyring.gpg] http://spritelink.github.io/NIPAP/repos/apt stable main extra" > /etc/apt/sources.list.d/nipap.list
 # And upate apt
 apt update

There are now seven new packages available:

* nipap-cli - Command line client. Can be installed remotely from nipapd if required.
* nipap-common - Library with common stuff needed by all the other components.
* nipap-whoisd - Translator between WHOIS and XML-RPC.
* nipap-www - Web frontend GUI. Can be installed remotely from nipapd if required.
* nipapd - The XML-RPC backend daemon which is a required component of the NIPAP system. It essentially represents the content of the database over an XML-RPC interface, allowing additions, deletions and modifications.
* python-pynipap - Python module for accessing NIPAP
* python3-pynipap - Python 3 module for accessing NIPAP
 
Step 3 - Install NIPAP
----------------------

**Note** If you don't install the packages in the order below, you will have to manually run ``dpkg-reconfigure nipap-www``.

Install everything apart from nipap-www::

 apt -y install nipapd nipap-common nipap-whoisd nipap-cli

During installation, the packages will prompt you for various values. Answer
'Yes' to all the Yes/No questions and accept any other defaults.

Finally, install nipap-www, selecting 'Yes' to all the questions asked::

 apt -y install nipap-www

Step 4 - Web UI
---------------

The user added to the local authentication database by the installation script
is merely used by the web interface to talk to the backend. Assuming you have
said 'Yes' to the various options offered in Step 3, the configuration file will
be updated accordingly.

See `config-www <config-www.rst>`_ for configuration of the web UI and how to
serve it using a web server.
