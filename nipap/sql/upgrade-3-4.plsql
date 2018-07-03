--
-- Upgrade from NIPAP database schema version 3 to 4
--

-- add statistics to vrf table
ALTER TABLE ip_net_vrf ADD COLUMN num_prefixes_v4 numeric(40) DEFAULT 0;
ALTER TABLE ip_net_vrf ADD COLUMN num_prefixes_v6 numeric(40) DEFAULT 0;
ALTER TABLE ip_net_vrf ADD COLUMN total_addresses_v4 numeric(40) DEFAULT 0;
ALTER TABLE ip_net_vrf ADD COLUMN total_addresses_v6 numeric(40) DEFAULT 0;
ALTER TABLE ip_net_vrf ADD COLUMN used_addresses_v4 numeric(40) DEFAULT 0;
ALTER TABLE ip_net_vrf ADD COLUMN used_addresses_v6 numeric(40) DEFAULT 0;
ALTER TABLE ip_net_vrf ADD COLUMN free_addresses_v4 numeric(40) DEFAULT 0;
ALTER TABLE ip_net_vrf ADD COLUMN free_addresses_v6 numeric(40) DEFAULT 0;

COMMENT ON COLUMN ip_net_vrf.num_prefixes_v4 IS 'Number of IPv4 prefixes in this VRF';
COMMENT ON COLUMN ip_net_vrf.num_prefixes_v6 IS 'Number of IPv6 prefixes in this VRF';
COMMENT ON COLUMN ip_net_vrf.total_addresses_v4 IS 'Total number of IPv4 addresses in this VRF';
COMMENT ON COLUMN ip_net_vrf.total_addresses_v6 IS 'Total number of IPv6 addresses in this VRF';
COMMENT ON COLUMN ip_net_vrf.used_addresses_v4 IS 'Number of used IPv4 addresses in this VRF';
COMMENT ON COLUMN ip_net_vrf.used_addresses_v6 IS 'Number of used IPv6 addresses in this VRF';
COMMENT ON COLUMN ip_net_vrf.free_addresses_v4 IS 'Number of free IPv4 addresses in this VRF';
COMMENT ON COLUMN ip_net_vrf.free_addresses_v6 IS 'Number of free IPv6 addresses in this VRF';

-- add statistics to prefix table
ALTER TABLE ip_net_plan ADD COLUMN total_addresses numeric(40) DEFAULT 0;
ALTER TABLE ip_net_plan ADD COLUMN used_addresses numeric(40) DEFAULT 0;
ALTER TABLE ip_net_plan ADD COLUMN free_addresses numeric(40) DEFAULT 0;
COMMENT ON COLUMN ip_net_plan.total_addresses IS 'Total number of addresses in this prefix';
COMMENT ON COLUMN ip_net_plan.used_addresses IS 'Number of used addresses in this prefix';
COMMENT ON COLUMN ip_net_plan.free_addresses IS 'Number of free addresses in this prefix';

-- add statistics to pool table
ALTER TABLE ip_net_pool ADD COLUMN member_prefixes_v4 numeric(40) DEFAULT 0;
ALTER TABLE ip_net_pool ADD COLUMN member_prefixes_v6 numeric(40) DEFAULT 0;
ALTER TABLE ip_net_pool ADD COLUMN used_prefixes_v4 numeric(40) DEFAULT 0;
ALTER TABLE ip_net_pool ADD COLUMN used_prefixes_v6 numeric(40) DEFAULT 0;
ALTER TABLE ip_net_pool ADD COLUMN total_addresses_v4 numeric(40) DEFAULT 0;
ALTER TABLE ip_net_pool ADD COLUMN total_addresses_v6 numeric(40) DEFAULT 0;
ALTER TABLE ip_net_pool ADD COLUMN used_addresses_v4 numeric(40) DEFAULT 0;
ALTER TABLE ip_net_pool ADD COLUMN used_addresses_v6 numeric(40) DEFAULT 0;
ALTER TABLE ip_net_pool ADD COLUMN free_addresses_v4 numeric(40) DEFAULT 0;
ALTER TABLE ip_net_pool ADD COLUMN free_addresses_v6 numeric(40) DEFAULT 0;
ALTER TABLE ip_net_pool ADD COLUMN free_prefixes_v4 numeric(40) DEFAULT 0;
ALTER TABLE ip_net_pool ADD COLUMN free_prefixes_v6 numeric(40) DEFAULT 0;
ALTER TABLE ip_net_pool ADD COLUMN total_prefixes_v4 numeric(40) DEFAULT 0;
ALTER TABLE ip_net_pool ADD COLUMN total_prefixes_v6 numeric(40) DEFAULT 0;

COMMENT ON COLUMN ip_net_pool.member_prefixes_v4 IS 'Number of IPv4 prefixes that are members of this pool';
COMMENT ON COLUMN ip_net_pool.member_prefixes_v6 IS 'Number of IPv6 prefixes that are members of this pool';
COMMENT ON COLUMN ip_net_pool.used_prefixes_v4 IS 'Number of IPv4 prefixes allocated from this pool';
COMMENT ON COLUMN ip_net_pool.used_prefixes_v6 IS 'Number of IPv6 prefixes allocated from this pool';
COMMENT ON COLUMN ip_net_pool.total_addresses_v4 IS 'Total number of IPv4 addresses in this pool';
COMMENT ON COLUMN ip_net_pool.total_addresses_v6 IS 'Total number of IPv6 addresses in this pool';
COMMENT ON COLUMN ip_net_pool.used_addresses_v4 IS 'Number of used IPv4 addresses in this pool';
COMMENT ON COLUMN ip_net_pool.used_addresses_v6 IS 'Number of used IPv6 addresses in this pool';
COMMENT ON COLUMN ip_net_pool.free_addresses_v4 IS 'Number of free IPv4 addresses in this pool';
COMMENT ON COLUMN ip_net_pool.free_addresses_v6 IS 'Number of free IPv6 addresses in this pool';
COMMENT ON COLUMN ip_net_pool.free_prefixes_v4 IS 'Number of potentially free IPv4 prefixes of the default assignment size';
COMMENT ON COLUMN ip_net_pool.free_prefixes_v6 IS 'Number of potentially free IPv6 prefixes of the default assignment size';
COMMENT ON COLUMN ip_net_pool.total_prefixes_v4 IS 'Potentially the total number of IPv4 child prefixes in pool. This is based on current number of childs and potential childs of the default assignment size, which is why it can vary.';
COMMENT ON COLUMN ip_net_pool.total_prefixes_v6 IS 'Potentially the total number of IPv6 child prefixes in pool. This is based on current number of childs and potential childs of the default assignment size, which is why it can vary.';

--
-- set stats for the first time
--
-- prefix stats
UPDATE ip_net_plan SET total_addresses = power(2::numeric, (CASE WHEN family(prefix) = 4 THEN 32 ELSE 128 END) - masklen(prefix));
UPDATE ip_net_plan AS inp SET used_addresses = COALESCE((SELECT SUM(total_addresses) FROM ip_net_plan AS inp2 WHERE inp2.prefix << inp.prefix AND inp2.indent = inp.indent + 1), 0);
UPDATE ip_net_plan SET free_addresses = total_addresses - used_addresses;
-- vrf stats
UPDATE ip_net_vrf SET num_prefixes_v4 = (SELECT COUNT(1) FROM ip_net_plan WHERE vrf_id = ip_net_vrf.id AND family(prefix) = 4);
UPDATE ip_net_vrf SET num_prefixes_v6 = (SELECT COUNT(1) FROM ip_net_plan WHERE vrf_id = ip_net_vrf.id AND family(prefix) = 6);
UPDATE ip_net_vrf SET total_addresses_v4 = COALESCE((SELECT SUM(total_addresses) FROM ip_net_plan WHERE vrf_id = ip_net_vrf.id AND indent = 0 AND family(prefix) = 4), 0);
UPDATE ip_net_vrf SET total_addresses_v6 = COALESCE((SELECT SUM(total_addresses) FROM ip_net_plan WHERE vrf_id = ip_net_vrf.id AND indent = 0 AND family(prefix) = 6), 0);
UPDATE ip_net_vrf SET used_addresses_v4 = COALESCE((SELECT SUM(used_addresses) FROM ip_net_plan WHERE vrf_id = ip_net_vrf.id AND indent = 0 AND family(prefix) = 4), 0);
UPDATE ip_net_vrf SET used_addresses_v6 = COALESCE((SELECT SUM(used_addresses) FROM ip_net_plan WHERE vrf_id = ip_net_vrf.id AND indent = 0 AND family(prefix) = 6), 0);
UPDATE ip_net_vrf SET free_addresses_v4 = COALESCE((SELECT SUM(free_addresses) FROM ip_net_plan WHERE vrf_id = ip_net_vrf.id AND indent = 0 AND family(prefix) = 4), 0);
UPDATE ip_net_vrf SET free_addresses_v6 = COALESCE((SELECT SUM(free_addresses) FROM ip_net_plan WHERE vrf_id = ip_net_vrf.id AND indent = 0 AND family(prefix) = 6), 0);
-- pool stats
UPDATE ip_net_pool SET member_prefixes_v4 = (SELECT COUNT(1) FROM ip_net_plan WHERE pool_id = ip_net_pool.id AND family(prefix) = 4);
UPDATE ip_net_pool SET member_prefixes_v6 = (SELECT COUNT(1) FROM ip_net_plan WHERE pool_id = ip_net_pool.id AND family(prefix) = 6);
UPDATE ip_net_pool SET used_prefixes_v4 = (SELECT COUNT(1) from ip_net_plan AS inp JOIN ip_net_plan AS inp2 ON (inp2.prefix << inp.prefix AND inp2.indent = inp.indent+1 AND family(inp.prefix) = 4) WHERE inp.pool_id = ip_net_pool.id);
UPDATE ip_net_pool SET used_prefixes_v6 = (SELECT COUNT(1) from ip_net_plan AS inp JOIN ip_net_plan AS inp2 ON (inp2.prefix << inp.prefix AND inp2.indent = inp.indent+1 AND family(inp.prefix) = 6) WHERE inp.pool_id = ip_net_pool.id);
UPDATE ip_net_pool SET total_addresses_v4 = COALESCE((SELECT SUM(total_addresses) FROM ip_net_plan WHERE pool_id = ip_net_pool.id AND family(prefix) = 4), 0);
UPDATE ip_net_pool SET total_addresses_v6 = COALESCE((SELECT SUM(total_addresses) FROM ip_net_plan WHERE pool_id = ip_net_pool.id AND family(prefix) = 6), 0);
UPDATE ip_net_pool SET used_addresses_v4 = COALESCE((SELECT SUM(used_addresses) FROM ip_net_plan WHERE pool_id = ip_net_pool.id AND family(prefix) = 4), 0);
UPDATE ip_net_pool SET used_addresses_v6 = COALESCE((SELECT SUM(used_addresses) FROM ip_net_plan WHERE pool_id = ip_net_pool.id AND family(prefix) = 6), 0);
UPDATE ip_net_pool SET free_addresses_v4 = COALESCE((SELECT SUM(free_addresses) FROM ip_net_plan WHERE pool_id = ip_net_pool.id AND family(prefix) = 4), 0);
UPDATE ip_net_pool SET free_addresses_v6 = COALESCE((SELECT SUM(free_addresses) FROM ip_net_plan WHERE pool_id = ip_net_pool.id AND family(prefix) = 6), 0);
-- TODO: implement this!
--UPDATE ip_net_pool SET free_prefixes_v4 = 
--UPDATE ip_net_pool SET free_prefixes_v6 = 
--UPDATE ip_net_pool SET total_prefixes_v4 = 
--UPDATE ip_net_pool SET total_prefixes_v6 = 

-- add pool_id index
CREATE INDEX ip_net_plan__pool_id__index ON ip_net_plan (pool_id);

-- update database schema version
COMMENT ON DATABASE %s IS 'NIPAP database - schema version: 4';
