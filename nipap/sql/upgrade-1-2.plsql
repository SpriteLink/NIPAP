--
-- Upgrade from NIPAP database schema version 1 to 2
--

-- add tags
ALTER TABLE ip_net_plan ADD COLUMN vlan integer;
ALTER TABLE ip_net_plan ADD COLUMN tags text[] DEFAULT '{}';
ALTER TABLE ip_net_plan ADD COLUMN inherited_tags text[] DEFAULT '{}';
