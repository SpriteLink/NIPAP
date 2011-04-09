
DROP TABLE ip_net_plan;
DROP TABLE ip_net_pool_def_prefix_len;
DROP TABLE ip_net_pool;
DROP TABLE ip_net_schema;

DROP TYPE ip_net_plan_type;
CREATE TYPE ip_net_plan_type AS ENUM ('reservation', 'assignment', 'host');

DROP TYPE priority_3step;
CREATE TYPE priority_3step AS ENUM ('low', 'medium', 'high');

--
-- This is where we store "schemas"
-- think of them as something like namespaces for our address plans
-- one would typically be the global one where all public addresses go
-- then we could have several for RFC1918 space to avoid collisions
--
CREATE TABLE ip_net_schema (
	id serial PRIMARY KEY,
	name text UNIQUE,
	description text
);

COMMENT ON TABLE ip_net_schema IS 'IP Address schemas, something like namespaces for our address plan';

--
-- This table is used to store our pools. pools are for a specific
-- purpose and when you need a specific type of address, ie a core
-- loopback or similar, you'll just pick the right pool and get an
-- address assigned automatically.
--
CREATE TABLE ip_net_pool (
	id serial PRIMARY KEY,
	name text UNIQUE,
	schema integer REFERENCES ip_net_schema (id) ON UPDATE CASCADE ON DELETE CASCADE DEFAULT 1,
	description text,
	default_type ip_net_plan_type NOT NULL DEFAULT 'reservation'
);

COMMENT ON TABLE ip_net_pool IS 'IP Pools for assigning prefixes from';

CREATE TABLE ip_net_pool_def_prefix_len (
	id serial primary key,
	ip_net_pool integer REFERENCES ip_net_pool (id) ON UPDATE CASCADE ON DELETE CASCADE NOT NULL,
	family integer CHECK(family = 4 OR family = 6),
	default_prefix_length integer NOT NULL
);

COMMENT ON TABLE ip_net_pool_def_prefix_len IS 'Store separate default-prefix-length for IPv4/6 per pool';

CREATE UNIQUE INDEX ip_net_pool_def_prefix_len__ip_net_pool__family__index ON ip_net_pool_def_prefix_len (ip_net_pool, family);

--
-- this table stores the actual prefixes in the address plan, or net 
-- plan as I prefer to call it
--
-- pool is the pool for which this prefix is part of and from which 
-- assignments can be made
--
CREATE TABLE ip_net_plan (
	id serial PRIMARY KEY,
	family integer CHECK(family = 4 OR family = 6),
	schema integer REFERENCES ip_net_schema (id) ON UPDATE CASCADE ON DELETE CASCADE DEFAULT 1,
	prefix inet,
	description text,
	comment text,
	node text,
	pool integer REFERENCES ip_net_pool (id) ON UPDATE CASCADE ON DELETE SET NULL,
	type ip_net_plan_type NOT NULL DEFAULT 'reservation',
	country text,
	span_order integer,
	alarm_priority priority_3step NOT NULL DEFAULT 'high'
);

COMMENT ON TABLE ip_net_plan IS 'Actual address / prefix plan';

CREATE UNIQUE INDEX ip_net_plan__schema_prefix__index ON ip_net_plan (schema, prefix);
CREATE INDEX ip_net_plan__node__index ON ip_net_plan (node);


CREATE OR REPLACE FUNCTION tf_ip_net_prefix_family() RETURNS trigger AS $$
DECLARE
	r RECORD;
BEGIN
	NEW.family = family(NEW.prefix);
	RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER trigger_ip_net_pool_prefix__iu ON ip_net_plan;
CREATE TRIGGER trigger_ip_net_pool_prefix__iu 
	BEFORE UPDATE OR INSERT
	ON ip_net_plan
	FOR EACH ROW
	EXECUTE PROCEDURE tf_ip_net_prefix_family();

GRANT ALL ON ip_net_plan TO nils;
GRANT USAGE ON ip_net_plan_id_seq TO nils;
GRANT ALL ON ip_net_pool TO nils;
GRANT USAGE ON ip_net_pool_id_seq TO nils;
GRANT ALL ON ip_net_schema TO nils;
GRANT USAGE ON ip_net_schema_id_seq TO nils;

--
-- example data
--

-- though you probably always want this
INSERT INTO ip_net_schema (name, description) VALUES ('global', 'Global address plan, ie the Internet');

INSERT INTO ip_net_pool (name, description) VALUES ('tele2-infrastructure', 'Tele2 Infrastructure allocation');
INSERT INTO ip_net_pool_def_prefix_len (ip_net_pool, family, default_prefix_length) VALUES ((SELECT id FROM ip_net_pool WHERE name='tele2-infrastructure'), 4, 0);
INSERT INTO ip_net_pool_def_prefix_len (ip_net_pool, family, default_prefix_length) VALUES ((SELECT id FROM ip_net_pool WHERE name='tele2-infrastructure'), 6, 0);

INSERT INTO ip_net_pool (name, description) VALUES ('loopback', 'loopback addresses for routers');
INSERT INTO ip_net_pool_def_prefix_len (ip_net_pool, family, default_prefix_length) VALUES ((SELECT id FROM ip_net_pool WHERE name='loopback'), 4, 32);
INSERT INTO ip_net_pool_def_prefix_len (ip_net_pool, family, default_prefix_length) VALUES ((SELECT id FROM ip_net_pool WHERE name='loopback'), 6, 128);

INSERT INTO ip_net_plan(prefix, description, pool) VALUES ('130.244.0.0/16', 'Tele2s good ol'' /16', (SELECT id FROM ip_net_pool WHERE name='tele2-infrastructure'));
INSERT INTO ip_net_plan(prefix, description, pool) VALUES ('212.151.0.0/16', 'Tele2s middle age /16', (SELECT id FROM ip_net_pool WHERE name='tele2-infrastructure'));

INSERT INTO ip_net_plan(prefix, description, pool) VALUES ('2a00:800::/25', 'Tele2s funky new /25', (SELECT id FROM ip_net_pool WHERE name='tele2-block'));



