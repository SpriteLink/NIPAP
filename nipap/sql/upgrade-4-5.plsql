--
-- Upgrade from NIPAP database schema version 4 to 5
--

--
-- Recalculate all statistics from scratch
--
CREATE OR REPLACE FUNCTION recalculate_statistics() RETURNS bool AS $_$
DECLARE
	i int;
BEGIN
	UPDATE ip_net_plan SET total_addresses = power(2::numeric, (CASE WHEN family(prefix) = 4 THEN 32 ELSE 128 END) - masklen(prefix)) WHERE family(prefix) = 4;
	UPDATE ip_net_plan SET total_addresses = power(2::numeric, (CASE WHEN family(prefix) = 4 THEN 32 ELSE 128 END) - masklen(prefix)) WHERE family(prefix) = 6;

	FOR i IN (SELECT generate_series(31, 0, -1)) LOOP
		--RAISE WARNING 'Calculating statistics for IPv4/%', i;
		UPDATE ip_net_plan AS inp SET used_addresses = COALESCE((SELECT SUM(total_addresses) FROM ip_net_plan AS inp2 WHERE iprange(inp2.prefix) << iprange(inp.prefix) AND inp2.indent = inp.indent + 1), CASE WHEN (family(prefix) = 4 AND masklen(prefix) = 32) OR (family(prefix) = 6 AND masklen(prefix) = 128) THEN 1 ELSE 0 END) WHERE family(prefix) = 4 AND masklen(prefix) = i;
		UPDATE ip_net_plan SET free_addresses = total_addresses - used_addresses WHERE family(prefix) = 4 AND masklen(prefix) = i;
	END LOOP;

	FOR i IN (SELECT generate_series(127, 0, -1)) LOOP
		--RAISE WARNING 'Calculating statistics for IPv4/%', i;
		UPDATE ip_net_plan AS inp SET used_addresses = COALESCE((SELECT SUM(total_addresses) FROM ip_net_plan AS inp2 WHERE iprange(inp2.prefix) << iprange(inp.prefix) AND inp2.indent = inp.indent + 1), CASE WHEN (family(prefix) = 4 AND masklen(prefix) = 32) OR (family(prefix) = 6 AND masklen(prefix) = 128) THEN 1 ELSE 0 END) WHERE family(prefix) = 6 AND masklen(prefix) = i;
		UPDATE ip_net_plan SET free_addresses = total_addresses - used_addresses WHERE family(prefix) = 4 AND masklen(prefix) = i;
	END LOOP;

	RETURN true;
END;
$_$ LANGUAGE plpgsql;

-- hstore extension is required for AVPs
CREATE EXTENSION IF NOT EXISTS hstore;

-- change default values for pool prefix statistics columns
ALTER TABLE ip_net_pool ALTER COLUMN free_prefixes_v4 SET DEFAULT NULL;
ALTER TABLE ip_net_pool ALTER COLUMN free_prefixes_v6 SET DEFAULT NULL;
ALTER TABLE ip_net_pool ALTER COLUMN total_prefixes_v4 SET DEFAULT NULL;
ALTER TABLE ip_net_pool ALTER COLUMN total_prefixes_v6 SET DEFAULT NULL;

-- update improved pool statistics
UPDATE ip_net_pool SET free_prefixes_v4 = calc_pool_free_prefixes(id, 4);
UPDATE ip_net_pool SET free_prefixes_v6 = calc_pool_free_prefixes(id, 6);
UPDATE ip_net_pool SET total_prefixes_v4 = used_prefixes_v4 + free_prefixes_v4, total_prefixes_v6 = used_prefixes_v6 + free_prefixes_v6;

-- add VRF tags
ALTER TABLE ip_net_vrf ADD COLUMN tags text[] DEFAULT '{}';
COMMENT ON COLUMN ip_net_vrf.tags IS 'Tags associated with the VRF';

-- add pool tags
ALTER TABLE ip_net_pool ADD COLUMN tags text[] DEFAULT '{}';
COMMENT ON COLUMN ip_net_pool.tags IS 'Tags associated with the pool';

-- prefix stats
SELECT recalculate_statistics();

-- add status field
CREATE TYPE ip_net_plan_status AS ENUM ('assigned', 'reserved', 'quarantine');
ALTER TABLE ip_net_plan ADD COLUMN status ip_net_plan_status NOT NULL DEFAULT 'assigned';

-- add AVP column
ALTER TABLE ip_net_vrf ADD COLUMN avps hstore NOT NULL DEFAULT '';
ALTER TABLE ip_net_plan ADD COLUMN avps hstore NOT NULL DEFAULT '';
ALTER TABLE ip_net_pool ADD COLUMN avps hstore NOT NULL DEFAULT '';

-- add expires field
ALTER TABLE ip_net_plan ADD COLUMN expires timestamp with time zone DEFAULT 'infinity';

-- update database schema version
COMMENT ON DATABASE %s IS 'NIPAP database - schema version: 5';
