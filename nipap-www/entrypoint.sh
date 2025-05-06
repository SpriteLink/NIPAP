#! /bin/bash

# If WWW_SECRET_KEY is not set, generate random string
if [ ! -v WWW_SECRET_KEY ]; then
	export WWW_SECRET_KEY=`tr -dc A-Za-z0-9 </dev/urandom | head -c 16`
fi

# Create NIPAP configuration file
if [ ! -e /etc/nipap/nipap.conf ]; then
    envtpl --keep-template --allow-missing -o /etc/nipap/nipap.conf /usr/local/share/nipap/nipap.conf.dist
fi

# Set up local auth database
if [ ! -e /etc/nipap/local_auth.db ]; then
    /usr/local/bin/nipap-passwd create-database
fi
if [ `nipap-passwd list | egrep -c ^$WWW_USERNAME\\\s` -eq 0 ]; then
    /usr/local/bin/nipap-passwd add -u $WWW_USERNAME -p $WWW_PASSWORD -n "NIPAP WWW user" -t
fi

# Configure apache
cat << EOF > /etc/apache2/sites-available/000-default.conf
<VirtualHost *:80>
    WSGIScriptAlias / /etc/nipap/www/nipap-www.wsgi
    ErrorLog \${APACHE_LOG_DIR}/error.log
    CustomLog \${APACHE_LOG_DIR}/access.log combined
    <Directory /etc/nipap/www>
        Require all granted
    </Directory>
</VirtualHost>
EOF

# Start apache
source /etc/apache2/envvars
exec /usr/sbin/apache2 -DFOREGROUND
