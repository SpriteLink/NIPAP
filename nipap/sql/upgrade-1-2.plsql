--
-- Upgrade from NIPAP database schema version 1 to 2
--

-- rename trigger function
DROP TRIGGER trigger_ip_net_plan_prefix__iu_after ON ip_net_plan;
CREATE TRIGGER trigger_ip_net_plan_prefix__iu_after
	AFTER DELETE OR INSERT OR UPDATE
	ON ip_net_plan
	FOR EACH ROW
	EXECUTE PROCEDURE tf_ip_net_prefix_after();

-- add children
ALTER TABLE ip_net_plan ADD COLUMN vlan integer;
COMMENT ON COLUMN ip_net_plan.vlan IS 'Number of direct sub-prefixes';

-- vlan support
ALTER TABLE ip_net_plan ADD COLUMN vlan integer;
COMMENT ON COLUMN ip_net_plan.vlan IS 'VLAN ID';

-- add tags
ALTER TABLE ip_net_plan ADD COLUMN tags text[] DEFAULT '{}';
ALTER TABLE ip_net_plan ADD COLUMN inherited_tags text[] DEFAULT '{}';
COMMENT ON COLUMN ip_net_plan.tags IS 'Tags associated with the prefix';
COMMENT ON COLUMN ip_net_plan.inherited_tags IS 'Tags inherited from parent (and grand-parent) prefixes';

-- timestamp columns
ALTER TABLE ip_net_plan ADD COLUMN added timestamp with time zone DEFAULT NOW();
ALTER TABLE ip_net_plan ADD COLUMN last_modified timestamp with time zone DEFAULT NOW();
COMMENT ON COLUMN ip_net_plan.added IS 'The date and time when the prefix was added';
COMMENT ON COLUMN ip_net_plan.last_modified IS 'The date and time when the prefix was last modified';
-- set added column to timestamp of first audit entry
UPDATE ip_net_plan inp SET added = (SELECT timestamp FROM ip_net_log inl WHERE inl.prefix_id = inp.id ORDER BY inl.timestamp DESC LIMIT 1);

