Configuration of the web UI
===========================

**NOTE** If you followed the Debian installation instructions and installed the *nipap-www*
package saying 'Yes' to all the options, the user account will have been created and the
configuration file updated accordingly. In this case, you do not need to follow the instructions
in this section. 

Make sure the web UI is installed before proceeding with configuration of it.

The web interface needs its own user account to authenticate towards the
backend and it should be a *trusted* account. Create it with the following::

    nipap-passwd add --username nipap-www --password s3cr3t --name "User account for the web UI" --trusted

Obviously, replace "s3cr3t" with a better password and feel free to use
whichever username you want, as long as you configure it accordingly. The user
account for the web UI should not be used by any other user. Configure
the web UI to use this account by configuring the xmlrpc_uri variable in the
www section of nipap.conf::

    xmlrpc_uri = http://nipap-www@local:s3cr3t@127.0.0.1:1337

This configuring assumes that you did indeed name the account "nipap-www",
replace "s3cr3t" with your password. "@local" instructs the backend to use the
"local" authentication backend. If you are running nipapd on a different host
or port, then update the "127.0.0.1:1337" part accordingly.

Finally, you can add a user for yourself and once you've configured your web
server to serve the NIPAP web UI you should be able to login with this user::

    nipap-passwd add --username myuser --password mypassword --name "my user"


Serving the web UI
==================
The NIPAP web UI is built on the web framework Flask can be served by any
WGSI-capable web server such as Apache httpd with mod_wsgi. For quick tests and
development Flask's own web server is handy.

Flask
-----

Using Flask is the easiest way to get the NIPAP web UI up and running, but
it's not really suitable for production deployment. To serve the NIPAP web UI
from the built-in web server, run the following::

    export FLASK_APP=nipapwww
    export FLASK_ENV=development
    flask run

Using the default configuration, the web UI should now be reachable on port
5000. By default, the NIPAP web UI will look for nipap.conf in /etc/nipap. The
path can be changed setting the environment variable NIPAP_CONFIG_PATH as
such::

      export NIPAP_CONFIG_PATH=~/.local/etc/nipap/nipap.conf

Apache httpd with mod_wsgi
--------------------------

Begin by installing Apache httpd with mod_wsgi::

    apt-get install libapache2-mod-wsgi-py3

Then, add a new virtual host or configure the default one with the line::

    WSGIScriptAlias / /etc/nipap/www/nipap-www.wsgi

If you are using Apache 2.4 you will also need to add the lines::

    <Directory /etc/nipap/www/>
        Require all granted
    </Directory>

The web server needs to be able to write to its cache, alter the permissions of
/var/cache/nipap-www so that the web server can write to it and preferrably
also make sure no one else has access to it. For a typical Debian install of
Apache httpd, the following should suffice::

    chown -R www-data:www-data /var/cache/nipap-www
    chmod -R u=rwX /var/cache/nipap-www

Now, restart Apache httpd and the NIPAP web UI should be up and running!

That wraps up this getting started guide, for more information see the manual
pages.
