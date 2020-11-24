#!/bin/sh

envtpl --allow-missing --keep-template /whoisd/nipap.conf.dist -o /etc/nipap/nipap.conf

exec /usr/sbin/nipap-whoisd --foreground --no-pid-file

