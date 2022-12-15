#! /bin/bash

# Create NIPAP configuration file
if [ ! -e /etc/nipap/nipap.conf ]; then
    envtpl --keep-template --allow-missing -o /etc/nipap/nipap.conf /nipap/nipap.conf.dist
fi

# Set up local auth database
if [ ! -e /etc/nipap/local_auth.db ]; then
    /usr/sbin/nipap-passwd create-database
fi
if [ `nipap-passwd list | egrep -c ^$WWW_USERNAME\\\s` -eq 0 ]; then
    /usr/sbin/nipap-passwd add -u $WWW_USERNAME -p $WWW_PASSWORD -n "NIPAP WWW user" -t
fi

# Fix permissions
chown -R www-data:www-data /var/cache/nipap-www
chmod -R u=rwX /var/cache/nipap-www

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
