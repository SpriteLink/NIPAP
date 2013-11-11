--
-- Upgrade from NIPAP database schema version 2 to 3
--

-- add customer_id 
ALTER TABLE ip_net_plan ADD COLUMN customer_id text;
COMMENT ON COLUMN ip_net_plan.customer_id IS 'Customer Identifier';

-- update database schema version
COMMENT ON DATABASE nipap IS 'NIPAP database - schema version: 3';
