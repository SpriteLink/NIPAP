#!/bin/sh

envtpl --allow-missing /nipap/nipap.conf.dist -o /etc/nipap/nipap.conf

/usr/sbin/nipap-passwd create-database
if [ -n "$NIPAP_USERNAME" -a -n "$NIPAP_PASSWORD" ]; then
	echo "Creating user '$NIPAP_USERNAME'"
	/usr/sbin/nipap-passwd add --username $NIPAP_USERNAME --name "NIPAP user" --password $NIPAP_PASSWORD
fi

exec /usr/sbin/nipapd --debug --foreground --auto-install-db --auto-upgrade-db --no-pid-file
