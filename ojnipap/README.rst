OJNIPAP - a NIPAP client library in for Oracle database
=======================================================
OJNIPAP is a client library used to communicate with the NIPAP XML-RPC service
from Oracle Database. It consists of classes using the SQLObject API to
facilitate passing of NIPAP objects between the SQL and Java world as well as,
somewhat limited, access to the NIPAP API functions.

Currently the SQL definitions needed to access the NIPAP functions from the
database is missing, but will be added.

Build instructions
------------------
OJNIPAP depends on JNIPAP and the Oracle Database JDBC drivers. JNIPAP will
automatically be built when needed, but the JDBC drivers must be downloaded
from Oracle. Place the file ``ojdbc5.jar`` in the ojnipap/lib directory and
then build OJNIPAP with:

``make jar```
