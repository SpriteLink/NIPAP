=====
nipap
=====

-----------------------------
the NIPAP command-line client
-----------------------------

Synopsis
========
**nipap** [command...]

Description
===========
**nipap** is the NIPAP command-line client. It connects (over a network or locally) to a NIPAP backend, send requests and displays the results.

**nipap** ships with a bash completion file which greatly simplifies working with **nipap**.


Options
=======
NIPAP supports a plethora of operations and to allow access to these via a CLI a somewhat unorthodox command structure has been chosen. The command to **nipap** is similar to how the CLI of a router works or how the git or iproute2 programs work. Following the **nipap** command is one of three object types; **address**, **vrf** or **pool**. For each object type a number of operations is possible; **add**, **list**, **modify**, **remove** and **view**. The operation is appended after the object to **nipap** after which options to the operation follows.

**nipap** object operation [options...]

Object types
------------

**address** is the object type for prefixes or addresses where an address is just a prefix with all bits set in the subnet mask (ie /32 for IPv4 or /128 for IPv6). One could argue that it should be called **prefix** instead, but as that would collide bash-completion wise with **pool**, **address** was chosen instead.

**pool** is simply a time-saver for getting new prefixes. One or more larger prefixes are grouped together in a pool and when you want a new prefix, you can request one from a pool and the system will automatically allocate the first available sub-prefix in that pool, for you.

**vrf** is simply a VRF. Prefixes/addresses must be unique within one VRF but can overlap between different VRFs. Google it for a more in depth explanation.

Object operations
-----------------

**add** is simply used to add a new object of the specified type.

**modify** modify an object.

**list** list will list one or more object of the specified type, possibly filtered by certain options.

**remove** remove an object.

**view** is used to get detailed information about one particular object.

Bugs / Caveats
==============
Not all operations supported by the NIPAP backend are possible to perform through the CLI, for example expanding or shrinking a pool. That needs to be done through the web interface.

Examples
========
List all VRFs:
    $ nipap vrf list

Create a VRF:
    $ nipap vrf add rt 123:456 name TEST-VRF

Add a new prefix:
    $ nipap address add prefix 192.0.2.0/24 type reservation description "My IP block from RIPE"

Create a pool called 'test-linknets' with a default type of 'assignment' and default prefix-length of 30 and 112 for IPv4 and IPv6 respectively:
    $ nipap pool add name test-linknets description "Link networks for my test network" default-type assignment ipv4_default_prefix_length 30 ipv6_default_prefix_length 112

Add a new IPv4 prefix from the pool 'test-linknets'. The type will be set to 'assignment' as that is the default-type for this pool (created in previous example) and the prefix-length will be /30 as that is the default for IPv4.
    $ nipap address add family ipv4 from-pool test-linknets description 'BAZINGA-CORE-1 <-> FOO-CORE-2'

Add a new IPv4 prefix from the pool 'test-linknets' (created in a previous example) and override the default prefix-length with /31:
    $ nipap address add family ipv4 from-pool test-linknets prefix_length 31 description 'BAZINGA-CORE-1 <-> FOO-CORE-2'

List all prefixes regexp matching '(core|backbone)' (ie, 'core' or 'backbone'):
    $ nipap address list '(core|backbone)'

Modify a prefix and set a new description:
    $ nipap address modify 192.0.2.0/24 set description FOO

Author
=========
Kristian Larsson, Lukas Garberg

Copyright
=========
Kristian Larsson, Lukas Garberg 2011-2013
