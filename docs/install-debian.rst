Getting started for sysadmins
-----------------------------
This guide will walk you through the setup process to get NIPAP up and running
on a Debian 7.0 (wheezy) or Ubuntu 12.04 or later system. With no prior
experience it should take about 15 minutes.

Debian and Debian derivatives (primarily Ubuntu) are the only distributions
supported at this time. It is certainly possible to install on other Linux
flavours or other UNIX-style operating systems, but there are no packages and
currently no instructions. We were hoping to provide .rpms, but given the large
amount of dependencies missing in RHEL and the added complexity in the package
build process, this has yet to happen.


Debian installation
-------------------
Add the NIPAP repo to your package sources and update your lists::

    echo "deb http://spritelink.github.io/NIPAP/repos/apt stable main extra" > /etc/apt/sources.list.d/nipap.list
    apt-get update

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

    apt-get install nipapd

apt-get will complain about that the packages cannot be authenticated. This is
due to the NIPAP Debian repository not being signed. Ignore the warning and
type 'y' to continue. During installation, the nipapd package will ask if you
want to automatically load the needed database structure and start nipapd on
startup - answer Yes to both questions. After the installation is done, you
will have the PostgreSQL database server and all the other necessary
dependencies installed. nipapd will not be able to start until it can connect
to the database and as postgresql does not by default listen to localhost
(127.0.0.1), you will need to edit /etc/postgresql/9.1/main/postgresql.conf and
uncomment the listen_address line to have it listen to localhost (or all '*').
Restart nipapd after editing your PostgreSQL configuration::

    /etc/init.d/nipapd restart


CLI configuration
-----------------
This is pretty easy, once you have the nipap-cli package installed, a new
command, 'nipap', is available to you. It reads .nipaprc in your home directry
and expects to find things like the host address of nipapd the authentication
credentials.

Create a new user in the local authentication database for the CLI::

    nipap-passwd -a *username* -p *username* -n "My CLI user"

Where *username* and *password* is the username and password you wish to crate.
Use the same username and password to fill in your .nipaprc. Here's an example
.nipaprc that will work towards localhost with the user you just crated::

    [global]
    hostname = localhost
    port     = 1337
    username = *username*
    password = *password*
    default_vrf = none

The last option sets which VRF is the default to work with if nothin else is
specified.

Let's try adding a prefix too::

    nipap address add prefix 192.0.2.0/24 type assignment description "test prefix"

And list everything covered by 0.0.0.0/0::

    nipap address list 0/0


Installation and configuration of the web UI
--------------------------------------------
The nipap-www package comes with an automagic configuration guide that will help you setup the needed user and configure it if, and only if, you are running nipapd on the same machine. Install nipap-www with::

    apt-get install nipap-www

When you are asked whether you want to add a user automatically and configure
it, answer yes. If you tried to install nipap-www at the same time as nipapd,
you might not be prompted with the quetion to automatically add a user. Try
doing 'dpkg-reconfigure nipap-www' in the case.

The user added to the local authentication database by the installation
script is merely used by the web interface to talk to the backend. For login to
the web interface, you should create one or more additional user accounts. Use
the nipap-passwd utility to add a user::

    nipap-passwd -a *username* -p *password* -n "Name of my new user"

Serving the web UI
------------------
The NIPAP web UI can be served by any WGSI-capable web server such as Apache
httpd with mod_wsgi. For quick tests and development the lightweight server
'paster', part of Python Paste, is handy.

paster
======
Using paster is the easiest way to get the NIPAP web UI up and running, but
it's not really suitable for deployment. Anyway, to serve the NIPAP web UI from
paster, simply run the following::

	paster serve /etc/nipap/nipap-www.ini

Using the default configuration, the web UI should now be reachable on port
5000. To change the port, edit /etc/nipap/nipap-www.ini.

Apache httpd with mod_wsgi
==========================
Begin by installing Apache httpd with mod_wsgi::

	apt-get install libapache2-mod-wsgi

Then, add a new virtual host or configure the default one with the line::

	WSGIScriptAlias / /etc/nipap/nipap-www.wsgi

The web server needs to be able to write to its cache, alter the permissions of
/var/cache/nipap-www so that the web server can write to it and preferrably
also make sure no one else has access to it. For a typical Debian install of
Apache httpd, the following should suffice::

	chown -R www-data:www-data /var/cache/nipap-www
	chmod -R u=rwX /var/cache/nipap-www

Now, restart Apache httpd and the NIPAP web UI should be up and running!

That wraps up this getting started guide, for more information see the manual
pages.
