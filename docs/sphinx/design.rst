.. Documentation file for design choices

Design choices
==============

This document tries to describe the overall design goals and decisions taken in
the development process of NIPAP.


Overall goals:

 * Simple to interact with for users and other systems alike, you should _want_
   to use it.
 * Powerful, allowing the system to do things that are best performed by
   computers leaving human users happy.
 * Easy to maintain. Tele2 does not have many developers so maintenance needs
   to be simple.

Out of these goals, the following set of tools and resources have been chosen
for the overall design.

 * Backend implemented using PostgreSQL
 * Middleware / XML-RPC API in Python with the Twisted framework
 * CLI client in Python
 * Web GUI in Python using the Pyramid framework



Why PostgreSQL?
---------------
Postgres has a native datatype called 'inet' which is able to store both IPv4
and IPv6 addresses and their prefix-length. The latter (IPv6) usually poses a
problem to database storage as even long integers can only accomodate 64 bits.
Hacks using two columns or some numeric type exist, but often result in
cumbersome or slow solutions. Postgres inet type is indexable and using ip4r
even ternary accesses (such as a longest prefix lookup) is indexable. This
makes it a superior solution compared to most other databases.

PostgreSQL is an open source database under a BSD license, meaning anyone can
use it and modify it. Ingres development was started in the early 1970s and
Postgres (Post Ingres) later evolved into PostgreSQL when the SQL language was
added in 1995 as query language. It is the oldest and the most advanced open
source relational database available today.


Why Python?
-----------
Python is a modern interpreted language with an easy to use syntax and plenty
of powerful features. Experienced programmers usually pick up the language
within a few days, less experienced within a slightly larger time. Its clean
syntax makes it easy for people to familiarize themselves with the NIPAP
codebase. In addition it offers the excellent networking framework Twisted
which NIPAP heavily relies on for it's API functionality.


Why Twisted?
------------
Twisted is one of the leading concurrency frameworks allowing developers to
focus on their own application instead of labour-intensive work surrounding it.
It is used by companies such as Apple (iCal server) and Spotify (playlist
service) to serve hundreds of thousands of users. Twisted includes modules for
serving data over XML-RPC and/or SOAP as well as a complete toolset for
asynchronous calls. For NIPAP, this means we write NIPAP code and not XML-RPC and
concurrency code, as most of that is already complete.


Why XML-RPC?
------------
From the very start, it was a important design goal that NIPAP remain open for
interoperation with any and all other systems and so it would be centered
around a small and simple API from which everything can be performed. Not
intending to reinvent the wheel, especially given the plethora of already
available APIs, it was up to chosing the "right one". Twisted offers built-in
support for SOAP (WebServices) as well as XML-RPC and given design goals such
as simple, SOAP didn't quite feel right and so XML-RPC was chosen. It should
however be noted that NIPAPs XML-RPC protocol is a thin wrapper around an inner
core and so exposing a SOAP interface in addition to XML-RPC can be easily
achieved. XML-RPC shares a lot of similarities with SOAP but is very much less
complex and it is possible for a human to read it in a tcpdump or similar while
with SOAP one likely needs some interpreter or the brain of Albert Einstein.





