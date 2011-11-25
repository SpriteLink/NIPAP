.. NIPAP documentation master file, created by
   sphinx-quickstart on Wed Jun 22 11:04:45 2011.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Neat IP-Address Planner
=======================

The majority of this documentation is generated from the Nipap Python module
where most of the server side logic is placed. A thin XML-RPC layer is wrapped
around the Nipap class to expose its functions over an XML-RPC interface as well
as translating internal Exceptions into XML-RPC errors codes. It is feasible to
implement other wrapper layers should one need a different interface, though
the XML-RPC interface should serve most well.

Given that the documentation is automatically generated from this internal Nipap
class, there is some irrelevant information regarding class structures - just
ignore that! :)

Happy hacking!

Contents:

.. toctree::
   :maxdepth: 2

   design
   nipap
   xmlrpc
   authlib
   pynipap


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

