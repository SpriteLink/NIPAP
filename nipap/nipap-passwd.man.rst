============
nipap-passwd
============

change NIPAP user password
==========================

Synopsis
--------
**nipapd** [option...]

Description
-----------
The **nipap-passwd** command administrates user accounts in a local (SQLite) database for use with the NIPAP backend. The NIPAP backend can be configured to use a "local" authentication backend, which is implemented with a SQLite database. This utility provides an easy way to add, remove or change users in such a database.

By default, **nipap-passwd** will read the NIPAP configuration file (/etc/nipap/nipap.conf) to find the location of the SQLite database.

Options
-------
**nipapd-passwd** accepts the following command-line arguments.

    -h, --help                      show a help message
    -a ADD_USER, --add=ADD_USER     add user with username ADD_USER
    -c CONFIG, --config=CONFIG      read configuration from configuration file CONFIG [default: /etc/nipap/nipap.conf]
    --create-database               create SqliteAuth database
    -d DELETE_USER, --delete=DELETE_USER    delete user with username DELETE_USER
    -f DB_FILE, --file=DB_FILE      database file [default: read from config]
    -n NAME, --name=NAME            set user's name to NAME
    --latest-version                check if the sqlite database is of the latest version
    -l, --list                      list all users
    -p PASSWORD, --password=PASSWORD    set user's password to PASSWORD
    -r, --readonly                  set usr to read only
    -t, --trusted                   mark user as trusted
    --upgrade-database              upgrade Sqlite database to latest version

Copyright
---------
Kristian Larsson, Lukas Garberg 2011-2014
