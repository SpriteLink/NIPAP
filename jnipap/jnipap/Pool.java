package jnipap;

import java.util.HashMap;
import java.util.Map;
import java.util.List;
import java.util.ArrayList;

import org.apache.xmlrpc.XmlRpcException;
import org.apache.xmlrpc.client.XmlRpcHttpTransportException;

import jnipap.NonExistentException;
import jnipap.ConnectionException;
import jnipap.AuthFailedException;
import jnipap.Connection;

public class Pool extends Jnipap {

	// Pool attributes
	public String name;
	public String description;
	public String default_type; // Some kind of enum?
	public Integer ipv4_default_prefix_length;
	public Integer ipv6_default_prefix_length;
	public VRF vrf;

	/**
	 * Save object to NIPAP
	 */
	public void save(Connection conn) throws JnipapException {

		// create hashmap of pool attributes
		HashMap attr = new HashMap();
		attr.put((Object)"name", (Object)this.name);
		attr.put((Object)"description", (Object)this.description);
		attr.put((Object)"default_type", (Object)this.default_type);
		attr.put((Object)"ipv4_default_prefix_length", (Object)this.ipv4_default_prefix_length);
		attr.put((Object)"ipv6_default_prefix_length", (Object)this.ipv6_default_prefix_length);

		// create pool spec
		HashMap pool_spec = new HashMap();
		pool_spec.put("id", this.id);

		// create args map
		HashMap args = new HashMap();
		args.put("auth", conn.authMap());
		args.put("attr", attr);

		// create params list
		List params = new ArrayList();
		params.add(args);

		// Create new or modify old?
		Map pool;
		if (this.id == null) {

			// ID null - create new pool
			pool = (Map)conn.execute("add_pool", params);

		} else {

			// Pool exists - modify existing.
			args.put("pool", pool_spec);
			Object[] result = (Object[])conn.execute("edit_pool", params);

			if (result.length != 1) {
				throw new JnipapException("Pool edit returned " + result.length + " entries, should be 1.");
			}

			pool = (Map)result[0];

		}

		// Update pool object with new data
		Pool.fromMap(conn, pool, this);

	}

	/**
	 * Remove object from NIPAP
	 */
	public void remove(Connection conn) throws JnipapException {

		// Build pool spec
		HashMap pool_spec = new HashMap();
		pool_spec.put("id", this.id);

		// Build function args
		HashMap args = new HashMap();
		args.put("auth", conn.authMap());
		args.put("pool", pool_spec);

		List params = new ArrayList();
		params.add(args);

		// execute query
		Object[] result = (Object[])conn.execute("remove_pool", params);

	}

	/**
	 * Return a string representation of a pool
	 *
	 * @return String describing the pool and its attributes
	 */
	public String toString() {

		// Return string representation of a pool
		return getClass().getName() + " id: " + this.id +
			" name: " + this.name +
			" desc: " + this.description +
			" default_type: " + this.default_type +
			" ipv4_default_prefix_length: " + this.ipv4_default_prefix_length +
			" ipv6_default_prefix_length: " + this.ipv6_default_prefix_length;

	}

	/**
	 * Get list of pools from NIPAP by its attributes
	 *
	 * @param conn Connection with auth options
	 * @param query Map describing the search query
	 * @param search_options Search options
	 * @return A list of Pool objects matching the attributes in the query map
	 */
	public static Map search(Connection conn, Map query, Map search_options) throws JnipapException {

		// Build function args
		HashMap args = new HashMap();
		args.put("auth", conn.authMap());
		args.put("query", query);
		args.put("search_options", search_options);

		List params = new ArrayList();
		params.add(args);

		// execute query
		Map result = (Map)conn.execute("search_pool", params);

		// extract data from result
		HashMap ret = new HashMap();
		ret.put("search_options", (Map)result.get("search_options"));
		ArrayList ret_pools = new ArrayList();

		Object[] result_pools = (Object[])result.get("result");

		for (int i = 0; i < result_pools.length; i++) {
			Map result_pool = (Map)result_pools[i];
			ret_pools.add(Pool.fromMap(conn, result_pool));
		}

		ret.put("result", ret_pools);

		return ret;

	}

	/**
	 * Get list of pools from NIPAP matching a search string
	 *
	 * @param conn Connection with auth options
	 * @param query Search string
	 * @param search_options Search options
	 * @return A list of Pool objects matching the query string
	 */
	public static Map search(Connection conn, String query, Map search_options) throws JnipapException {

		// Build function args
		HashMap args = new HashMap();
		args.put("auth", conn.authMap());
		args.put("query_string", query);
		args.put("search_options", search_options);

		List params = new ArrayList();
		params.add(args);

		// execute query
		Map result = (Map)conn.execute("smart_search_pool", params);

		// extract data from result
		HashMap ret = new HashMap();
		ret.put("search_options", (Map)result.get("search_options"));
		ret.put("interpretation", (Map)result.get("interpretation"));

		ArrayList ret_pools = new ArrayList();
		Object[] result_pools = (Object[])result.get("result");
		for (int i = 0; i < result_pools.length; i++) {
			Map result_pool = (Map)result_pools[i];
			ret_pools.add(Pool.fromMap(conn, result_pool));
		}
		ret.put("result", ret_pools);

		return ret;

	}

	/**
	 * List pools with specified attributes
	 *
	 * @param conn Connection with auth options
	 * @param pool_spec Map of pool attributes
	 * @return List of pools matching the attributes
	 */
	public static List list(Connection conn, Map pool_spec) throws JnipapException {

		// Build function args
		HashMap args = new HashMap();
		args.put("auth", conn.authMap());
		args.put("pool", pool_spec);

		List params = new ArrayList();
		params.add(args);

		// execute query
		Object[] result = (Object[])conn.execute("list_pool", params);

		// extract data from result
		ArrayList ret = new ArrayList();

		for (int i = 0; i < result.length; i++) {
			Map result_pool = (Map)result[i];
			ret.add(Pool.fromMap(conn, result_pool));
		}

		return ret;

	}

	/**
	 * Get pool from NIPAP by ID
	 *
	 * Fetch a pool from NIPAP by specifying its ID. If no matching pool
	 * was found, an exception is thrown.
	 *
	 * @param conn Connection with auth options
	 * @param id ID of requested pool
	 * @return The pool which was found
	 */
	public static Pool get(Connection conn, Integer id) throws JnipapException {

		// Build pool spec
		HashMap pool_spec = new HashMap();
		pool_spec.put((Object)"id", (Object)id);

		List result = Pool.list(conn, pool_spec);

		// extract data from result
		if (result.size() < 1) {
			throw new NonExistentException("no matching pool found");
		}

		return (Pool)result.get(0);

	}

	/**
	 * Create pool object from map of pool attributes
	 *
	 * Helper function for creating objects of data received over XML-RPC
	 *
	 * @param input Map with pool attributes
	 * @return Pool object
	 */
	public static Pool fromMap(Connection conn, Map input) throws JnipapException {

		return Pool.fromMap(conn, input, new Pool());

	}

	/**
	 * Create pool object from map of pool attributes
	 *
	 * Updates a Pool object with attributes from a Map as received over
	 * XML-RPC
	 *
	 * @param conn Connection object
	 * @param input Map with pool attributes
	 * @param pool Pool object to populate with attributes from map
	 * @return Pool object
	 */
	public static Pool fromMap(Connection conn,Map input, Pool pool) throws JnipapException {

		pool.id = (Integer)input.get("id");
		pool.name = (String)input.get("name");
		pool.description = (String)input.get("description");
		pool.default_type = (String)input.get("default_type");
		pool.ipv4_default_prefix_length = (Integer)input.get("ipv4_default_prefix_length");
		pool.ipv6_default_prefix_length = (Integer)input.get("ipv6_default_prefix_length");

		// If VRF is not null, fetch VRF object
		if (input.get("vrf_id") != null) {
			pool.vrf = VRF.get(conn, (Integer)input.get("vrf_id"));
		}

		return pool;

	}

	/**
	 * Compute hash of VRF
	 */
	public int hashCode() {

		int hash = super.hashCode();
		hash = hash * 31 + (name == null ? 0 : name.hashCode());
		hash = hash * 31 + (description == null ? 0 : description.hashCode());
		hash = hash * 31 + (default_type == null ? 0 : default_type.hashCode());
		hash = hash * 31 + (ipv4_default_prefix_length == null ? 0 : ipv4_default_prefix_length.hashCode());
		hash = hash * 31 + (ipv6_default_prefix_length == null ? 0 : ipv6_default_prefix_length.hashCode());
		hash = hash * 31 + (vrf == null ? 0 : vrf.hashCode());

		return hash;

	}

	/**
	 * Verify equality
	 */
	public boolean equals(Object other) {

		if (!super.equals(other)) return false;
		Pool pool = (Pool)other;

		return (
			(name == pool.name || (name != null && name.equals(pool.name))) &&
			(description == pool.description ||
				(description != null && description.equals(pool.description))) &&
			(default_type == pool.default_type ||
				(default_type != null && default_type.equals(pool.default_type))) &&
			(ipv4_default_prefix_length == pool.ipv4_default_prefix_length ||
				(ipv4_default_prefix_length != null &&
					ipv4_default_prefix_length.equals(pool.ipv4_default_prefix_length))) &&
			(ipv6_default_prefix_length == pool.ipv6_default_prefix_length ||
				(ipv6_default_prefix_length != null &&
					ipv6_default_prefix_length.equals(pool.ipv6_default_prefix_length))) &&
			(vrf == pool.vrf || (vrf != null && vrf.equals(pool.vrf)))
		);

	}

}
