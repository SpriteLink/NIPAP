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
and set the log level to debug::

    cd nipap
    ./nipapd -d -f --no-pid-file --port 1234


Using paster to serve the web UI
--------------------------------
In a production environment the NIPAP web UI is typically served via Apache.
For a development environment it is a lot quicker and easier to use paster
which is a fairly small Python application to serve web pages WSGI style.

The web UI ships with a development.ini file that paster reads. Starting it is
no more difficult than running::

    cd nipap-www
    paster serve --reload development.ini

It does require that you have the required dependencies installed and reachable
for paster to work properly. The easiest way of accomplishing this, especially
if you intend on doing development in pynipap (the python client library), is
to use virtualenv. Set up a new virtualenv by doing::

    virtualenv --system-site-packages venv

Activate it::

    . venv/bin/activate

Install pynipap in your virtualenv::

    cd ../pynipap
    python setup.py install

And go back and run paster::

    cd ../nipap-www/
    python `which paster` serve --reload development.ini

If you just run paster you will not utilize the python installed in the
virtualenv and will thus not have access to the pynipap installed in the
virtualenv.

Reach Ballmer peak and code moar
----------------------------------
As has been `empirically proven http://xkcd.com/323/`, a moderate BAC will
vastly improve programming ability. The developers of NIPAP recommend Belgian
Trappiste or a nice stout or an IPA or a whisky or a light lager or really,
anything you like. It's important you like it. Now code moar!

.. image:: mustcodemoar.jpg
        :alt: Must code MOAR!
