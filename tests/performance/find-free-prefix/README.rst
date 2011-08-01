
find_free_prefix() is a function used to retrieve the first available prefix
meeting certain criterias. It is used when we want to automatically assign a
prefix from a pool or another prefix. This is the story of it's optimization ;)

First off, speedtest.py was modified - another option for testing
find_free_prefix was added. It's really not a lot of code, more or less just a
wrapper to easyily pass arguments to the internal class doing the real work. I
had my table with a bunch of prefixes from my previous testing of inserting
prefixes; ::

    nap=# select count(*) from ip_net_plan;
      count  
    ---------
     1175844
    (1 row)

I deleted one early on, thinking find_free_prefix (since I know it works by
searching from low addresses and up) should find it early and I could establish
a fast baseline and see how it would get slower the further away my prefix was.
::

    kll@Overlord ~/NIPAP/tests/performance $ ./speedtest.py --find-free-prefix 1.0.0.0/8
    First free prefix: ['1.0.0.1'] found in 0.975670099258 seconds

That's a hair from one second. At least we know there is some room for improvement.

I re-added 1.0.0.1 and instead deleted 1.0.50.0 so that find_free_prefix would
now need to seek through a bunch of addresses to find an available. The result: ::

    kll@Overlord ~/NIPAP/tests/performance $ ./speedtest.py --find-free-prefix 1.0.0.0/8
    First free prefix: ['1.0.50.0'] found in 27.8062901497 seconds

Looking at the stored procedure
-------------------------------
This is an excerp from the stored procedure: ::

        WHILE set_masklen(current_prefix, masklen(search_prefix)) <= broadcast(search_prefix) LOOP
            -- TODO: can this be optimized by reordering of tests? could potentially save a lot of time on all these small subselects

            -- avoid prefixes larger than the current_prefix but inside our search_prefix
            IF EXISTS (SELECT 1 FROM ip_net_plan WHERE schema = arg_schema AND prefix >>= current_prefix AND prefix << search_prefix) THEN
                SELECT broadcast(current_prefix) + 1 INTO current_prefix;
                CONTINUE;
            END IF;
            -- prefix must not contain any breakouts, that would mean it's not empty, ie not free
            IF EXISTS (SELECT 1 FROM ip_net_plan WHERE schema = arg_schema AND prefix <<= current_prefix) THEN
                SELECT broadcast(current_prefix) + 1 INTO current_prefix;
                CONTINUE;
            END IF;
            IF current_prefix IS NULL THEN
                SELECT broadcast(current_prefix) + 1 INTO current_prefix;
                CONTINUE;
            END IF;
            IF (set_masklen(network(search_prefix), max_prefix_len) = current_prefix) THEN
                SELECT broadcast(current_prefix) + 1 INTO current_prefix;
                CONTINUE;
            END IF;
            IF (set_masklen(broadcast(search_prefix), max_prefix_len) = current_prefix) THEN
                SELECT broadcast(current_prefix) + 1 INTO current_prefix;
                CONTINUE;
            END IF;
            -- TODO: move this to the top? it's probably the fastest operation //kll
            IF EXISTS (SELECT 1 FROM ip_net_plan WHERE schema=arg_schema AND prefix=current_prefix) THEN
                SELECT broadcast(current_prefix) + 1 INTO current_prefix;
                CONTINUE;
            END IF;

            RETURN NEXT current_prefix;

            i_found := i_found + 1;
            IF i_found >= arg_count THEN
                RETURN;
            END IF;

            current_prefix := broadcast(current_prefix) + 1;
        END LOOP;

It basically loops over all prefixes starting at the beginning of the prefixes
to be searched and going forward. For every prefix, it performs six tests to
rule out whether a prefix is eligible or not. The operations used as well as
the order in which we run these tests impact the time it takes greatly.

Here we even find a TODO entry that it might be a good idea to move the last
entry first. Let's do that and rerun; ::

    kll@Overlord ~/NIPAP/tests/performance $ ./speedtest.py --find-free-prefix 1.0.0.0/8
    First free prefix: ['1.0.50.0'] found in 1.4773888588 seconds

That's better. Obviously, doing an exact match is order of magnitudes faster
than a ternary value lookup such as the inet "contains" or "contained within".
We still see a pretty hefty time though, close to 1.5 seconds is not something
we want to wait. Seeing that it now takes pretty much the same time to find the
first prefix (1.0.0.1) as it does to find 1.0.50.0 we can conclude that it's
probably not the equal match performed on all those already "occupied"
prefixes. Instead, let's see what happens next. We still have those "contains"
matches. Running one of those queries manually shows they each take about half
a second: ::

    nap=# SELECT 1 FROM ip_net_plan WHERE schema = (SELECT id FROM ip_net_schema WHERE name='test-schema') AND prefix >>= '1.0.0.0' AND prefix << '1.0.0.0/8';
     ?column? 
    ----------
            1
    (1 row)

    Time: 480.155 ms

We'll copycat our fix for calc_indent and use ip4r indices to speed up these
queries. Once again, this will not affect IPv6 but only speed up IPv4 which is
unfortunate but we have little choice as of today.

With an updated find_free_prefix we get rather reasonable times: ::

    kll@Overlord ~/NIPAP/tests/performance $ ./speedtest.py --find-free-prefix 1.0.0.0/8
    First free prefix: ['1.0.50.0'] found in 0.42563700676 seconds

That's for searching 12800 prefixes. Not halfbad, although something that could
likely grow into a nuisance with a larger amount of prefixes.


