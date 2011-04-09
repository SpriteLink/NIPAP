CREATE OR REPLACE FUNCTION get_ip(arg_family integer, arg_from_prefix cidr, arg_from_pool text, arg_prefix_len integer, arg_status ip_net_plan_status, arg_default_status ip_net_plan_status, arg_pool integer, arg_description text, arg_comment text, arg_node integer) RETURNS inet AS $$
DECLARE
	new_net inet;
	r record;
	current_prefix inet;
	wanted_prefix_len integer;
	max_prefix_len integer;
	pool_family integer;
	i_status ip_net_plan_status;
	i_default_status ip_net_plan_status;
	i_pool_id integer;
	i_family integer;
	i_parent_prefix inet;
BEGIN
	--
	-- some sanity checking
	--
	IF arg_from_prefix IS NULL AND arg_from_pool IS NULL THEN
		RAISE EXCEPTION 'Either arg_from_prefix or arg_from_pool must be specified!';
	END IF;

	IF arg_from_prefix IS NOT NULL THEN
		IF (SELECT status FROM ip_net_plan WHERE prefix=arg_from_prefix) = 'host' THEN
			RAISE EXCEPTION 'Cannot add child prefix where parent has type "host"';
		END IF;
		i_family := family(arg_from_prefix);
		SELECT default_status INTO i_status FROM ip_net_plan WHERE prefix=arg_from_prefix;
	ELSE
		i_family := arg_family;
	END IF;

	--
	IF NOT (i_family = 4 OR i_family = 6) THEN
		RAISE EXCEPTION '% is not a known address family (must be 4 or 6)', i_family;
	END IF;

	--
	IF arg_node IS NOT NULL AND NOT EXISTS (SELECT 1 FROM node WHERE id=arg_node) THEN
		RAISE EXCEPTION 'Non-existing node specified!';
	END IF;

	--
	IF i_family = 4 THEN
		max_prefix_len := 32;
	ELSE
		max_prefix_len := 128;
	END IF;

	-- set status for the prefix
	-- we take arg_status if that is provided
	-- if not, either the default_status from the parent prefix/pool, depending what is provided
	IF i_status IS NULL THEN
		SELECT COALESCE(arg_status, (SELECT default_status FROM ip_net_plan WHERE prefix=arg_from_prefix), (SELECT default_status FROM ip_net_pool WHERE family=i_family AND name=arg_from_pool), 'assignment') INTO i_status;
	END IF;

	--
	SELECT COALESCE(arg_prefix_len, (CASE WHEN i_status = 'host' THEN max_prefix_len ELSE NULL END), (SELECT default_prefix_length FROM ip_net_plan WHERE prefix=arg_from_prefix), (SELECT default_prefix_length FROM ip_net_pool WHERE family=i_family AND name=arg_from_pool)) INTO wanted_prefix_len;


	-- get the parent pool id and store for later use
	SELECT id INTO i_pool_id FROM ip_net_pool WHERE family=i_family AND name=arg_from_pool;

	-- if you don't get this.. it's ok ;)
	FOR r IN SELECT prefix FROM ip_net_plan LEFT OUTER JOIN ip_net_pool ON (ip_net_plan.pool=ip_net_pool.id) WHERE ip_net_plan.family=i_family AND (ip_net_pool.name=arg_from_pool OR ip_net_plan.prefix=arg_from_prefix) ORDER BY ip_net_plan.prefix ASC LOOP

		-- should this really be here? ;)
		IF (masklen(r.prefix) > wanted_prefix_len) THEN
			CONTINUE;
		END IF;

		SELECT set_masklen(r.prefix, wanted_prefix_len) INTO current_prefix;

		WHILE set_masklen(current_prefix, masklen(r.prefix)) <= broadcast(r.prefix) LOOP

			IF NOT EXISTS (SELECT 1 FROM ip_net_plan WHERE (pool != i_pool_id OR prefix != arg_from_prefix) AND (prefix<<=current_prefix)) THEN
				-- prefix must not contain any breakouts, that would mean it's not empty, ie not free
				IF EXISTS (SELECT 1 FROM ip_net_plan WHERE prefix <<= current_prefix) THEN
					SELECT broadcast(current_prefix) + 1 INTO current_prefix;
					CONTINUE;
				END IF;
				IF current_prefix IS NULL THEN
					SELECT broadcast(current_prefix) + 1 INTO current_prefix;
					CONTINUE;
				END IF;
				IF (set_masklen(network(r.prefix), max_prefix_len) = current_prefix) THEN
					SELECT broadcast(current_prefix) + 1 INTO current_prefix;
					CONTINUE;
				END IF;
				IF (set_masklen(broadcast(r.prefix), max_prefix_len) = current_prefix) THEN
					SELECT broadcast(current_prefix) + 1 INTO current_prefix;
					CONTINUE;
				END IF;
				IF EXISTS (SELECT 1 FROM ip_net_plan WHERE prefix=current_prefix) THEN
					SELECT broadcast(current_prefix) + 1 INTO current_prefix;
					CONTINUE;
				END IF;

				SELECT prefix INTO i_parent_prefix FROM ip_net_plan WHERE prefix >> current_prefix ORDER BY masklen(prefix) DESC LIMIT 1;
				IF i_family = 6 AND i_status = 'assignment' AND host(current_prefix) = host(i_parent_prefix) THEN
					SELECT broadcast(current_prefix) + 1 INTO current_prefix;
					CONTINUE;
				END IF;

				INSERT INTO ip_net_plan (prefix, status, pool, description, comment, node, default_prefix_length) VALUES (current_prefix, i_status, arg_pool, arg_description, arg_comment, arg_node, max_prefix_len);
				RETURN current_prefix;

			END IF;
			SELECT broadcast(current_prefix) + 1 INTO current_prefix;

		END LOOP;
	END LOOP;

	RETURN NULL;
END;
$$ LANGUAGE plpgsql;
