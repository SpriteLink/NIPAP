Getting started
---------------
This will walk you through the setup process to get NIPAP running. With no
prior experience it should take about 15 minutes to get NIPAP running,
including installing all prerequisites.

Debian and Ubuntu are the only two distributions supported at this time. It is
certainly possible to install on other Linux flavours or other UNIX-style
operating systems, but there are no packages and currently no instructions. We
were hoping to provide .rpms, but given the large amount of dependencies
missing in RHEL and the added complexity in the package build process, this has
yet to happen.


Debian installation
-------------------
Add the NIPAP repo to your package sources and update your lists::

    echo "deb http://spritelink.github.com/NIPAP/repos/apt stable main" > /etc/apt/sources.list.d/nipap.list
    apt-get update

There are now five new packages::

    root@debian:~# apt-cache search nipap
    nipap-cli - Neat IP Address Planner
    nipap-common - Neat IP Address Planner
    nipap-www - web frontend for NIPAP
    nipapd - Neat IP Address Planner XML-RPC daemon
    python-pynipap - Python module for accessing NIPAP
    root@debian:~#

'nipapd' contains the XML-RPC middleware daemon which is a required component
in the NIPAP suite. It's the glue between the database and the rest of the
world. 'nipap-common' is more of a library with common stuff needed by all the
other components, so regardless which one you choose, you will get this one.
'nipap-cli' is, not very surprisingly, a CLI client for NIPAP while 'nipap-www'
is web GUI. Choose your favourite interface or both and install it, you will
automatically get 'python-pynipap' which is a client-side library for Python
applications and since both the web GUI and CLI client is written in Python,
you will need 'python-pynipap'. If you want, you can install the nipapd
middleware on one machine and the CLI and/or web on a different one.

Once you've picked your packages, issue apt-get install. Here we install the
nipapd daemon and CLI client::

    apt-get install nipapd nipap-cli

apt-get will complain about that the packages cannot be authenticated. This is
due to the reason that the NIPAP Debian repository is not signed. Ignore the
warning and type 'y' to continue. After the installation is done, you will have
the PostgreSQL database server and all the other necessary dependancies
installed except for ip4r, an addon to Postgres which allows for efficient
indexing of IPv4 and IPv6 data.

ip4r
----
The latest ip4r code in CVS supports IPv4 as well as IPv6. Unfortunately, it
has not been released as a new version yet nor do any distributions carry the
version from CVS, thus for IPv6 support you will have to get the CVS version
yourself.

If you are lucky enough to run a Debian 6.0 (Squeeze) installation on amd64, we
have a prebuilt ip4r package in the NIPAP Debian repository that matches up
with the PostgreSQL 8.4 that ships in Debian 6.0. Add the 'extras' repo, update
and install it with::

    echo "deb http://spritelink.github.com/NIPAP/repos/apt stable main extras" > /etc/apt/sources.list.d/nipap.list
    apt-get update
    apt-get install postgresql-8.4-ip4r

... and skip to the next section.

If you are using something other than Debian 6.0 on amd64, you will need to
install ip4r from source. Get ip4r from CVS;
http://pgfoundry.org/scm/?group_id=1000079
Once you have it, follow the instructions to have it installed on your machine.
It should be a simple matter of getting a few dev libs for postgresl via apt
and then make && make install.

Populating the database
-----------------------
The database needs to be populated with tables and a database user that the
nipapd daemon can authenticate as. This is unfortunately a manual task for now.
Hopefully it will soon be done through debians post-installation sciprint
infrastructure. Until then, you need to follow these steps.

Begin by creating a new database user. To administrate the Postgres database,
you typically sudo to root and then su to postgres, from where you can add the
new user::

    sudo -i
    su - postgres
    createuser -S -R -D -W nipap
    createdb -O nipap nipap

You'll be prompted for a new password when creating the user - remember it. Now
we need to populate the database with some tables and functions. In the ip4r
directory downloaded via CVS, there is a file called ip4r.sql that needs to be
run in for the 'nipap' database, again as the nipap user::

    psql -d nipap -f <path to ip4r.sql>

Continue with the functions file followed by the tables::

    psql -d nipap -f /usr/share/nipap/sql/functions.plsql
    psql -d nipap -f /usr/share/nipap/sql/ip_net.plsql

Your database is now ready to go!

Running nipapd
--------------
Edit /etc/nipap/nipap.conf and fill in the database password that you set
earlier. Edit /etc/default/nipapd and set RUN=yes. Now you can go ahead and
start nipapd by executing ``/etc/init.d/nipapd start``

nipapd ships with a default local authentication database with a user called
'guest' and with the password 'guest'. You can set up the CLI client to test
your new setup or continue to the web UI configuration to get the web up and
running.

CLI configuration
-----------------
This is pretty easy, once you have the nipap-cli command installed, a new
command, 'nipap', is available to you. It reads .nipaprc in your home directory
and expects to find things like the host address of the nipapd and the
authentication credentials.

Here's an example .nipaprc that will work towards localhost with the default
guest login::

    [global]
    hostname = localhost
    port     = 1337
    username = guest
    password = guest
    default_schema = test

The last option sets which schema which is the default to work with if nothing
else is set. Schemas is an integral part of working with NIPAP and you can read
more about it in the user documentation. For now, let's create that test schema
so that you can work with it::

    nipap schema add name test description "My test schema"

Now let's try adding a prefix too::

    nipap address add prefix 192.0.2.0/24 type assignment description "test prefix"

And list everything covered by 0.0.0.0/0::

    nipap address list 0/0

Installation of the web UI
--------------------------
The NIPAP web UI performs all operations through the NIPAP XML-RPC API served
by nipapd, which means they do not need to be installed on the same machine. It
is built on the Pylons web framework and requires Pylons version >= 1.0. This
version has unfortunately not yet made it into neither the Debian nor the
Ubuntu official repositories yet. For you lycky enough to run an apt-based
distribution, there is a Pylons 1.0 package in the NIPAP 'extra' repository
which should work on any apt-based system running python 2.5, 2.6 or 2.7.  See
how to enable the 'extra' repo under the ip4r-section above. With the 'extra'
repository enabled, the NIPAP web UI is installed using the following command::

    apt-get install nipap-www

When apt-get has completed the installation, you should have all dependencies
required for the NIPAP web UI as well as the web UI itself installed.

Configuration of the web UI
---------------------------
Begin by adding a user for the web interface to the local authentication
database on the server where nipapd is running::

	nipap-passwd -a *username* -p *password* -n 'NIPAP web UI' -t

The '-t' option tells nipap-passwd to make the new user a 'trusted' user, that
is a user which can authenticate against nipapd using one username but log all
changes as made by another user. See the docs for the NIPAP authentication
library for more information about this:
http://spritelink.github.com/NIPAP/nipap/authlib.html

Now we need to configure the web UI with the URI to the nipapd server. Edit
/etc/nipap/nipap.conf and set the option 'xmlrpc_uri' under the section
'[www]'. The URI should have the form
'http://*username*:*password*@*address*:*port*', for example
'http://www:secret@127.0.0.1:9000' to connect to nipapd running on the local
machine (127.0.0.1) listening on port 9000 and authenticate with the username
'www' and password 'secret'.

For authentication, the NIPAP web UI uses the same authentication library and
settings as nipapd. That means, if they are running on the same machine they by
default use the same authentication database and the users can use the same
credentials for the web UI as for the backend. If they are not running on the
same machine, there will be two separate authentication databases; one for the
XML-RPC backend and one for the web UI.  Thus the web users needs to be added
on the machine where the web UI is running as well, using the 'nipap-passwd'
command as described above. These users does not need to be 'trusted' as above
though, so skip the '-t' option.

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

	chown www-data:www-data /var/cache/nipap-www
	chmod -R u=rwX /var/cache/nipap-www

Now, restart Apache httpd and the NIPAP web UI should be up and running!

That wraps up this getting started guide, for more information see the manual
pages.
