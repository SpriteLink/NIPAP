--
-- SQL functions for NIPAP
--

--
-- calc_indent is an internal function that calculates the correct indentation
-- for a prefix. It is called from a trigger function on the ip_net_plan table.
--
CREATE OR REPLACE FUNCTION calc_indent(arg_schema integer, arg_prefix inet, delta integer) RETURNS bool AS $_$
DECLARE
	r record;
	current_indent integer;
BEGIN
	current_indent := (
		SELECT COUNT(*)
		FROM
			(SELECT DISTINCT inp.prefix
			FROM ip_net_plan inp
			WHERE schema = arg_schema
				AND iprange(prefix) >> iprange(arg_prefix::cidr)
			) AS a
		);

	UPDATE ip_net_plan SET indent = current_indent WHERE schema = arg_schema AND prefix = arg_prefix;
	UPDATE ip_net_plan SET indent = indent + delta WHERE schema = arg_schema AND iprange(prefix) << iprange(arg_prefix::cidr);

	RETURN true;
END;
$_$ LANGUAGE plpgsql;



--
-- find_free_prefix finds one or more prefix(es) of a certain prefix-length
-- inside a larger prefix. It is typically called by get_prefix or to return a
-- list of unused prefixes.
--

-- default to 1 prefix if no count is specified
CREATE OR REPLACE FUNCTION find_free_prefix(arg_schema integer, IN arg_prefixes inet[], arg_wanted_prefix_len integer) RETURNS SETOF inet AS $_$
BEGIN
	RETURN QUERY SELECT * FROM find_free_prefix(arg_schema, arg_prefixes, arg_wanted_prefix_len, 1) AS prefix;
END;
$_$ LANGUAGE plpgsql;

-- full function
CREATE OR REPLACE FUNCTION find_free_prefix(arg_schema integer, IN arg_prefixes inet[], arg_wanted_prefix_len integer, arg_count integer) RETURNS SETOF inet AS $_$
DECLARE
	i_family integer;
	i_found integer;
	p int;
	search_prefix inet;
	current_prefix inet;
	max_prefix_len integer;
	covering_prefix inet;
BEGIN
	covering_prefix := NULL;
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

			-- avoid prefixes larger than the current_prefix but inside our search_prefix
			covering_prefix := (SELECT prefix FROM ip_net_plan WHERE schema = arg_schema AND iprange(prefix) >>= iprange(current_prefix::cidr) AND iprange(prefix) << iprange(search_prefix::cidr) ORDER BY masklen(prefix) ASC LIMIT 1);
			IF covering_prefix IS NOT NULL THEN
				SELECT set_masklen(broadcast(covering_prefix) + 1, arg_wanted_prefix_len) INTO current_prefix;
				CONTINUE;
			END IF;
			-- prefix must not contain any breakouts, that would mean it's not empty, ie not free
			IF EXISTS (SELECT 1 FROM ip_net_plan WHERE schema = arg_schema AND iprange(prefix) <<= iprange(current_prefix::cidr)) THEN
				SELECT broadcast(current_prefix) + 1 INTO current_prefix;
				CONTINUE;
			END IF;

			-- while the following two tests are family agnostic, they use
			-- functions and so are not indexed
			-- TODO: should they be indexed?

			IF ((i_family = 4 AND masklen(search_prefix) < 31) OR i_family = 6 AND masklen(search_prefix) < 127)THEN
				IF (set_masklen(network(search_prefix), max_prefix_len) = current_prefix) THEN
					SELECT broadcast(current_prefix) + 1 INTO current_prefix;
					CONTINUE;
				END IF;
				IF (set_masklen(broadcast(search_prefix), max_prefix_len) = current_prefix) THEN
					SELECT broadcast(current_prefix) + 1 INTO current_prefix;
					CONTINUE;
				END IF;
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



--
-- get_prefix provides a convenient and MVCC-proof way of getting the next
-- available prefix from another prefix.
--
CREATE OR REPLACE FUNCTION get_prefix(arg_schema integer, IN arg_prefixes inet[], arg_wanted_prefix_len integer) RETURNS inet AS $_$
DECLARE
	p inet;
BEGIN
	LOOP
		-- get a prefix
		SELECT prefix INTO p FROM find_free_prefix(arg_schema, arg_prefixes, arg_wanted_prefix_len) AS prefix;

		BEGIN
			INSERT INTO ip_net_plan (schema, prefix) VALUES (arg_schema, p);
			RETURN p;
		EXCEPTION WHEN unique_violation THEN
			-- Loop and try to find a new prefix
		END;

	END LOOP;
END;
$_$ LANGUAGE plpgsql;



--
-- Trigger function to keep data consistent in the ip_net_plan table with
-- regards to prefix type and similar. This function handles INSERTs and
-- UPDATEs.
--
CREATE OR REPLACE FUNCTION tf_ip_net_prefix_iu_before() RETURNS trigger AS $_$
DECLARE
	parent RECORD;
	child RECORD;
	i_max_pref_len integer;
BEGIN
	-- this is a shortcut to avoid running the rest of this trigger as it
	-- can be fairly costly performance wise
	--
	-- sanity checking is done on 'type' and derivations of 'prefix' so if
	-- those stay the same, we don't need to run the rest of the sanity
	-- checks.
	IF TG_OP = 'UPDATE' THEN
		-- we need to nest cause plpgsql is stupid :(
		IF OLD.type = NEW.type AND OLD.prefix = NEW.prefix THEN
			RETURN NEW;
		END IF;
	END IF;


	i_max_pref_len := 32;
	IF family(NEW.prefix) = 6 THEN
		i_max_pref_len := 128;
	END IF;
	-- contains the parent prefix
	SELECT * INTO parent FROM ip_net_plan WHERE schema = NEW.schema AND iprange(prefix) >> iprange(NEW.prefix) ORDER BY masklen(prefix) DESC LIMIT 1;

	-- check that type is correct on insert and update
	IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
		IF NEW.type = 'host' THEN
			IF masklen(NEW.prefix) != i_max_pref_len THEN
				RAISE EXCEPTION '1200:Prefix of type host must have all bits set in netmask';
			END IF;
			IF parent.prefix IS NULL THEN
				RAISE EXCEPTION '1200:Prefix of type host must have a parent (covering) prefix of type assignment';
			END IF;
			IF parent.type != 'assignment' THEN
				RAISE EXCEPTION '1200:Parent prefix (%) is of type % but must be of type ''assignment''', parent.prefix, parent.type;
			END IF;
			NEW.display_prefix := set_masklen(NEW.prefix::inet, masklen(parent.prefix));
		ELSIF NEW.type = 'assignment' THEN
			IF parent.type IS NULL THEN
				-- all good
			ELSIF parent.type != 'reservation' THEN
				RAISE EXCEPTION '1200:Parent prefix (%) is of type % but must be of type ''reservation''', parent.prefix, parent.type;
			END IF;

			-- also check that the new prefix does not have any childs other than hosts
			--
			-- it is practically feasible that it would even have a child of
			-- type 'host', since it would require a parent of type assignment,
			-- but we don't need to limit the consistency check here if we ever
			-- are to make changes in the future
			IF EXISTS (SELECT * FROM ip_net_plan WHERE schema = NEW.schema AND type != 'host' AND iprange(prefix) << iprange(NEW.prefix) LIMIT 1) THEN
				RAISE EXCEPTION '1200:Prefix of type ''assignment'' must not have any subnets other than of type ''host''';
			END IF;
			NEW.display_prefix := NEW.prefix;
		ELSIF NEW.type = 'reservation' THEN
			IF parent.type IS NULL THEN
				-- all good
			ELSIF parent.type != 'reservation' THEN
				RAISE EXCEPTION '1200:Parent prefix (%) is of type % but must be of type ''reservation''', parent.prefix, parent.type;
			END IF;
			NEW.display_prefix := NEW.prefix;
		ELSE
			RAISE EXCEPTION 'Unknown prefix type';
		END IF;
	END IF;

	-- only allow specific cases for changing the type of prefix
	IF TG_OP = 'UPDATE' THEN
		IF (OLD.type = 'reservation' AND NEW.type = 'assignment') OR (OLD.type = 'assignment' AND new.type = 'reservation') THEN
			-- don't allow any childs, since they would automatically be of the
			-- wrong type, ie inconsistent data
			IF EXISTS (SELECT 1 FROM ip_net_plan WHERE schema = NEW.schema AND iprange(prefix) << iprange(NEW.prefix)) THEN
				RAISE EXCEPTION '1200:Changing from type ''%'' to ''%'' requires there to be no child prefixes.', OLD.type, NEW.type;
			END IF;
		ELSE
			IF OLD.type != NEW.type THEN
				-- FIXME: better exception code
				RAISE EXCEPTION '1200:Changing type is disallowed';
			END IF;
		END IF;
	END IF;

	RETURN NEW;
END;
$_$ LANGUAGE plpgsql;


--
-- Trigger function to keep data consistent in the ip_net_plan table with
-- regards to prefix type and similar. This function handles DELETE operations.
--
CREATE OR REPLACE FUNCTION tf_ip_net_prefix_d_before() RETURNS trigger AS $_$
BEGIN
	-- prevent certain deletes to maintain DB integrity
	IF TG_OP = 'DELETE' THEN
		-- if an assignment contains hosts, we block the delete
		IF OLD.type = 'assignment' THEN
			-- contains one child prefix
			-- FIXME: optimize with this, what is improvement?
			-- IF (SELECT COUNT(1) FROM ip_net_plan WHERE prefix << OLD.prefix LIMIT 1) > 0 THEN
			IF (SELECT COUNT(1) FROM ip_net_plan WHERE prefix << OLD.prefix AND schema = OLD.schema) > 0 THEN
				RAISE EXCEPTION '1200:Disallowed delete, prefix (%) contains hosts.', OLD.prefix;
			END IF;
		END IF;
		-- everything else is allowed
	END IF;

	RETURN OLD;
END;
$_$ LANGUAGE plpgsql;


--
-- Trigger function to make update the indent level when adding or removing
-- prefixes.
--
CREATE OR REPLACE FUNCTION tf_ip_net_prefix_family_after() RETURNS trigger AS $$
DECLARE
	r RECORD;
BEGIN
	IF TG_OP = 'DELETE' THEN
		PERFORM calc_indent(OLD.schema, OLD.prefix, -1);
	ELSIF TG_OP = 'INSERT' THEN
		PERFORM calc_indent(NEW.schema, NEW.prefix, 1);
	ELSE
		-- nothing!
	END IF;
	RETURN NEW;
END;
$$ LANGUAGE plpgsql;
