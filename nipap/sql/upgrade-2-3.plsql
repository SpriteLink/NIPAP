--
-- Upgrade from NIPAP database schema version 2 to 3
--

-- add customer_id 
ALTER TABLE ip_net_plan ADD COLUMN customer_id text;
COMMENT ON COLUMN ip_net_plan.customer_id IS 'Customer Identifier';

-- update database schema version
COMMENT ON DATABASE %s IS 'NIPAP database - schema version: 3';

CREATE OR REPLACE FUNCTION update_children() RETURNS boolean AS $_$
DECLARE
	r record;
	num_children integer;
BEGIN
	FOR r IN (SELECT * FROM ip_net_plan) LOOP
		num_children := (SELECT COALESCE((
			SELECT COUNT(1)
			FROM ip_net_plan
			WHERE vrf_id = r.vrf_id
				AND prefix << r.prefix
				AND indent = r.indent+1), 0));
		UPDATE ip_net_plan SET children = num_children WHERE id = r.id;
	END LOOP;

	RETURN true;
END;
$_$ LANGUAGE plpgsql;

SELECT update_children();
DROP FUNCTION update_children();
