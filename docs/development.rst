Getting started with NIPAP development
======================================
Got a good idea or some spare time to kill? Help out with NIPAP development and
receive fame!

This guide will try to help you setup an enviroment for further developing
NIPAP into what you want it to become or just help fix identified bugs. The sky
is the limit.

Start a local nipapd
--------------------
You really need the nipapd backend to do any form of development since it's
such a crucial part of the NIPAP system. You'll find the nipapd program in
$NIPAP/nipap. nipapd forks into the background by default as well as writing a
PID file in /var/run. Since development usually doesn't happen as root and most
users don't have access to write files in /var/run, it is recommended to
disable writing a pid file by using the option --no-pid-file. It also helps
avoiding collisions with another running (production?) nipapd, just as changing
the TCP port to listen with --port to does. Last but not least, if you want
some debugging output, it is pretty useful to let nipapd stay in the foreground
and set the log level to debug.
    cd nipap
    ./nipapd -d -f --no-pid-file --port 1234


Using paster to serve the web UI
--------------------------------
In a production environment the NIPAP web UI is typically served via Apache.
For a development environment it is a lot quicker and easier to use paster
which is a fairly small Python application to serve web pages WSGI style.

The web UI ships with a development.ini file that paster reads. Starting it is
no more difficult than running:
    cd nipap-www
    paster serve --reload development.ini

It does require that you have the required dependencies installed and reachable for
