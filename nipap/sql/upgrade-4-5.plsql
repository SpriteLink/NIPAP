--
-- Upgrade from NIPAP database schema version 4 to 5
--

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
UPDATE ip_net_plan SET total_addresses = power(2::numeric, (CASE WHEN family(prefix) = 4 THEN 32 ELSE 128 END) - masklen(prefix));
UPDATE ip_net_plan AS inp SET used_addresses = COALESCE((SELECT SUM(total_addresses) FROM ip_net_plan AS inp2 WHERE inp2.prefix << inp.prefix AND inp2.indent = inp.indent + 1), CASE WHEN (family(prefix) = 4 AND masklen(prefix) = 32) OR (family(prefix) = 6 AND masklen(prefix) = 128) THEN 1 ELSE 0 END);
UPDATE ip_net_plan SET free_addresses = total_addresses - used_addresses;

-- add status field
CREATE TYPE ip_net_plan_status AS ENUM ('active', 'reserved', 'quarantine');
ALTER TABLE ip_net_plan ADD COLUMN status ip_net_plan_status NOT NULL DEFAULT 'active';

-- update database schema version
COMMENT ON DATABASE nipap IS 'NIPAP database - schema version: 5';
