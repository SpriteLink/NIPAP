======
nipapd
======

the NIPAP backend server
========================

Synopsis
--------
**nipapd** [option...]

Description
-----------
**nipapd** is the NIPAP backend server. In order for a client application to access information stored in the NIPAP database, it connects (over a network or locally) to a running nipapd backend instance and sends its' requests.

By default nipapd will fork off into the background and listen to TCP port 1337 for requests from clients.

Options
-------
nipapd accepts the following command-line arguments. These and more options are available in the configuration file nipap.conf, which typically resides in /etc/nipap/nipap.conf. On debian-like systems, /etc/default/nipapd is used to control the startup of nipapd in the init script.

    -h, --help                      show a help message
    -d, --debug                     enable debugging
    -f, --foreground                run in foreground and log to stdout
    -l ADDRESS, --listed=ADDRESS    listen to IPv4/6 **ADDRESS**
    -p PORT, --port=PORT            listen on TCP port **PORT**
    -c CONFIG-FILE, --config=CONFIG_FILE    read configuration from file **CONFIG_FILE**
    -P PID_FILE, --pid-file=PID_FILE    write a PID file to **PID_FILE**
    --no-pid-file                   turn off writing a PID file (overrides config file)

Bugs / Caveats
--------------
**nipapd** is single threaded and handles requests in a synchronous fashion. This means that slow queries will block the backend from responding to other queries until the slow query has run to completion.

Examples
--------
To start nipapd in the background using default values, type:
    $ nipapd

To start nipapd in the foreground with a specific port, e.g. 1234 and with no PID file, typically for development:
    $ nipapd -f -p 1234 --no-pid-file

Copyright
---------
Kristian Larsson, Lukas Garberg 2011-2013
