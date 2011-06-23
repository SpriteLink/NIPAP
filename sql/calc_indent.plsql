

CREATE OR REPLACE FUNCTION calc_indent(arg_schema integer, arg_prefix inet) RETURNS bool AS $_$
DECLARE
	r record;
BEGIN
	IF family(arg_prefix) = 4 THEN
		FOR r IN SELECT (SELECT COUNT(*) FROM (SELECT DISTINCT inp2.prefix FROM ip_net_plan inp2 WHERE schema = arg_schema AND family(prefix)=4 AND ip4r(CASE WHEN family(inp2.prefix) = 4 THEN inp2.prefix ELSE NULL::cidr END) >> ip4r(inp.prefix)) AS a) AS calc_indent, inp.prefix, inp.indent FROM ip_net_plan inp WHERE family(prefix)=4 AND ip4r(CASE WHEN family(prefix) = 4 THEN prefix ELSE NULL::cidr END) <<= ip4r(arg_prefix::cidr) LOOP
			IF r.calc_indent != r.indent OR r.indent IS NULL THEN
				UPDATE ip_net_plan SET indent = r.calc_indent WHERE prefix = r.prefix;
			END IF;
		END LOOP;
	ELSE
		FOR r IN SELECT (SELECT COUNT(*) FROM (SELECT DISTINCT inp2.prefix FROM ip_net_plan inp2 WHERE schema = arg_schema AND family(prefix)=6 AND inp2.prefix >> inp.prefix) AS a) AS calc_indent, inp.prefix, inp.indent FROM ip_net_plan inp WHERE family(prefix)=6 AND inp.prefix <<= arg_prefix LOOP
			IF r.calc_indent != r.indent OR r.indent IS NULL THEN
				UPDATE ip_net_plan SET indent = r.calc_indent WHERE prefix = r.prefix;
			END IF;
		END LOOP;
	END IF;
	RETURN true;
END;
$_$ LANGUAGE plpgsql;
