
DROP TABLE ip_net_plan;
DROP TABLE ip_net_pool_def_prefix_len;
DROP TABLE ip_net_pool;
DROP TABLE ip_net_schema;

DROP TYPE ip_net_plan_type;
DROP TYPE priority_3step;

DROP TRIGGER trigger_ip_net_pool_prefix__iu_before ON ip_net_plan;
DROP TRIGGER trigger_ip_net_pool_prefix__iu_after ON ip_net_plan;
