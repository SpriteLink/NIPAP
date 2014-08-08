NIPAP
=====

[![Build Status](https://travis-ci.org/SpriteLink/NIPAP.svg?branch=master)](https://travis-ci.org/SpriteLink/NIPAP)
[![Scrutinizer Code Quality](https://scrutinizer-ci.com/g/SpriteLink/NIPAP/badges/quality-score.png?b=master)](https://scrutinizer-ci.com/g/SpriteLink/NIPAP/?branch=master)

NIPAP is a sleek, intuitive and powerful IP address management system built to
efficiently handle large amounts of IP addresses.

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
 * Native support for IPv6 (full feature parity with IPv4)
 * CLI for the hardcore user
 * Native VRF support, allowing overlapping prefixes in different VRFs
 * Support for documenting individual hosts
 * Very powerful search function (featuring regexp)
 * Integrated audit log
 * IP address request system for automatically assigning suitable prefixes
 * XML-RPC middleware, allowing easy integration with other applications or writing
 * Flexible authentication using SQLite and/or LDAP

Check out the webpage for information, screenshots and more:
http://SpriteLink.github.com/NIPAP

Getting started
---------------
If you are running Ubuntu / Debian, add the followin repo:

   deb http://spritelink.github.io/NIPAP/repos/apt stable main

And install nipapd for the backend, nipap-cli for the cli and/or nipap-www for
the web pages.

Also see "Getting it" at http://SpriteLink.github.com/NIPAP.

Contributing
------------
Contributions to NIPAP are more than welcome. Please report bugs or improvement
requests via GitHub issues.

If you would like to submit code, please read through our code submission
guidelines at https://github.com/SpriteLink/NIPAP/wiki/Code%20submission

Community
---------
Keep track of development and community news.
 - Follow NIPAP news on [Google+](https://plus.google.com/100520153767587090955)
 - Chat with other uses and the core team on IRC. `irc.freenode.net` / #NIPAP

Versioning
----------
We try to adhere to [the Semantic Versioning guidelines](http://semver.org/)
but sometimes we mess up.


Copyright and License
---------------------
Code released under the [MIT license](LICENSE). Documentation released under
[Creative Commons](docs/LICENSE).
