--
-- Upgrade from NIPAP database schema version 4 to 5
--

-- add VRF tags
ALTER TABLE ip_net_vrf ADD COLUMN tags text[] DEFAULT '{}';
COMMENT ON COLUMN ip_net_vrf.tags IS 'Tags associated with the VRF';

-- add pool tags
ALTER TABLE ip_net_pool ADD COLUMN tags text[] DEFAULT '{}';
COMMENT ON COLUMN ip_net_pool.tags IS 'Tags associated with the pool';

-- update database schema version
COMMENT ON DATABASE nipap IS 'NIPAP database - schema version: 5';
