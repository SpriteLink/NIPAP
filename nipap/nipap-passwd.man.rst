============
nipap-passwd
============

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
	action {list, add, delete, test-user, create-database, upgrade-database, latest-version}      define an action to execute

	list
    	List all users in the SQLite database.

	add
		Add user with username specified with **-u** and password specified
		with **-p** to the database.

	delete
    	Delete user with username specifies with **-u** from the database

	test-user
		Try to authenticate with user specified with the option **-u** and
		password speficied with **-p**. The program will return exit code **2**
		if the user does not exist or the password is wrong.

	create-database
		Create an empty SqliteAuth database in the path specified in the config
		or by option **-f**

	upgrade-database
    	Upgrade SQLite database to latest version

	latest-version
    	Check if the SQLite database is of the latest version

 optional arguments:
    -h, --help
		Show a help message

	-u USER, --user=USER
    	In combination with action **add**, the username of the user will be set to *USER*.
	    In combination with option **test-user**, the authentication will be tested with *USER.
		In combination with action **delete**, the user *USER* will be deleted.

    -p PASSWORD, --password=PASSWORD
    	In combination with action **add**, the password of the user will be set to *PASSWORD*.
	    In combination with option **test-user**, the authentication will be tested with *PASSWORD*.

    -n NAME, --name=NAME
    	Set user's name to *NAME*

    -t, --trusted
    	Mark user as trusted. A trusted user will be able to impersonate other users

    -r, --readonly
    	Give the user read-only permissions, i.e. the user is not able to edit anything

    -f DB_FILE, --file=DB_FILE
    	Use the specified file as SQLite database file
	    [default: read from config]

    -c CONFIG, --config=CONFIG
    	Read configuration from configuration file *CONFIG*
	    [default: /etc/nipap/nipap.conf]

    --version
		Show program's version number and exit


Return codes
------------

The program will either return one of the following codes

- ``0`` on success
- ``1`` on error
- ``2`` if the authentication with option *--test-user* failed

Copyright
---------
Kristian Larsson, Lukas Garberg 2011-2015
