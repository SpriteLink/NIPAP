

CREATE OR REPLACE FUNCTION calc_indent(arg_schema integer, arg_prefix inet) RETURNS bool AS $_$
DECLARE
	r record;
BEGIN
	IF family(arg_prefix) = 4 THEN
		FOR r IN SELECT (SELECT COUNT(*) FROM (SELECT DISTINCT network(inp2.prefix) FROM ip_net_plan inp2 WHERE schema = arg_schema AND family=4 AND network(inp2.prefix) >> inp.prefix) AS a) AS calc_indent, inp.prefix, inp.indent FROM ip_net_plan inp WHERE family=4 AND inp.prefix <<= arg_prefix LOOP
			IF r.calc_indent != r.indent OR r.indent IS NULL THEN
				UPDATE ip_net_plan SET indent = r.calc_indent WHERE prefix = r.prefix;
			END IF;
		END LOOP;
	ELSE
		FOR r IN SELECT (SELECT COUNT(*) FROM (SELECT DISTINCT network(inp2.prefix) FROM ip_net_plan inp2 WHERE schema = arg_schema AND family=6 AND network(inp2.prefix) >> inp.prefix) AS a) AS calc_indent, inp.prefix, inp.indent FROM ip_net_plan inp WHERE family=6 AND inp.prefix <<= arg_prefix LOOP
			IF r.calc_indent != r.indent OR r.indent IS NULL THEN
				UPDATE ip_net_plan SET indent = r.calc_indent WHERE prefix = r.prefix;
			END IF;
		END LOOP;
	END IF;
	RETURN true;
END;
$_$ LANGUAGE plpgsql;
