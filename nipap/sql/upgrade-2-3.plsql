-- upgrade from nipap database schema version 2 to 3

CREATE UNIQUE INDEX ip_net_plan__vrf_id_prefix_type__index ON ip_net_plan (vrf_id, prefix, type);
COMMENT ON INDEX ip_net_plan__vrf_id_prefix_type__index IS 'prefix';
DROP INDEX ip_net_plan__vrf_id_prefix__index;
