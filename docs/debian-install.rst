

Debian installation
===================
Add the NIPAP repo to your package sources and update your lists.
echo "deb http://spritelink.github.com/NIPAP/repos/apt stable main" > \
    /etc/apt/sources.list.d/nipap.list
apt-get update

There are now five new packages;

root@debian:~# apt-cache search nipap
nipap-cli - Neat IP Address Planner
nipap-common - Neat IP Address Planner
nipap-www - web frontend for NIPAP
nipapd - Neat IP Address Planner XML-RPC daemon
python-pynipap - Python module for accessing NIPAP
root@debian:~# 

'nipapd' contains the XML-RPC middleware daemon which is a required component
in the NIPAP suite. It's the glue between the database and the rest of the
world. 'nipap-common' is more of a library with common stuff needed by all the
other components, so regardless which one you choose, you will get this one.
'nipap-cli' is, not very surprisingly, a CLI client for NIPAP while 'nipap-www'
is web GUI. Choose your favourite interface or both and install it, you will
automatically get 'python-pynipap' which is a client-side library for Python
applications and since both the web GUI and CLI client is written in Python,
you will need 'python-pynipap'. If you want, you can install the nipapd
middleware on one machine and the CLI and/or web on a different one.

Once you've picked your packages, issue apt-get install. Here we install the
nipapd daemon and CLI client;
``apt-get install nipapd nipap-cli``
apt-get will complain about that the packages cannot be authenticated. This is
due to the reason that the NIPAP Debian repository is not signed. Ignore the
warning and type 'y' to continue. After the installation is done, you will have
a PostgreSQL database and all the other necessary dependancies installed.

The database needs to be populated with tables and a database user that the
nipapd daemon can authenticate as. This is unfortunately a manual task for now.
Hopefully it will soon be done through debians post-installation sciprint
infrastructure. Until then, you need to follow these steps.

Begin by creating a new database user. To administrate the Postgres database,
you typically sudo to root and then su to postgres, from where you can add the
new user:
``sudo -i
su - postgres
createuser -S -R -D -W nipap``
You'll be prompted for a new password - remember it. Run 

