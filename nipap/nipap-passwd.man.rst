============
nipap-passwd
============

change NIPAP user password
==========================

Synopsis
--------
**nipap-passwd** action [options...]

Description
-----------
The **nipap-passwd** command administrates user accounts in a local (SQLite) database for use with the NIPAP backend. The NIPAP backend can be configured to use a "local" authentication backend, which is implemented with a SQLite database. This utility provides an easy way to add, remove or change users in such a database.

By default, **nipap-passwd** will read the NIPAP configuration file (/etc/nipap/nipap.conf) to find the location of the SQLite database.

Options
-------
**nipapd-passwd** accepts the following command-line arguments.

 positional arguments:
    action {list, add, delete}      define an action to execute

 optional arguments:
    -h, --help                      show a help message
    -u USER, --user=USER            username
    -p PASSWORD, --password=PASSWORD    set user's password to PASSWORD
    -n NAME, --name=NAME            set user's name to NAME
    -t, --trusted                   mark user as trusted
    -r, --readonly                  set user to read only
    -f DB_FILE, --file=DB_FILE      database file [default: read from config]
    -c CONFIG, --config=CONFIG      read configuration from configuration file CONFIG [default: /etc/nipap/nipap.conf]
    --version                       show program's version number and exit

Copyright
---------
Kristian Larsson, Lukas Garberg 2011-2013
