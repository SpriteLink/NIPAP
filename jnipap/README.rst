JNIPAP - a Java NIPAP client library
====================================
JNIPAP is a Java client library to communicate with the NIPAP server via
XML-RPC.

Build instructions
------------------
JNIPAP depends on parts of the Apache Web Services framework. All dependencies
are shipped with the NIPAP repository, so as long as you have gradle in your
path you should be able to build the JNIPAP .jar with:

``make jar``

To run tests, do:

``make test``
