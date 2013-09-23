
DROP TABLE ip_net_log;
DROP TABLE ip_net_plan;
DROP TABLE ip_net_pool;
DROP TABLE ip_net_vrf;
DROP TABLE ip_net_asn;

DROP TYPE ip_net_plan_type CASCADE;
DROP TYPE priority_3step CASCADE;

DROP FUNCTION calc_indent(arg_vrf integer, arg_prefix inet, delta integer);
DROP FUNCTION array_undup(ANYARRAY);
DROP FUNCTION calc_tags(arg_vrf integer, arg_prefix inet);
DROP FUNCTION find_free_prefix(arg_vrf integer, IN arg_prefixes inet[], arg_wanted_prefix_len integer);
DROP FUNCTION find_free_prefix(arg_vrf integer, IN arg_prefixes inet[], arg_wanted_prefix_len integer, arg_count integer);
DROP FUNCTION get_prefix(arg_vrf integer, IN arg_prefixes inet[], arg_wanted_prefix_len integer);
DROP FUNCTION vrf_rt_order(arg_rt text);
DROP FUNCTION tf_ip_net_vrf_iu_before();
DROP FUNCTION tf_ip_net_vrf_d_before();
DROP FUNCTION tf_ip_net_prefix_iu_before();
DROP FUNCTION tf_ip_net_prefix_d_before();
DROP FUNCTION tf_ip_net_prefix_after();
