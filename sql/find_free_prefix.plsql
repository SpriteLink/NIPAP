
CREATE OR REPLACE FUNCTION find_free_prefix(arg_schema integer, IN arg_prefixes inet[], arg_wanted_prefix_len integer) RETURNS SETOF inet AS $_$
BEGIN
	RETURN QUERY SELECT * FROM find_free_prefix(arg_schema, arg_prefixes, arg_wanted_prefix_len, 1) AS prefix;
END;
$_$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION find_free_prefix(arg_schema integer, IN arg_prefixes inet[], arg_wanted_prefix_len integer, arg_count integer) RETURNS SETOF inet AS $_$
DECLARE
	i_family integer;
	i_found integer;
	p int;
	search_prefix inet;
	current_prefix inet;
	max_prefix_len integer;
BEGIN
	-- sanity checking
	-- make sure all provided search_prefixes are of same family
	FOR p IN SELECT generate_subscripts(arg_prefixes, 1) LOOP
		IF i_family IS NULL THEN
			i_family := family(arg_prefixes[p]);
		END IF;

		IF i_family != family(arg_prefixes[p]) THEN
			RAISE EXCEPTION 'Search prefixes of inconsistent address-family provided';
		END IF;
	END LOOP;

	-- determine maximum prefix-length for our family
	IF i_family = 4 THEN
		max_prefix_len := 32;
	ELSE
		max_prefix_len := 128;
	END IF;

	-- the wanted prefix length cannot be more than 32 for ipv4 or more than 128 for ipv6
	IF arg_wanted_prefix_len > max_prefix_len THEN
		RAISE EXCEPTION 'Requested prefix-length exceeds max prefix-length %', max_prefix_len;
	END IF;
	--

	i_found := 0;

	-- loop through our search list of prefixes
	FOR p IN SELECT generate_subscripts(arg_prefixes, 1) LOOP
		-- save the current prefix in which we are looking for a candidate
		search_prefix := arg_prefixes[p];

		IF (masklen(search_prefix) > arg_wanted_prefix_len) THEN
			CONTINUE;
		END IF;

		SELECT set_masklen(search_prefix, arg_wanted_prefix_len) INTO current_prefix;

		-- we step through our search_prefix in steps of the wanted prefix
		-- length until we are beyond the broadcast size, ie end of our
		-- search_prefix
		WHILE set_masklen(current_prefix, masklen(search_prefix)) <= broadcast(search_prefix) LOOP
			-- tests put in order of speed, fastest one first

			-- the following are address family agnostic
			IF current_prefix IS NULL THEN
				SELECT broadcast(current_prefix) + 1 INTO current_prefix;
				CONTINUE;
			END IF;
			IF EXISTS (SELECT 1 FROM ip_net_plan WHERE schema=arg_schema AND prefix=current_prefix) THEN
				SELECT broadcast(current_prefix) + 1 INTO current_prefix;
				CONTINUE;
			END IF;

			-- We unfortunately need to use the ip4r index as we cannot reach
			-- any reasonable speeds without it this means we need to split our
			-- checks based on if we are searching for an IPv4 or IPv6 prefix
			IF i_family = 4 THEN
				-- avoid prefixes larger than the current_prefix but inside our search_prefix
				IF EXISTS (SELECT 1 FROM ip_net_plan WHERE schema = arg_schema AND family(prefix) = 4 AND ip4r(CASE WHEN family(prefix) = 4 THEN prefix ELSE NULL::cidr END) >>= ip4r(current_prefix::cidr) AND ip4r(CASE WHEN family(prefix) = 4 THEN prefix ELSE NULL::cidr END) << ip4r(search_prefix::cidr)) THEN
					SELECT broadcast(current_prefix) + 1 INTO current_prefix;
					CONTINUE;
				END IF;
				-- prefix must not contain any breakouts, that would mean it's not empty, ie not free
				IF EXISTS (SELECT 1 FROM ip_net_plan WHERE schema = arg_schema AND family(prefix) = 4 AND ip4r(CASE WHEN family(prefix) = 4 THEN prefix ELSE NULL::cidr END) <<= ip4r(current_prefix::cidr)) THEN
					SELECT broadcast(current_prefix) + 1 INTO current_prefix;
					CONTINUE;
				END IF;
			ELSE
				-- avoid prefixes larger than the current_prefix but inside our search_prefix
				IF EXISTS (SELECT 1 FROM ip_net_plan WHERE schema = arg_schema AND prefix >>= current_prefix AND prefix << search_prefix) THEN
					SELECT broadcast(current_prefix) + 1 INTO current_prefix;
					CONTINUE;
				END IF;
				-- prefix must not contain any breakouts, that would mean it's not empty, ie not free
				IF EXISTS (SELECT 1 FROM ip_net_plan WHERE schema = arg_schema AND prefix <<= current_prefix) THEN
					SELECT broadcast(current_prefix) + 1 INTO current_prefix;
					CONTINUE;
				END IF;
			END IF;

			-- while the following two tests are family agnostic, they use
			-- functions and so are not indexed
			-- TODO: should they be indexed?

			IF (set_masklen(network(search_prefix), max_prefix_len) = current_prefix) THEN
				SELECT broadcast(current_prefix) + 1 INTO current_prefix;
				CONTINUE;
			END IF;
			IF (set_masklen(broadcast(search_prefix), max_prefix_len) = current_prefix) THEN
				SELECT broadcast(current_prefix) + 1 INTO current_prefix;
				CONTINUE;
			END IF;

			RETURN NEXT current_prefix;

			i_found := i_found + 1;
			IF i_found >= arg_count THEN
				RETURN;
			END IF;

			current_prefix := broadcast(current_prefix) + 1;
		END LOOP;

	END LOOP;

	RETURN;

END;
$_$ LANGUAGE plpgsql;
