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

-- update database schema version
COMMENT ON DATABASE nipap IS 'NIPAP database - schema version: 5';
