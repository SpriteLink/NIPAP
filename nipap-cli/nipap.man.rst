=====
nipap
=====

the NIPAP command-line client
=============================

Synopsis
--------
**nipap** [command...]

Description
-----------
**nipap** is the NIPAP command-line client. It connects (over a network or locally) to a NIPAP backend, send requests and displays the results.

Bash completion 


Options
-------
NIPAP supports a plethora of operations and to allow access to these via a CLI a somewhat unorthodox approach has been taken. The command to **nipap** is similar to how the CLI of a router works or how the git program works. Following the **nipap** command is one of three object types; **address**, **vrf** or **pool**. For each object type a number of operations is possible; **add**, **list**, **modify**, **remove** and **view**.

**add** is simply used to 

Bugs / Caveats
--------------
Not all operations supported by the NIPAP backend are possible to perform through the CLI, for example expanding or shrinking a pool. That needs to be done through the interface.

Examples
--------
List all prefixes in VRF 123:456 regexp matching '(core|backbone)' (ie, 'core' or 'backbone'):
    $ nipap address list '(core|backbone)' vrf_rt 123:456

List all VRFs:
    $ nipap vrf list

Add a new IPv4 prefix from the pool 'test-linknets' with a prefix length of /31 and a description of 'BAZINGA-CORE-1 <-> FOO-CORE-2':
    $ nipap address add family ipv4 from-pool test-linknets prefix_length 31 description 'BAZINGA-CORE-1 <-> FOO-CORE-2'

Copyright
---------
Kristian Larsson, Lukas Garberg 2011-2013
