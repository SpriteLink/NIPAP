Testing prefix insertion time
=============================

Here we look at the time it takes to insert a new prefix into the database.
This is a silly test, one might say, since it should only be limited by the
database and could be seen as any general insertion test. That is true in one
sence, it is mostly limited by the database as there is quite little overhead
added by the NIPAP class and it is quite constant. However, the database
implements a number of stored procedures to calculate certain values (such as
the indent level) and if nothing else, it might be interesting just to see how
the database fares with our specific table setups.

Read on to see how we achieved a speedup by several magnitudes!

Testing method
--------------
We use a small script called speedtest.py to perform our test. It has a mode of
operation called "fill-prefix" in which it takes a prefix as an argument and
fills that prefix with /32s. For every /24 inserted it outputs one line with
the number of the /24 starting at 0 and the time it took on average to insert
one prefix in that /24.

First run - baseline
--------------------

Running the test resulted in a rather apparent decrease in speed with the
number of inserted prefixes. Here's a test inserting a /16, though aborted at
the 214th /24 due to the time it took to run the test.

.. image:: plot-before.png

The output can also be viewed raw, see the file data.insert-start 

When adding a prefix there is not much going on, we do some simple sanity
checking and then a DB INSERT. In the database there are triggers both before
and after the row has been inserted and seeming like good candidates for
optimization this was where focus was placed.

Commenting out the triggers resulted in linear performance again, so it's
somewhere in the triggers and going through the code you'll find that both
calc_indent and the before trigger placed SELECT queries with a ternary value
operator on the 'prefix' column (ie "contains" or "is contained within"). Those
operators are not indexable by default in PostgreSQL with a B-tree index but
instead require the ip4r datatype and GiST indices.

Extracting one of the basic queries from the before trigger, it looks like this: ::

    SELECT * INTO parent 
    FROM ip_net_plan 
    WHERE schema = NEW.schema 
        AND prefix >> NEW.prefix 
    ORDER BY masklen(prefix) DESC 
    LIMIT 1;


The ">>" operator on prefix is the magic that makes us not use indices. With
the query slightly rewritten (so that it may be run manually) and EXPLAIN
ANALYZE added for timing; ::

    EXPLAIN ANALYZE
    SELECT *
    FROM ip_net_plan
    WHERE
        schema = (SELECT id FROM ip_net_schema WHERE name='test-schema')
        AND ip4r(prefix) >> ip4r('1.3.3.1/32')
    ORDER BY masklen(prefix) DESC LIMIT 1;

Results in: ::

                                    QUERY PLAN
    -------------------------------------------------------------------------------
     Limit  (cost=1021.61..1021.61 rows=1 width=175) (actual time=26.121..26.123 rows=1 loops=1)
       InitPlan 1 (returns $0)
         ->  Seq Scan on ip_net_schema  (cost=0.00..1.02 rows=1 width=4) (actual time=0.013..0.017 rows=1 loops=1)
               Filter: (name = 'test-schema'::text)
       ->  Sort  (cost=1020.58..1020.63 rows=21 width=175) (actual time=26.117..26.117 rows=1 loops=1)
             Sort Key: (masklen((ip_net_plan.prefix)::inet))
             Sort Method:  quicksort  Memory: 25kB
             ->  Index Scan using ip_net_plan__schema__index on ip_net_plan  (cost=0.00..1020.48 rows=21 width=175) (actual time=26.080..26.084 rows=2 loops=1)
                   Index Cond: (schema = $0)
                   Filter: (ip4r(prefix) >> '1.3.3.1'::ip4r))
     Total runtime: 26.203 ms
    (11 rows)

Optimizing
----------

ip4r is a PostgreSQL extension that amongst other things bring GiST indexability
for ternary lookup operators such as the << or >>.  The biggest problem with
ip4r is that it currently only supports IPv4 but given that we will have far
more IPv4 entries in the short term, this should do for now and it's definitely
better than nothing. Rewriting the query so it works with both IPv4 and IPv6
input and mixed IPv4 and IPv6 content in the table required some fiddling but
here's the result: ::

    EXPLAIN ANALYZE
    SELECT *
    FROM ip_net_plan
    WHERE
        schema = (SELECT id FROM ip_net_schema WHERE name='test-schema')
        AND ip4r(CASE WHEN family(prefix) = 4 THEN prefix ELSE NULL::cidr END) >> ip4r('1.3.3.1/32')
    ORDER BY masklen(prefix) DESC LIMIT 1


                                    QUERY PLAN
    -------------------------------------------------------------------------------
     Limit  (cost=126.11..126.11 rows=1 width=175) (actual time=0.127..0.129 rows=1 loops=1)
       InitPlan 1 (returns $0)
         ->  Seq Scan on ip_net_schema  (cost=0.00..1.02 rows=1 width=4) (actual time=0.010..0.011 rows=1 loops=1)
               Filter: (name = 'test-schema'::text)
       ->  Sort  (cost=125.08..125.13 rows=20 width=175) (actual time=0.124..0.124 rows=1 loops=1)
             Sort Key: (masklen((ip_net_plan.prefix)::inet))
             Sort Method:  quicksort  Memory: 25kB
             ->  Bitmap Heap Scan on ip_net_plan  (cost=4.57..124.98 rows=20 width=175) (actual time=0.089..0.095 rows=2 loops=1)
                   Recheck Cond: (ip4r(CASE WHEN (family((prefix)::inet) = 4) THEN prefix ELSE NULL::cidr END) >> '1.3.3.1'::ip4r)
                   Filter: (schema = $0)
                   ->  Bitmap Index Scan on ip_net_plan__prefix__ip4r_index  (cost=0.00..4.56 rows=40 width=0) (actual time=0.056..0.056 rows=3 loops=1)
                         Index Cond: (ip4r(CASE WHEN (family((prefix)::inet) = 4) THEN prefix ELSE NULL::cidr END) >> '1.3.3.1'::ip4r)
     Total runtime: 0.210 ms
    (13 rows)


Total runtime down from ~26ms to 0.2! After performing a similar change to
calc_indent, the performance of add_prefix is rather linear and stays around
20ms per operation. 

.. image:: plot-before-and-after.png

It is unlikely my laptop will perform any better but a modern server certainly
should. One thing to keep in mind is that although 20ms is a very acceptable
latency for one transaction, NIPAP is currently single-threaded and so it is
blocked during this period. This means we get some 50 adds per second. With
asynchronous operation we could certainly raise this.

On the downside, ip4r only supports IPv4 at this point, so the graph for IPv6
will likely look much like the "before" plot.

And then what?
--------------

.. image:: plot-after-4610-24s.png

The second test, here plotted is a test where I let my office workstation
insert prefixes over a night, it managed to insert 4610 /24s and in the plot we
can see how the time it takes to insert a prefix increases from roughly 10ms to
closer to 100ms. Around prefix 4200 there is a quite distinct increase in
insertion time which I cannot explain. The test setup is running inside a
VirtualBox machine on a Windows PC and perhaps Windows decided to start doing
something.. or PostgreSQL is planning the query differently. Regardless, given
the low-end hardware I find the results rather satisfactory. There are close to
1.2 million prefixes in the database by the end of the test and with an
insertion time of 0.2 seconds users would likely perceive it as "instant".
Higher end hardware will, needless to say, perform better. With asynchronous
operation, we could handle several of these queries in parallell too.

