Getting started on a Unix-like platform
=======================================
NIPAP is primarily supported on Debian or derivatives thereof. This document is
for installing NIPAP on other Unix like systems. Depending on what system you
are trying to install on, you may need to compile dependencies manually or find
third party ways of installing them.

Download NIPAP
--------------
You can download NIPAP as a tar ball from GitHub at
https://github.com/SpriteLink/NIPAP/releases or get the latest source via git::

    git clone https://github.com/SpriteLink/NIPAP.git

Please do note that the git master branch is a development branch and is not
recommended for production environments. Check out the tag for the latest
stable version instead::

    git checkout v0.27.4

PostgreSQL
----------
NIPAP relies on the PostgreSQL database for storage of information. Since
version 0.23 of NIPAP, support for column triggers is required which is
available in PostgreSQL 9.0 or later. ip4r is an addon to PostgreSQL for fast
indexing of IP addresses and prefixes. ip4r 2.0 added IPv6 support and a new IP
version agnostic data type called iprange. As NIPAP handles both IPv4 and IPv6,
ip4r 2.0 or later is required. Please make sure you install both of these
before continuing.

Populating the database
^^^^^^^^^^^^^^^^^^^^^^^
The database needs to be populated with tables and a database user that the
nipapd daemon can authenticate as.

Begin by creating a new database user. To administrate the Postgres database,
you typically sudo to root and then su to postgres, from where you can add the
new user::

    sudo -i
    su - postgres
    createuser -S -R -D -W nipap
    createdb -O nipap nipap

You'll be prompted for a new password when creating the user - remember it. Now
we need to populate the database with some tables and functions. 

On modern versions of PostgreSQL you should be able to install ip4r by running::

    CREATE EXTENSION ip4r;

Continue with the functions, tables and triggers files::

    psql -d nipap -f /usr/share/nipap/sql/ip_net.plsql
    psql -d nipap -f /usr/share/nipap/sql/functions.plsql
    psql -d nipap -f /usr/share/nipap/sql/triggers.plsql

Your database should now be ready to go!


Install NIPAP
-------------
Install the nipapd daemon and CLI client::

    cd nipap
    python setup.py install
    cd ../nipap-cli
    python setup.py install


Running nipapd
--------------
Edit /etc/nipap/nipap.conf and fill in the database password that you set
earlier. Edit /etc/default/nipapd and set RUN=yes. Now you can go ahead and
start nipapd by executing::

    /etc/init.d/nipapd start

CLI configuration
-----------------
This is pretty easy, once you have the nipap-cli command installed, a new
command, 'nipap', is available to you. It reads .nipaprc in your home directory
and expects to find things like the host address of the nipapd and the
authentication credentials.

Here's an example .nipaprc, fill in your username and password with the cred XXX
need to restart nipapd before local auth takes effect
guest login::

    [global]
    hostname = localhost
    port     = 1337
    username = guest
    password = guest
    default_vrf_rt = test

The last option sets which VRF is the default to work with if nothing
else is set. For now, let's create that test vrf so that you can work with it::

    nipap vrf add name test description "My test VRF"

Now let's try adding a prefix too::

    nipap address add prefix 192.0.2.0/24 type assignment description "test prefix"

And list everything covered by 0.0.0.0/0::

    nipap address list 0/0

Installation of the web UI
--------------------------
The NIPAP web UI performs all operations through the NIPAP XML-RPC API served
by nipapd, which means they do not need to be installed on the same machine. It
is built on the Pylons web framework and requires Pylons version >= 1.0.

You will find the source in nipap-www

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
Begin by installing Apache httpd with mod_wsgi, then add a new virtual host or
configure the default one with the line::

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
