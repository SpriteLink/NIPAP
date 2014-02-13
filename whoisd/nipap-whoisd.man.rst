============
nipap-whoisd
============

The NIPAP whois daemon
======================

Synopsis
--------
**nipap-whoisd** [option...]

Description
-----------
**nipap-whoisd** is a whois frontend to the NIPAP backend. It will listen on
the standard whois port and "translate" between received whois queries and the
NIPAP XML-RPC format that the NIPAP backend service speaks.

Options
-------
**nipap-whoisd** accepts the following command-line arguments.

    -h, --help          show a help message
    --config=CONFIG_FILE    read configuration from file **CONFIG_FILE** [default: /etc/nipap/nipap-whoisd.conf]
    --listen=ADDRESS    listen on IPv4/6 **ADDRESS**
    --port=PORT         port to listen on
    --pid-file=PID_FILE     write a PID file to **PID_FILE**
    --no-pid-file       turn off writing PID file
    --version           display version information and exit
    
Copyright
---------
Kristian Larsson, Lukas Garberg 2011-2014
