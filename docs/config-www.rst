Installation and configuration of the web UI
--------------------------------------------
This assumes you have installed the nipap-www package via apt or equivalent.

For login to the web interface, you should create one or more user accounts.
You might have already created a user interface when installing the nipap-www
package but that account is for the web interface to talk to the backend.
Adding the following accounts is for login to the web interface itself.
Use the nipap-passwd utility to add a user::

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
