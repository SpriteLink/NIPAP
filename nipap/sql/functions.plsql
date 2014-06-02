--
-- SQL functions for NIPAP
--

--
-- calc_indent is an internal function that calculates the correct indentation
-- for a prefix. It is called from a trigger function on the ip_net_plan table.
--
CREATE OR REPLACE FUNCTION calc_indent(arg_vrf integer, arg_prefix inet, delta integer) RETURNS bool AS $_$
DECLARE
	r record;
	current_indent integer;
BEGIN
	current_indent := (
		SELECT COUNT(*)
		FROM
			(SELECT DISTINCT inp.prefix
			FROM ip_net_plan inp
			WHERE vrf_id = arg_vrf
				AND iprange(prefix) >> iprange(arg_prefix::cidr)
			) AS a
		);

	UPDATE ip_net_plan SET indent = current_indent WHERE vrf_id = arg_vrf AND prefix = arg_prefix;
	UPDATE ip_net_plan SET indent = indent + delta WHERE vrf_id = arg_vrf AND iprange(prefix) << iprange(arg_prefix::cidr);

	RETURN true;
END;
$_$ LANGUAGE plpgsql;


--
-- Remove duplicate elements from an array
--
CREATE OR REPLACE FUNCTION array_undup(ANYARRAY) RETURNS ANYARRAY AS $_$
	SELECT ARRAY(
		SELECT DISTINCT $1[i]
		FROM generate_series(
			array_lower($1,1),
			array_upper($1,1)
			) AS i
		);
$_$ LANGUAGE SQL;


--
-- calc_tags is an internal function that calculates the inherited_tags
-- from parent prefixes to its children. It is called from a trigger function
-- on the ip_net_plan table.
--
CREATE OR REPLACE FUNCTION calc_tags(arg_vrf integer, arg_prefix inet) RETURNS bool AS $_$
DECLARE
	i_indent integer;
	new_inherited_tags text[];
BEGIN
	i_indent := (
		SELECT indent+1
		FROM ip_net_plan
		WHERE vrf_id = arg_vrf
			AND prefix = arg_prefix
		);
	-- set default if we don't have a parent prefix
	IF i_indent IS NULL THEN
		i_indent := 0;
	END IF;

	new_inherited_tags := (
		SELECT array_undup(array_cat(inherited_tags, tags))
		FROM ip_net_plan
		WHERE vrf_id = arg_vrf
			AND prefix = arg_prefix
		);
	-- set default if we don't have a parent prefix
	IF new_inherited_tags IS NULL THEN
		new_inherited_tags := '{}';
	END IF;

	UPDATE ip_net_plan SET inherited_tags = new_inherited_tags WHERE vrf_id = arg_vrf AND iprange(prefix ) << iprange(arg_prefix::cidr) AND indent = i_indent;

	RETURN true;
END;
$_$ LANGUAGE plpgsql;


--
-- find_free_prefix finds one or more prefix(es) of a certain prefix-length
-- inside a larger prefix. It is typically called by get_prefix or to return a
-- list of unused prefixes.
--

-- default to 1 prefix if no count is specified
CREATE OR REPLACE FUNCTION find_free_prefix(arg_vrf integer, IN arg_prefixes inet[], arg_wanted_prefix_len integer) RETURNS SETOF inet AS $_$
BEGIN
	RETURN QUERY SELECT * FROM find_free_prefix(arg_vrf, arg_prefixes, arg_wanted_prefix_len, 1) AS prefix;
END;
$_$ LANGUAGE plpgsql;

-- full function
CREATE OR REPLACE FUNCTION find_free_prefix(arg_vrf integer, IN arg_prefixes inet[], arg_wanted_prefix_len integer, arg_count integer) RETURNS SETOF inet AS $_$
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
			IF EXISTS (SELECT 1 FROM ip_net_plan WHERE vrf_id = arg_vrf AND prefix = current_prefix) THEN
				SELECT broadcast(current_prefix) + 1 INTO current_prefix;
				CONTINUE;
			END IF;

			-- avoid prefixes larger than the current_prefix but inside our search_prefix
			covering_prefix := (SELECT prefix FROM ip_net_plan WHERE vrf_id = arg_vrf AND iprange(prefix) >>= iprange(current_prefix::cidr) AND iprange(prefix) << iprange(search_prefix::cidr) ORDER BY masklen(prefix) ASC LIMIT 1);
			IF covering_prefix IS NOT NULL THEN
				SELECT set_masklen(broadcast(covering_prefix) + 1, arg_wanted_prefix_len) INTO current_prefix;
				CONTINUE;
			END IF;

			-- prefix must not contain any breakouts, that would mean it's not empty, ie not free
			IF EXISTS (SELECT 1 FROM ip_net_plan WHERE vrf_id = arg_vrf AND iprange(prefix) <<= iprange(current_prefix::cidr)) THEN
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
CREATE OR REPLACE FUNCTION get_prefix(arg_vrf integer, IN arg_prefixes inet[], arg_wanted_prefix_len integer) RETURNS inet AS $_$
DECLARE
	p inet;
BEGIN
	LOOP
		-- get a prefix
		SELECT prefix INTO p FROM find_free_prefix(arg_vrf, arg_prefixes, arg_wanted_prefix_len) AS prefix;

		BEGIN
			INSERT INTO ip_net_plan (vrf_id, prefix) VALUES (arg_vrf, p);
			RETURN p;
		EXCEPTION WHEN unique_violation THEN
			-- Loop and try to find a new prefix
		END;

	END LOOP;
END;
$_$ LANGUAGE plpgsql;



--
-- Helper to sort VRF RTs
--
-- RTs are tricky to sort since they exist in two formats and have the classic
-- sorted-as-string-problem;
--
--      199:456
--     1234:456
--  1.3.3.7:456
--
CREATE OR REPLACE FUNCTION vrf_rt_order(arg_rt text) RETURNS bigint AS $_$
DECLARE
	part_one text;
	part_two text;
	ip text;
BEGIN
	BEGIN
		part_one := split_part(arg_rt, ':', 1)::bigint;
	EXCEPTION WHEN others THEN
		ip := split_part(arg_rt, ':', 1);
		part_one := (split_part(ip, '.', 1)::bigint << 24) +
					(split_part(ip, '.', 2)::bigint << 16) +
					(split_part(ip, '.', 3)::bigint << 8) +
					(split_part(ip, '.', 4)::bigint);
	END;

	part_two := split_part(arg_rt, ':', 2);

	RETURN (part_one::bigint << 32) + part_two::bigint;
END;
$_$ LANGUAGE plpgsql IMMUTABLE STRICT;



--
-- Trigger function to validate VRF input, prominently the RT attribute which
-- needs to follow the allowed formats
--
CREATE OR REPLACE FUNCTION tf_ip_net_vrf_iu_before() RETURNS trigger AS $_$
DECLARE
	rt_part_one text;
	rt_part_two text;
	ip text;
BEGIN
	-- don't allow setting an RT for VRF id 0
	IF NEW.id = 0 THEN
		IF NEW.rt IS NOT NULL THEN
			RAISE EXCEPTION 'Invalid input for column rt, must be NULL for VRF id 0';
		END IF;
	ELSE -- make sure all VRF except for VRF id 0 has a proper RT
		-- make sure we only have two fields delimited by a colon
		IF (SELECT COUNT(1) FROM regexp_matches(NEW.rt, '(:)', 'g')) != 1 THEN
			RAISE EXCEPTION 'Invalid input for column rt, should be ASN:id (123:456) or IP:id (1.3.3.7:456)';
		END IF;

		-- check first part
		BEGIN
			-- either it's a integer (AS number)
			rt_part_one := split_part(NEW.rt, ':', 1)::bigint;
		EXCEPTION WHEN others THEN
			BEGIN
				-- or an IPv4 address
				ip := host(split_part(NEW.rt, ':', 1)::inet);
				rt_part_one := (split_part(ip, '.', 1)::bigint << 24) +
							(split_part(ip, '.', 2)::bigint << 16) +
							(split_part(ip, '.', 3)::bigint << 8) +
							(split_part(ip, '.', 4)::bigint);
			EXCEPTION WHEN others THEN
				RAISE EXCEPTION 'Invalid input for column rt, should be ASN:id (123:456) or IP:id (1.3.3.7:456)';
			END;
		END;

		-- check part two
		BEGIN
			rt_part_two := split_part(NEW.rt, ':', 2)::bigint;
		EXCEPTION WHEN others THEN
			RAISE EXCEPTION 'Invalid input for column rt, should be ASN:id (123:456) or IP:id (1.3.3.7:456)';
		END;
		NEW.rt := rt_part_one::text || ':' || rt_part_two::text;
	END IF;

	RETURN NEW;
END;
$_$ LANGUAGE plpgsql;


--
-- Trigger function to keep data consistent in the ip_net_vrf table with
-- regards to prefix type and similar. This function handles DELETE operations.
--
CREATE OR REPLACE FUNCTION tf_ip_net_vrf_d_before() RETURNS trigger AS $_$
BEGIN
	-- block delete of default VRF with id 0
	IF OLD.id = 0 THEN
		RAISE EXCEPTION '1200:Prohibited delete of default VRF (id=0).';
	END IF;

	RETURN OLD;
END;
$_$ LANGUAGE plpgsql;


--
-- Trigger function to keep data consistent in the ip_net_plan table with
-- regards to prefix type and similar. This function handles INSERTs and
-- UPDATEs.
--
CREATE OR REPLACE FUNCTION tf_ip_net_plan__prefix_iu_before() RETURNS trigger AS $_$
DECLARE
	new_parent RECORD;
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
		-- don't allow changing VRF
		IF OLD.vrf_id != NEW.vrf_id THEN
			RAISE EXCEPTION '1200:Changing VRF is not allowed';
		END IF;

		-- update last modified timestamp
		NEW.last_modified = NOW();

		-- if prefix, type and pool is the same, quick return!
		IF OLD.type = NEW.type AND OLD.prefix = NEW.prefix AND OLD.pool_id = NEW.pool_id THEN
			RETURN NEW;
		END IF;
	END IF;


	i_max_pref_len := 32;
	IF family(NEW.prefix) = 6 THEN
		i_max_pref_len := 128;
	END IF;
	-- contains the parent prefix
	SELECT * INTO new_parent FROM ip_net_plan WHERE vrf_id = NEW.vrf_id AND iprange(prefix) >> iprange(NEW.prefix) ORDER BY masklen(prefix) DESC LIMIT 1;

	-- check that type is correct on insert and update
	IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
		IF NEW.type = 'host' THEN
			IF masklen(NEW.prefix) != i_max_pref_len THEN
				RAISE EXCEPTION '1200:Prefix of type host must have all bits set in netmask';
			END IF;
			IF new_parent.prefix IS NULL THEN
				RAISE EXCEPTION '1200:Prefix of type host must have a parent (covering) prefix of type assignment';
			END IF;
			IF new_parent.type != 'assignment' THEN
				RAISE EXCEPTION '1200:Parent prefix (%) is of type % but must be of type ''assignment''', new_parent.prefix, new_parent.type;
			END IF;
			NEW.display_prefix := set_masklen(NEW.prefix::inet, masklen(new_parent.prefix));

		ELSIF NEW.type = 'assignment' THEN
			IF new_parent.type IS NULL THEN
				-- all good
			ELSIF new_parent.type != 'reservation' THEN
				RAISE EXCEPTION '1200:Parent prefix (%) is of type % but must be of type ''reservation''', new_parent.prefix, new_parent.type;
			END IF;

			-- also check that the new prefix does not have any childs other than hosts
			--
			-- need to separate INSERT and UPDATE as OLD (which we rely on in
			-- the update case) is not set for INSERT queries
			IF TG_OP = 'INSERT' THEN
				IF EXISTS (SELECT * FROM ip_net_plan WHERE vrf_id = NEW.vrf_id AND type != 'host' AND iprange(prefix) << iprange(NEW.prefix) LIMIT 1) THEN
					RAISE EXCEPTION '1200:Prefix of type ''assignment'' must not have any subnets other than of type ''host''';
				END IF;
			ELSIF TG_OP = 'UPDATE' THEN
				IF EXISTS (SELECT * FROM ip_net_plan WHERE vrf_id = NEW.vrf_id AND type != 'host' AND iprange(prefix) << iprange(NEW.prefix) AND prefix != OLD.prefix LIMIT 1) THEN
					RAISE EXCEPTION '1200:Prefix of type ''assignment'' must not have any subnets other than of type ''host''';
				END IF;
			END IF;
			NEW.display_prefix := NEW.prefix;

		ELSIF NEW.type = 'reservation' THEN
			IF new_parent.type IS NULL THEN
				-- all good
			ELSIF new_parent.type != 'reservation' THEN
				RAISE EXCEPTION '1200:Parent prefix (%) is of type % but must be of type ''reservation''', new_parent.prefix, new_parent.type;
			END IF;
			NEW.display_prefix := NEW.prefix;

		ELSE
			RAISE EXCEPTION '1200:Unknown prefix type';
		END IF;

		-- is the new prefix part of a pool?
		IF NEW.pool_id IS NOT NULL THEN
			-- if so, make sure all prefixes in that pool belong to the same VRF
			IF NEW.vrf_id != (SELECT vrf_id FROM ip_net_plan WHERE pool_id = NEW.pool_id LIMIT 1) THEN
				RAISE EXCEPTION '1200:Change not allowed. All member prefixes of a pool must be in a the same VRF.';
			END IF;
		END IF;

		-- Only allow setting node on prefixes of type host or typ assignment
		-- and when the prefix length is the maximum prefix length for the
		-- address family. The case for assignment is when a /32 is used as a
		-- loopback address or similar in which case it is registered as an
		-- assignment and should be able to have a node specified.
		IF NEW.node IS NOT NULL THEN
			IF NEW.type = 'host' THEN
				-- all good
			ELSIF NEW.type = 'reservation' THEN
				RAISE EXCEPTION '1200:Not allowed to set ''node'' value for prefixes of type ''reservation''.';
			ELSE
				-- not a /32 or /128, so do not allow
				IF masklen(NEW.prefix) != i_max_pref_len THEN
					RAISE EXCEPTION '1200:Not allowed to set ''node'' value for prefixes of type ''assignment'' which do not have all bits set in netmask.';
				END IF;
			END IF;
		END IF;
	END IF;

	-- only allow specific cases for changing the type of prefix
	IF TG_OP = 'UPDATE' THEN
		IF (OLD.type = 'reservation' AND NEW.type = 'assignment') OR (OLD.type = 'assignment' AND new.type = 'reservation') THEN
			-- don't allow any childs, since they would automatically be of the
			-- wrong type, ie inconsistent data
			IF EXISTS (SELECT 1 FROM ip_net_plan WHERE vrf_id = NEW.vrf_id AND iprange(prefix) << iprange(NEW.prefix)) THEN
				RAISE EXCEPTION '1200:Changing from type ''%'' to ''%'' requires there to be no child prefixes.', OLD.type, NEW.type;
			END IF;
		ELSE
			IF OLD.type != NEW.type THEN
				RAISE EXCEPTION '1200:Changing type is not allowed';
			END IF;
		END IF;
	END IF;

	-- all is well, return
	RETURN NEW;
END;
$_$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION tf_ip_net_plan__other__iu_before() RETURNS trigger AS $_$
DECLARE
BEGIN
	-- Check country code- value needs to be a two letter country code
	-- according to ISO 3166-1 alpha-2
	--
	-- We do not check that the actual value is in ISO 3166-1, because that
	-- would entail including a full listing of country codes which we do not want
	-- as we risk including an outdated one. We don't want to force users to
	-- upgrade merely to get a new ISO 3166-1 list.
	NEW.country = upper(NEW.country);
	IF NEW.country !~ '^[A-Z]{2}$' THEN
		RAISE EXCEPTION '1200: Please enter a two letter country code according to ISO 3166-1 alpha-2';
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
	-- if an assignment contains hosts, we block the delete
	IF OLD.type = 'assignment' THEN
		-- contains one child prefix
		IF (SELECT COUNT(1) FROM ip_net_plan WHERE iprange(prefix) << iprange(OLD.prefix) AND vrf_id = OLD.vrf_id LIMIT 1) > 0 THEN
			RAISE EXCEPTION '1200:Prohibited delete, prefix (%) contains hosts.', OLD.prefix;
		END IF;
	END IF;

	RETURN OLD;
END;
$_$ LANGUAGE plpgsql;


--
-- Trigger function to set indent and children on the new prefix.
--
CREATE OR REPLACE FUNCTION tf_ip_net_plan__indent_children__iu_before() RETURNS trigger AS $_$
DECLARE
	new_parent record;
BEGIN
	SELECT * INTO new_parent FROM ip_net_plan WHERE vrf_id = NEW.vrf_id AND iprange(prefix) >> iprange(NEW.prefix) ORDER BY prefix DESC LIMIT 1;

	IF TG_OP = 'UPDATE' THEN
		NEW.children := (SELECT COUNT(1) FROM ip_net_plan WHERE vrf_id = NEW.vrf_id AND iprange(prefix) << iprange(NEW.prefix) AND prefix != OLD.prefix AND indent = COALESCE(new_parent.indent+1, 1));
	ELSE
		NEW.children := (SELECT COUNT(1) FROM ip_net_plan WHERE vrf_id = NEW.vrf_id AND iprange(prefix) << iprange(NEW.prefix) AND indent = COALESCE(new_parent.indent+1, 0));
	END IF;

	RETURN NEW;
END;
$_$ LANGUAGE plpgsql;


--
-- Trigger function to update various data once a prefix has been UPDATEd.
--
CREATE OR REPLACE FUNCTION tf_ip_net_plan__prefix_iu_after() RETURNS trigger AS $_$
DECLARE
	new_parent RECORD;
	child RECORD;
	i_max_pref_len integer;
BEGIN
	i_max_pref_len := 32;
	IF family(NEW.prefix) = 6 THEN
		i_max_pref_len := 128;
	END IF;
	-- contains the parent prefix
	SELECT * INTO new_parent FROM ip_net_plan WHERE vrf_id = NEW.vrf_id AND iprange(prefix) >> iprange(NEW.prefix) ORDER BY masklen(prefix) DESC LIMIT 1;

	-- update display_prefix of children prefixes
	IF TG_OP = 'UPDATE' THEN
		IF NEW.type = 'assignment' AND OLD.prefix != NEW.prefix THEN
			UPDATE ip_net_plan SET display_prefix = set_masklen(prefix::inet, masklen(NEW.prefix)) WHERE vrf_id = NEW.vrf_id AND prefix << NEW.prefix;
		END IF;
	END IF;

	-- all is well, return
	RETURN NEW;
END;
$_$ LANGUAGE plpgsql;


--
-- Trigger function to calculate the number of children and update the indent
-- level for associated prefix when adding or removing a prefix.
--
CREATE OR REPLACE FUNCTION tf_ip_net_plan__indent_children__iud_after() RETURNS trigger AS $$
DECLARE
	old_parent record;
	new_parent record;
BEGIN
	-- This only sets the number of children prefix for the old or new parent
	-- prefix. The number of children for the prefix being modified is
	-- calculated in the before trigger.

	IF TG_OP IN ('DELETE', 'UPDATE') THEN
		-- calculation of children is dependent upon indent, so do indent first
		PERFORM calc_indent(OLD.vrf_id, OLD.prefix, -1);

		-- children calc
		-- Note how we have to explicitly filter out NEW.prefix as the table
		-- has already been updated and we risk getting ourself as old_parent.
		IF TG_OP = 'UPDATE' THEN
			SELECT * INTO old_parent FROM ip_net_plan WHERE vrf_id = OLD.vrf_id AND iprange(prefix) >> iprange(OLD.prefix) AND prefix != NEW.prefix ORDER BY prefix DESC LIMIT 1;
		ELSE
			SELECT * INTO old_parent FROM ip_net_plan WHERE vrf_id = OLD.vrf_id AND iprange(prefix) >> iprange(OLD.prefix) ORDER BY prefix DESC LIMIT 1;
		END IF;

		IF old_parent.id IS NOT NULL THEN
			UPDATE ip_net_plan SET children =
					(SELECT COUNT(1)
					FROM ip_net_plan
					WHERE vrf_id = OLD.vrf_id
						AND iprange(prefix) << iprange(old_parent.prefix)
						AND indent = old_parent.indent+1)
				WHERE id = old_parent.id;
		END IF;
	END IF;

	IF TG_OP IN ('INSERT', 'UPDATE') THEN
		-- calculation of children is dependent upon indent, so do indent first
		PERFORM calc_indent(NEW.vrf_id, NEW.prefix, 1);

		-- children calc
		SELECT * INTO new_parent FROM ip_net_plan WHERE vrf_id = NEW.vrf_id AND iprange(prefix) >> iprange(NEW.prefix) ORDER BY prefix DESC LIMIT 1;
		IF new_parent.id IS NOT NULL THEN
			UPDATE ip_net_plan SET children =
					(SELECT COUNT(1)
					FROM ip_net_plan
					WHERE vrf_id = NEW.vrf_id
						AND iprange(prefix) << iprange(new_parent.prefix)
						AND indent = new_parent.indent+1)
				WHERE id = new_parent.id;
		END IF;
	END IF;

	RETURN NEW;
END;
$$ LANGUAGE plpgsql;


--
-- Trigger function to update inherited tags.
--
CREATE OR REPLACE FUNCTION tf_ip_net_plan__tags__iud_after() RETURNS trigger AS $$
DECLARE
	old_parent record;
	new_parent record;
BEGIN
	IF TG_OP = 'DELETE' THEN
		SELECT * INTO old_parent FROM ip_net_plan WHERE vrf_id = OLD.vrf_id AND iprange(prefix) >> iprange(OLD.prefix) ORDER BY prefix DESC LIMIT 1;

		-- parent is NULL if we are top level
		IF old_parent.id IS NULL THEN
			-- calc tags from parent of the deleted prefix to what is now the
			-- direct children of the parent prefix
			-- tags
			PERFORM calc_tags(OLD.vrf_id, OLD.prefix);
		ELSE
			-- tags
			PERFORM calc_tags(OLD.vrf_id, old_parent.prefix);
		END IF;

	ELSIF TG_OP = 'INSERT' THEN
		SELECT * INTO new_parent FROM ip_net_plan WHERE vrf_id = NEW.vrf_id AND iprange(prefix) >> iprange(NEW.prefix) ORDER BY prefix DESC LIMIT 1;

		-- identify the parent and run calc_tags on it to inherit tags to
		-- the new prefix from the parent
		-- tag calculation
		PERFORM calc_tags(NEW.vrf_id, new_parent.prefix);
		-- now push tags from the new prefix to its children
		PERFORM calc_tags(NEW.vrf_id, NEW.prefix);

	ELSIF TG_OP = 'UPDATE' THEN
		PERFORM calc_tags(OLD.vrf_id, OLD.prefix);
		PERFORM calc_tags(NEW.vrf_id, NEW.prefix);
	END IF;

	RETURN NEW;
END;
$$ LANGUAGE plpgsql;


--
-- Function used to remove all triggers during installation of new triggers
--
CREATE OR REPLACE FUNCTION clean_nipap_triggers() RETURNS bool AS $_$
DECLARE
	r record;
BEGIN
	FOR r IN (SELECT DISTINCT trigger_name FROM information_schema.triggers WHERE event_object_table = 'ip_net_vrf' AND trigger_schema NOT IN ('pg_catalog', 'information_schema')) LOOP
		EXECUTE 'DROP TRIGGER ' || r.trigger_name || ' ON ip_net_vrf';
	END LOOP;
	FOR r IN (SELECT DISTINCT trigger_name FROM information_schema.triggers WHERE event_object_table = 'ip_net_plan' AND trigger_schema NOT IN ('pg_catalog', 'information_schema')) LOOP
		EXECUTE 'DROP TRIGGER ' || r.trigger_name || ' ON ip_net_plan';
	END LOOP;

	RETURN true;
END;
$_$ LANGUAGE plpgsql;

SELECT clean_nipap_triggers();

--
-- Triggers for sanity checking on ip_net_vrf table.
--
CREATE TRIGGER trigger_ip_net_vrf__iu_before
	BEFORE UPDATE OR INSERT
	ON ip_net_vrf
	FOR EACH ROW
	EXECUTE PROCEDURE tf_ip_net_vrf_iu_before();

CREATE TRIGGER trigger_ip_net_vrf__d_before
	BEFORE DELETE
	ON ip_net_vrf
	FOR EACH ROW
	EXECUTE PROCEDURE tf_ip_net_vrf_d_before();



--
-- Triggers for consistency checking and updating indent level on ip_net_plan
-- table.
--


-- sanity checking of INSERTs on ip_net_plan
CREATE TRIGGER trigger_ip_net_plan__i_before
	BEFORE INSERT
	ON ip_net_plan
	FOR EACH ROW
	EXECUTE PROCEDURE tf_ip_net_plan__prefix_iu_before();

-- sanity checking of UPDATEs on ip_net_plan
CREATE TRIGGER trigger_ip_net_plan__vrf_prefix_type__u_before
	BEFORE UPDATE OF vrf_id, prefix, type
	ON ip_net_plan
	FOR EACH ROW
	WHEN (OLD.vrf_id != NEW.vrf_id
		OR OLD.prefix != NEW.prefix
		OR OLD.type != NEW.type)
	EXECUTE PROCEDURE tf_ip_net_plan__prefix_iu_before();

-- actions to be performed after an UPDATE on ip_net_plan
-- sanity checks are performed in the before trigger, so this is only to
-- execute various changes that need to happen once a prefix has been updated
CREATE TRIGGER trigger_ip_net_plan__vrf_prefix_type__u_after
	AFTER UPDATE OF vrf_id, prefix, type
	ON ip_net_plan
	FOR EACH ROW
	WHEN (OLD.vrf_id != NEW.vrf_id
		OR OLD.prefix != NEW.prefix
		OR OLD.type != NEW.type)
	EXECUTE PROCEDURE tf_ip_net_plan__prefix_iu_after();

-- check country code is correct
CREATE TRIGGER trigger_ip_net_plan__other__i_before
	BEFORE INSERT
	ON ip_net_plan
	FOR EACH ROW
	EXECUTE PROCEDURE tf_ip_net_plan__other__iu_before();

CREATE TRIGGER trigger_ip_net_plan__other__u_before
	BEFORE UPDATE OF country
	ON ip_net_plan
	FOR EACH ROW
	WHEN (OLD.country != NEW.country)
	EXECUTE PROCEDURE tf_ip_net_plan__other__iu_before();


-- ip_net_plan - update indent and number of children
CREATE TRIGGER trigger_ip_net_plan__indent_children__i_before
	BEFORE INSERT
	ON ip_net_plan
	FOR EACH ROW
	EXECUTE PROCEDURE tf_ip_net_plan__indent_children__iu_before();

CREATE TRIGGER trigger_ip_net_plan__indent_children__u_before
	BEFORE UPDATE OF prefix
	ON ip_net_plan
	FOR EACH ROW
	WHEN (OLD.prefix != NEW.prefix)
	EXECUTE PROCEDURE tf_ip_net_plan__indent_children__iu_before();

CREATE TRIGGER trigger_ip_net_plan__indent_children__id_after
	AFTER INSERT OR DELETE
	ON ip_net_plan
	FOR EACH ROW
	EXECUTE PROCEDURE tf_ip_net_plan__indent_children__iud_after();

CREATE TRIGGER trigger_ip_net_plan__indent_children__u_after
	AFTER UPDATE OF prefix
	ON ip_net_plan
	FOR EACH ROW
	WHEN (OLD.prefix != NEW.prefix)
	EXECUTE PROCEDURE tf_ip_net_plan__indent_children__iud_after();


-- update tags and inherited tags
CREATE TRIGGER trigger_ip_net_plan__tags__id_after
	AFTER INSERT OR DELETE
	ON ip_net_plan
	FOR EACH ROW
	EXECUTE PROCEDURE tf_ip_net_plan__tags__iud_after();

CREATE TRIGGER trigger_ip_net_plan__tags__u_after
	AFTER UPDATE OF prefix, tags, inherited_tags
	ON ip_net_plan
	FOR EACH ROW
	WHEN (OLD.prefix != NEW.prefix
		OR OLD.tags != NEW.tags
		OR OLD.inherited_tags != NEW.inherited_tags)
	EXECUTE PROCEDURE tf_ip_net_plan__tags__iud_after();

--
CREATE TRIGGER trigger_ip_net_plan_prefix__d_before
	BEFORE DELETE
	ON ip_net_plan
	FOR EACH ROW
	EXECUTE PROCEDURE tf_ip_net_prefix_d_before();
