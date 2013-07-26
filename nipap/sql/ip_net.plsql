--------------------------------------------
--
-- The basic table structure and similar
--
--------------------------------------------

COMMENT ON DATABASE nipap IS 'NIPAP database - schema version: 1';

CREATE TYPE ip_net_plan_type AS ENUM ('reservation', 'assignment', 'host');

CREATE TYPE priority_5step AS ENUM ('warning', 'low', 'medium', 'high', 'critical');


CREATE TABLE ip_net_asn (
	asn integer NOT NULL PRIMARY KEY,
	name text
);

--
-- This is where we store VRFs
--
CREATE TABLE ip_net_vrf (
	id serial PRIMARY KEY,
	rt text,
	name text,
	description text
);

--
-- A little hack to allow a single VRF with no VRF or name
--
CREATE UNIQUE INDEX ip_net_vrf__unique_vrf__index ON ip_net_vrf ((''::TEXT)) WHERE rt IS NULL;
CREATE UNIQUE INDEX ip_net_vrf__unique_name__index ON ip_net_vrf ((''::TEXT)) WHERE name IS NULL;
--
INSERT INTO ip_net_vrf (id, rt, name, description) VALUES (0, NULL, 'default', 'The default VRF, typically the Internet.');

CREATE UNIQUE INDEX ip_net_vrf__rt__index ON ip_net_vrf (rt) WHERE rt IS NOT NULL;
CREATE UNIQUE INDEX ip_net_vrf__name__index ON ip_net_vrf (name) WHERE name IS NOT NULL;
-- TODO: add trigger function on I/U to validate vrf format (123.123.123.123:4567 or 1234:5678 - 32:16 or 16:32)

COMMENT ON TABLE ip_net_vrf IS 'IP Address VRFs';
COMMENT ON INDEX ip_net_vrf__rt__index IS 'VRF RT';
COMMENT ON INDEX ip_net_vrf__name__index IS 'VRF name';



--
-- This table is used to store our pools. pools are for a specific
-- purpose and when you need a specific type of address, ie a core
-- loopback or similar, you'll just pick the right pool and get an
-- address assigned automatically.
--
CREATE TABLE ip_net_pool (
	id serial PRIMARY KEY,
	name text NOT NULL UNIQUE,
	description text,
	default_type ip_net_plan_type,
	ipv4_default_prefix_length integer,
	ipv6_default_prefix_length integer
);

COMMENT ON TABLE ip_net_pool IS 'IP Pools for assigning prefixes from';

COMMENT ON INDEX ip_net_pool_name_key IS 'pool name';


--
-- this table stores the actual prefixes in the address plan, or net 
-- plan as I prefer to call it
--
-- pool is the pool for which this prefix is part of and from which 
-- assignments can be made
--
CREATE TABLE ip_net_plan (
	id serial PRIMARY KEY,
	vrf_id integer NOT NULL DEFAULT 0 REFERENCES ip_net_vrf (id) ON UPDATE CASCADE ON DELETE CASCADE,
	prefix cidr NOT NULL,
	display_prefix inet,
	description text,
	comment text,
	node text,
	pool_id integer REFERENCES ip_net_pool (id) ON UPDATE CASCADE ON DELETE SET NULL,
	type ip_net_plan_type NOT NULL,
	indent integer,
	country text,
	order_id text,
	external_key text,
	authoritative_source text NOT NULL DEFAULT 'nipap',
	alarm_priority priority_5step,
	monitor boolean,
	vlan integer
);

COMMENT ON TABLE ip_net_plan IS 'Actual address / prefix plan';

COMMENT ON COLUMN ip_net_plan.vrf_id IS 'VRF in which the prefix resides';
COMMENT ON COLUMN ip_net_plan.prefix IS '"true" IP prefix, with hosts registered as /32';
COMMENT ON COLUMN ip_net_plan.display_prefix IS 'IP prefix with hosts having their covering assignments prefix-length';
COMMENT ON COLUMN ip_net_plan.description IS 'Prefix description';
COMMENT ON COLUMN ip_net_plan.comment IS 'Comment!';
COMMENT ON COLUMN ip_net_plan.node IS 'Name of the node, typically the hostname or FQDN of the node (router/switch/host) on which the address is configured';
COMMENT ON COLUMN ip_net_plan.pool_id IS 'Pool that this prefix is part of';
COMMENT ON COLUMN ip_net_plan.type IS 'Type is one of "reservation", "assignment" or "host"';
COMMENT ON COLUMN ip_net_plan.indent IS 'Number of indents to properly render this prefix';
COMMENT ON COLUMN ip_net_plan.country IS 'ISO3166-1 two letter country code';
COMMENT ON COLUMN ip_net_plan.order_id IS 'Order identifier';
COMMENT ON COLUMN ip_net_plan.external_key IS 'Field for use by exernal systems which need references to its own dataset.';
COMMENT ON COLUMN ip_net_plan.authoritative_source IS 'The authoritative source for information regarding this prefix';
COMMENT ON COLUMN ip_net_plan.alarm_priority IS 'Priority of alarms sent for this prefix to NetWatch.';
COMMENT ON COLUMN ip_net_plan.monitor IS 'Whether the prefix should be monitored or not.';

CREATE UNIQUE INDEX ip_net_plan__vrf_id_prefix__index ON ip_net_plan (vrf_id, prefix);

CREATE INDEX ip_net_plan__vrf_id__index ON ip_net_plan (vrf_id);
CREATE INDEX ip_net_plan__node__index ON ip_net_plan (node);
CREATE INDEX ip_net_plan__family__index ON ip_net_plan (family(prefix));
CREATE INDEX ip_net_plan__prefix_iprange_index ON ip_net_plan USING gist(iprange(prefix));

COMMENT ON INDEX ip_net_plan__vrf_id_prefix__index IS 'prefix';

--
-- Audit log table
--
CREATE TABLE ip_net_log (
	id serial PRIMARY KEY,
	vrf_id INTEGER,
	vrf_rt TEXT,
	vrf_name TEXT,
	prefix_prefix cidr,
	prefix_id INTEGER,
	pool_name TEXT,
	pool_id INTEGER,
	timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
	username TEXT NOT NULL,
	authenticated_as TEXT NOT NULL,
	authoritative_source TEXT NOT NULL,
	full_name TEXT,
	description TEXT NOT NULL
);

COMMENT ON TABLE ip_net_log IS 'Log of changes made to tables';

COMMENT ON COLUMN ip_net_log.vrf_id IS 'ID of affected VRF, or VRF of affected prefix';
COMMENT ON COLUMN ip_net_log.vrf_rt IS 'RT of affected VRF, or RT of VRF of affected prefix';
COMMENT ON COLUMN ip_net_log.vrf_name IS 'Name of affected VRF, or name of VRF of affected prefix';
COMMENT ON COLUMN ip_net_log.prefix_id IS 'ID of affected prefix';
COMMENT ON COLUMN ip_net_log.prefix_prefix IS 'Prefix which was affected of the action';
COMMENT ON COLUMN ip_net_log.pool_id IS 'ID of affected pool';
COMMENT ON COLUMN ip_net_log.pool_name IS 'Name of affected pool';
COMMENT ON COLUMN ip_net_log.timestamp IS 'Time when the change was made';
COMMENT ON COLUMN ip_net_log.username IS 'Username of the user who made the change';
COMMENT ON COLUMN ip_net_log.authenticated_as IS 'Username of user who authenticated the change. This can be a real person or a system which is trusted to perform operations in another users name.';
COMMENT ON COLUMN ip_net_log.authoritative_source IS 'System from which the action was made';
COMMENT ON COLUMN ip_net_log.full_name IS 'Full name of the user who is responsible for the action';
COMMENT ON COLUMN ip_net_log.description IS 'Text describing the action';

--
-- Indices.
--
CREATE INDEX ip_net_log__vrf__index ON ip_net_log(vrf_id);
CREATE INDEX ip_net_log__prefix__index ON ip_net_log(prefix_id);
CREATE INDEX ip_net_log__pool__index ON ip_net_log(pool_id);



--
-- Triggers for sanity checking on ip_net_vrf table.
--
CREATE TRIGGER trigger_ip_net_vrf__iu_before
	BEFORE UPDATE OR INSERT
	ON ip_net_vrf
	FOR EACH ROW
	EXECUTE PROCEDURE tf_ip_net_vrf_iu_before();

CREATE TRIGGER trigger_ip_net_vrf__d_before
	BEFORE DELETE
	ON ip_net_vrf
	FOR EACH ROW
	EXECUTE PROCEDURE tf_ip_net_vrf_d_before();



--
-- Triggers for consistency checking and updating indent level on ip_net_plan
-- table.
--
CREATE TRIGGER trigger_ip_net_plan_prefix__iu_before
	BEFORE UPDATE OR INSERT
	ON ip_net_plan
	FOR EACH ROW
	EXECUTE PROCEDURE tf_ip_net_prefix_iu_before();

CREATE TRIGGER trigger_ip_net_plan_prefix__d_before
	BEFORE DELETE
	ON ip_net_plan
	FOR EACH ROW
	EXECUTE PROCEDURE tf_ip_net_prefix_d_before();

CREATE TRIGGER trigger_ip_net_plan_prefix__iu_after
	AFTER DELETE OR INSERT OR UPDATE
	ON ip_net_plan
	FOR EACH ROW
	EXECUTE PROCEDURE tf_ip_net_prefix_family_after();

