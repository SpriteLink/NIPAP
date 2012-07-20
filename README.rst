NIPAP
=====
NIPAP is the Neat IP Address Planner - a system built for managing large
amounts of IP addresses.

Having been developed at a fairly large service provider with operations
throughout Europe, NIPAP is well suited for large organisations with massive
amounts of IP addresses just as well as smaller enterprises with simple needs.
The intuitive web interface lowers the barrier of entry considerable for
beginner users while also offering advanced search by regexp and IPv4/IPv6
prefix. It features a powerful Google-style search, both a web GUI and a CLI
together with client libraries for Python, Java and Oracle for those that want
to integrate with other systems.

Features in short:
 * Very fast and scalable to hundreds of thousands of prefixes
 * A stylish and intuitive web interface
 * CLI for the hardcore user
 * Native support for IPv6 (full feature parity with IPv4)
 * Support for VRFs through the use of "schemas", allowing overlapping prefixes
 * Very powerful search function
 * Integrated audit log
 * IP address request system for automatically assigning suitable prefixes
 * XML-RPC middleware, allowing easy integration with other applications or writing
 * Flexible authentication using SQLite and/or LDAP

Check out the webpage for information, screenshots and more:
http://SpriteLink.github.com/NIPAP

Getting started
---------------
If you are running Ubuntu / Debian, add the followin repo:
deb http://spritelink.github.com/NIPAP/repos/apt stable main
And install nipapd for the backend, nipap-cli for the cli and/or nipap-www for
the web pages.

Also see "Getting it" at http://SpriteLink.github.com/NIPAP.

License
-------
X11 / MIT

Contributing
------------
Contributions or suggestions are very much welcome! Fork us on GitHub! :)

