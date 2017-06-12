--
-- Upgrade from NIPAP database schema version 5 to 6
--

CREATE EXTENSION IF NOT EXISTS citext;

ALTER TABLE ip_net_vrf ALTER COLUMN name SET NOT NULL;

DROP INDEX ip_net_vrf__name__index;
CREATE UNIQUE INDEX ip_net_vrf__name__index ON ip_net_vrf (lower(name)) WHERE name IS NOT NULL;

ALTER TABLE ip_net_pool DROP CONSTRAINT ip_net_pool_name_key;
CREATE UNIQUE INDEX ip_net_pool__name__index ON ip_net_pool (lower(name));

-- update database schema version
COMMENT ON DATABASE %s IS 'NIPAP database - schema version: 6';
