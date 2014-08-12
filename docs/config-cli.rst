CLI configuration
-----------------
This is pretty easy, once you have the nipap-cli package installed (or if
you've installed it manually), a new command, 'nipap', is available to you. It
reads .nipaprc in your home directory and expects to find things like the host
address of nipapd and authentication credentials.

If you haven't already done so, you can create a new user. Execute the
following on the machine running nipapd to create a new user in the local
authentication database::

    nipap-passwd -a *username* -p *username* -n "My CLI user"

Where *username* and *password* is the username and password you wish to
create. Use the same username and password to fill in your .nipaprc. Here's an
example .nipaprc that will work towards localhost with the user you just
crated::

    [global]
    hostname = localhost
    port     = 1337
    username = *username*
    password = *password*
    default_vrf = none

Naturally, if you are running the CLI and nipapd on two different machines,
'hostname' will need to be set to the machine where nipapd is running.

The last option sets which VRF is the default to work with if nothin else is
specified.

Let's try adding a prefix too::

    nipap address add prefix 192.0.2.0/24 type assignment description "test prefix"

And list everything covered by 0.0.0.0/0::

    nipap address list 0/0

