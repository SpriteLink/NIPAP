--
-- Upgrade from NIPAP database schema version 6 to 7
--

CREATE OR REPLACE FUNCTION tf_ip_net_plan__prefix_iu_before() RETURNS trigger AS $_$
DECLARE
	new_parent RECORD;
	child RECORD;
	i_max_pref_len integer;
	p RECORD;
	num_used numeric(40);
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

		-- if vrf, type, prefix and pool is the same, quick return!
		IF OLD.vrf_id = NEW.vrf_id AND OLD.type = NEW.type AND OLD.prefix = NEW.prefix AND OLD.pool_id IS NOT DISTINCT FROM NEW.pool_id THEN
			RETURN NEW;
		END IF;
	END IF;


	i_max_pref_len := 32;
	IF family(NEW.prefix) = 6 THEN
		i_max_pref_len := 128;
	END IF;
	-- contains the parent prefix
	IF TG_OP = 'INSERT' THEN
		SELECT * INTO new_parent FROM ip_net_plan WHERE vrf_id = NEW.vrf_id AND iprange(prefix) >> iprange(NEW.prefix) ORDER BY masklen(prefix) DESC LIMIT 1;
	ELSE
		-- avoid selecting our old self as parent
		SELECT * INTO new_parent FROM ip_net_plan WHERE vrf_id = NEW.vrf_id AND iprange(prefix) >> iprange(NEW.prefix) AND prefix != OLD.prefix ORDER BY masklen(prefix) DESC LIMIT 1;
	END IF;

	--
	---- Various sanity checking -----------------------------------------------
	--
	-- Trigger on: vrf_id, prefix, type
	--
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
				RAISE EXCEPTION '1200:Parent prefix (%%) is of type %% but must be of type ''assignment''', new_parent.prefix, new_parent.type;
			END IF;
			NEW.display_prefix := set_masklen(NEW.prefix::inet, masklen(new_parent.prefix));

		ELSIF NEW.type = 'assignment' THEN
			IF new_parent.type IS NULL THEN
				-- all good
			ELSIF new_parent.type != 'reservation' THEN
				RAISE EXCEPTION '1200:Parent prefix (%%) is of type %% but must be of type ''reservation''', new_parent.prefix, new_parent.type;
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
				RAISE EXCEPTION '1200:Parent prefix (%%) is of type %% but must be of type ''reservation''', new_parent.prefix, new_parent.type;
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
				RAISE EXCEPTION '1200:Changing from type ''%%'' to ''%%'' requires there to be no child prefixes.', OLD.type, NEW.type;
			END IF;
		ELSE
			IF OLD.type != NEW.type THEN
				RAISE EXCEPTION '1200:Changing type is not allowed';
			END IF;
		END IF;
	END IF;


	--
	---- Calculate indent for new prefix ---------------------------------------
	--
	-- Trigger on: vrf_id, prefix
	--
	-- use parent prefix indent+1 or if parent is not set, it means we are a
	-- top level prefix and we use indent 0
	NEW.indent := COALESCE(new_parent.indent+1, 0);


	--
	---- Statistics ------------------------------------------------------------
	--
	-- Trigger on: vrf_id, prefix
	--

	-- total addresses
	IF family(NEW.prefix) = 4 THEN
		NEW.total_addresses = power(2::numeric, 32 - masklen(NEW.prefix));
	ELSE
		NEW.total_addresses = power(2::numeric, 128 - masklen(NEW.prefix));
	END IF;

	-- used addresses
	-- special case for hosts
	IF masklen(NEW.prefix) = i_max_pref_len THEN
		NEW.used_addresses := NEW.total_addresses;
	ELSE
		num_used := 0;
		IF TG_OP = 'INSERT' THEN
			FOR p IN (SELECT * FROM ip_net_plan WHERE prefix << NEW.prefix AND vrf_id = NEW.vrf_id AND indent = COALESCE(new_parent.indent+1, 0) ORDER BY prefix ASC) LOOP
				num_used := num_used + (SELECT power(2::numeric, i_max_pref_len-masklen(p.prefix)))::numeric(39);
			END LOOP;
		ELSIF TG_OP = 'UPDATE' THEN
			IF OLD.prefix = NEW.prefix THEN
				-- No change - keep old value
				num_used := OLD.used_addresses;
			ELSIF NEW.prefix << OLD.prefix AND OLD.indent = NEW.indent THEN -- NEW is smaller and covered by OLD
				FOR p IN (SELECT * FROM ip_net_plan WHERE prefix << NEW.prefix AND vrf_id = NEW.vrf_id AND indent = NEW.indent+1 ORDER BY prefix ASC) LOOP
					num_used := num_used + (SELECT power(2::numeric, i_max_pref_len-masklen(p.prefix)))::numeric(39);
				END LOOP;
			ELSIF NEW.prefix << OLD.prefix THEN -- NEW is smaller and covered by OLD
				--
				FOR p IN (SELECT * FROM ip_net_plan WHERE prefix << NEW.prefix AND vrf_id = NEW.vrf_id AND indent = NEW.indent ORDER BY prefix ASC) LOOP
					num_used := num_used + (SELECT power(2::numeric, i_max_pref_len-masklen(p.prefix)))::numeric(39);
				END LOOP;
			ELSIF NEW.prefix >> OLD.prefix AND OLD.indent = NEW.indent THEN -- NEW is larger and covers OLD, but same indent
				-- since the new prefix covers the old prefix but the indent
				-- hasn't been updated yet, we will see child prefixes with
				-- OLD.indent + 1 and then the part that is now covered by
				-- NEW.prefix but wasn't covered by OLD.prefix will have
				-- indent = NEW.indent ( to be NEW.indent+1 after update)
				FOR p IN (SELECT * FROM ip_net_plan WHERE vrf_id = NEW.vrf_id AND prefix != OLD.prefix AND ((indent = OLD.indent+1 AND prefix << OLD.prefix) OR indent = NEW.indent AND prefix << NEW.prefix) ORDER BY prefix ASC) LOOP
					num_used := num_used + (SELECT power(2::numeric, i_max_pref_len-masklen(p.prefix)))::numeric(39);
				END LOOP;

			ELSIF NEW.prefix >> OLD.prefix THEN -- NEW is larger and covers OLD but with different indent
				FOR p IN (SELECT * FROM ip_net_plan WHERE vrf_id = NEW.vrf_id AND prefix != OLD.prefix AND (indent = NEW.indent AND prefix << NEW.prefix) ORDER BY prefix ASC) LOOP
					num_used := num_used + (SELECT power(2::numeric, i_max_pref_len-masklen(p.prefix)))::numeric(39);
				END LOOP;
			ELSE -- prefix has been moved and doesn't cover or is covered by OLD
				FOR p IN (SELECT * FROM ip_net_plan WHERE vrf_id = NEW.vrf_id AND prefix << NEW.prefix AND indent = COALESCE(new_parent.indent+1, 0) ORDER BY prefix ASC) LOOP
					num_used := num_used + (SELECT power(2::numeric, i_max_pref_len-masklen(p.prefix)))::numeric(39);
				END LOOP;

			END IF;
		END IF;
		NEW.used_addresses = num_used;
	END IF;

	-- free addresses
	NEW.free_addresses := NEW.total_addresses - NEW.used_addresses;


	--
	---- Inherited Tags --------------------------------------------------------
	-- Update inherited tags
	--
	-- Trigger: vrf_id, prefix
	--
	-- set new inherited_tags based on parent_prefix tags and inherited_tags
	IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
		NEW.inherited_tags := array_undup(array_cat(new_parent.inherited_tags, new_parent.tags));
	END IF;


	-- all is well, return
	RETURN NEW;
END;
$_$ LANGUAGE plpgsql;

-- update database schema version
COMMENT ON DATABASE %s IS 'NIPAP database - schema version: 7';
