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
* nipap-whoisd - Translator between WHOIS and XML-RPC. We'll ignore this for the moment as it requires separate configuration.
* nipap-www - Web frontend GUI. Can be installed remotely from nipapd if required.
* nipapd - The XML-RPC backend daemon which is a required component of the NIPAP system. It essentially represents the content of the database over an XML-RPC interface, allowing additions, deletions and modifications.
* python-pynipap - Python module for accessing NIPAP
* python3-pynipap - Python 3 module for accessing NIPAP
 
Step 3 - Install NIPAP
----------------------

**Note** If you don't install the packages in the order below, you will have to manually run ``dpkg-reconfigure nipap-www``.

Install everything apart from nipap-www::

 apt -y install nipapd nipap-common nipap-cli

During installation, the packages will prompt you for various values. Answer
'Yes' to all the Yes/No questions and accept any other defaults.

Finally, install nipap-www, selecting 'Yes' to all the questions asked::

 apt -y install nipap-www

Step 4 - Web UI
---------------

The user added to the local authentication database by the installation script
is used by the web interface to talk to the backend. But... By default, the NIPAP configuration
file at /etc/nipap/nipap.conf contains templates that aren't replaced and cause errors. To avoid
this, run the following at the command line and this will hard code the xmlrpc_uri to use
``localhost:1337``::

    sed -i 's/{{NIPAPD_HOST}}:{{NIPAPD_PORT}}/localhost:1337/g' /etc/nipap/nipap.conf

Assuming you have said 'Yes' to the various options offered in Step 3, the configuration file will
be updated accordingly and the only thing you have to do is to install and configure Apache2.
The following script can be pasted directly to the command line (but change
``ServerName nipap.example.com`` to suit your site.)::

    # Install Apache2 and WSGI module.
    apt -y install apache2 libapache2-mod-wsgi-py3

    # Create new virtual host site
    cat > /etc/apache2/sites-available/nipap.conf <<'EOF'
    <VirtualHost *:80>
      ServerName nipap.example.com
      DocumentRoot /var/cache/nipap-www/
      ServerAdmin admin@nipap.example.com
      WSGIScriptAlias / /etc/nipap/www/nipap-www.wsgi

    <Directory /etc/nipap/www/>
        Require all granted
    </Directory>

    <Directory /var/cache/nipap-www/>
        Require all granted
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/nipap_error.log
    CustomLog ${APACHE_LOG_DIR}/nipap_access.log combined

    </VirtualHost>
    EOF

    # Enable WSGI (it is likely already enabled, but here just to make sure)
    a2enmod wsgi

    # Enable the site we've just created
    a2ensite nipap.conf
    
    # Make sure Apache2 can write to the cache
    mkdir -p /var/cache/nipap-www
    chown -R www-data:www-data /var/cache/nipap-www
    chmod -R 770 /var/cache/nipap-www

    # And finally, restart Apache2
    systemctl restart apache2

This should make the site *nipap.example.com* available on port 80.

Add a user::

    nipap-passwd add --username mywebuser --password mywebpassword --name "my web user"

And you should be good to go.

Step 4a - Using Caddy to proxy NIPAP
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you are proxying NIPAP behind Caddy, the caddy definition may need to change
the host header (the example assumes that the public facing address of the site
is ``nipap.example.com`` and the ``ServerName`` definition of the internal site is ``nipap.internal``)::

    nipap.example.com {
        reverse_proxy http://192.0.2.100 {
            header_up Host nipap.internal
        }
    }
        
Step 4b - Other methods of serving the web UI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The page `config-www <config-www.rst>`_ lists other methods of serving the Web UI.

Step 5 - CLI
------------

The page `config-cli <config-cli.rst>`_ details the CLI configuration.
