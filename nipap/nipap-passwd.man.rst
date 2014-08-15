============
nipap-passwd
============

Synopsis
--------
``nipap-passwd`` [OPTIONS]

Description
-----------
The **nipap-passwd** command administrates user accounts in a local (SQLite) database for use with the NIPAP backend. The NIPAP backend can be configured to use a "local" authentication backend, which is implemented with a SQLite database. This utility provides an easy way to add, remove or change users in such a database.

By default, **nipap-passwd** will read the NIPAP configuration file (/etc/nipap/nipap.conf) to find the location of the SQLite database.

Options
-------
**nipapd-passwd** accepts the following command-line arguments.

--create-database

    Create an empty SqliteAuth database in the path specified in the config
    or by option **-f**

--latest-version

    Check if the SQLite database is of the latest version

--upgrade-database

    Upgrade SQLite database to latest version

-l, --list

    List all users in the SQLite database

-a ADD_USER, --add=ADD_USER

    Add user with username *ADD_USER* to the database

-p PASSWORD, --password=PASSWORD

    In combination with option **-a**, the password of the user will be set to *PASSWORD*.
    In combination with option **--test-user**, the authentication will be tested with *PASSWORD*.

-n NAME, --name=NAME

    Set user's name to *NAME*

-r, --readonly

    Give the user read-only permissions, i.e. the user is not able to edit anything

-t, --trusted

    Mark user as trusted. A trusted user will be able to impersonate other users

--test-user TEST_USER

    Try to authenticate with *TEST_USER*. The program will return exit code **2** if the user does not exist or the password is wrong.

-d DELETE_USER, --delete=DELETE_USER

    Delete user with username *DELETE_USER* from the database

-c CONFIG, --config=CONFIG

    Read configuration from the specified file
    [default: /etc/nipap/nipap.conf]

-f DB_FILE, --file=DB_FILE

    Use the specified file as SQLite database file
    [default: read from config]

-h, --help

    Show a help message

Return codes
------------

The program will either return one of the following codes

- ``0`` on success
- ``1`` on error
- ``2`` if the authentication with option *--test-user* failed

Copyright
---------
Kristian Larsson, Lukas Garberg 2011-2014
