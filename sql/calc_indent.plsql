

CREATE OR REPLACE FUNCTION calc_indent(arg_schema integer, arg_prefix inet, delta integer) RETURNS bool AS $_$
DECLARE
	r record;
	current_indent integer;
BEGIN
	IF family(arg_prefix) = 4 THEN

		current_indent := (
			SELECT COUNT(*)
			FROM
				(SELECT DISTINCT inp.prefix
				FROM ip_net_plan inp
				WHERE schema = arg_schema
					AND family(prefix)=4
					AND ip4r(CASE WHEN family(prefix) = 4 THEN prefix ELSE NULL::cidr END) >> ip4r(arg_prefix::cidr)
				) AS a
			);

		UPDATE ip_net_plan SET indent = current_indent WHERE schema = arg_schema AND prefix = arg_prefix;
		UPDATE ip_net_plan SET indent = indent + delta WHERE schema = arg_schema AND family(prefix) = 4 AND ip4r(CASE WHEN family(prefix) = 4 THEN prefix ELSE NULL::cidr END) << ip4r(arg_prefix::cidr);

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
