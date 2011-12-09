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
import jnipap.Schema;

public class Pool extends Jnipap {

	// Pool attributes
	public String name;
	public Schema schema;
	public String description;
	public String default_type; // Some kind of enum?
	public Integer ipv4_default_prefix_length;
	public Integer ipv6_default_prefix_length;

	/**
	 * Save object to NIPAP
	 */
	public void save(Connection conn) throws JnipapException {

		// TODO: handle schema = null

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

		// create schema spec
		HashMap schema_spec = new HashMap();
		schema_spec.put("id", this.schema.id);

		// create args map
		HashMap args = new HashMap();
		args.put("auth", conn.authMap());
		args.put("attr", attr);
		args.put("schema", schema_spec);

		// create params list
		List params = new ArrayList();
		params.add(args);

		// Create new or modify old?
		String cmd;
		if (this.id == null) {

			// ID null - create new pool
			attr.put("schema", this.schema.id);
			cmd = "add_pool";

		} else {

			// Pool exists - modify existing.
			args.put("pool", pool_spec);
			cmd = "edit_pool";

		}

		// perform operation
		Integer result = (Integer)conn.execute(cmd, params);

		// If we added a new pool, fetch and set ID
		if (this.id == null) {
			this.id = result;
		}

	}

	/**
	 * Remove object from NIPAP
	 */
	public void remove(Connection conn) throws JnipapException {

		// Build pool spec
		HashMap pool_spec = new HashMap();
		pool_spec.put("id", this.id);

		HashMap schema_spec = new HashMap();
		schema_spec.put("id", this.schema.id);

		// Build function args
		HashMap args = new HashMap();
		args.put("auth", conn.authMap());
		args.put("schema", schema_spec);
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
	 * @param schema Schema to search
	 * @param query Map describing the search query
	 * @param search_options Search options
	 * @return A list of Pool objects matching the attributes in the query map
	 */
	public static Map search(Connection conn, Schema schema, Map query, Map search_options) throws JnipapException {

		HashMap schema_spec = new HashMap();
		schema_spec.put("id", schema.id);

		// Build function args
		HashMap args = new HashMap();
		args.put("auth", conn.authMap());
		args.put("schema", schema_spec);
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
	 * @param schema Schema to search
	 * @param query Search string
	 * @param search_options Search options
	 * @return A list of Pool objects matching the query string
	 */
	public static Map search(Connection conn, Schema schema, String query, Map search_options) throws JnipapException {

		HashMap schema_spec = new HashMap();
		schema_spec.put("id", schema.id);

		// Build function args
		HashMap args = new HashMap();
		args.put("auth", conn.authMap());
		args.put("schema", schema_spec);
		args.put("query_string", query);
		args.put("search_options", search_options);

		List params = new ArrayList();
		params.add(args);

		// execute query
		Map result = (Map)conn.execute("smart_search_pool", params);

		// extract data from result
		HashMap ret = new HashMap();
		ret.put("search_options", (Map)result.get("search_options"));

		Object[] interpretation_result = (Object[])result.get("interpretation");
		List ret_interpretation = new ArrayList();
		for (int i = 0; i < interpretation_result.length; i++) {
			ret_interpretation.add((Map)interpretation_result[i]);
		}
		ret.put("interpretation", ret_interpretation);

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
	public static List list(Connection conn, Schema schema, Map pool_spec) throws JnipapException {

		HashMap schema_spec = new HashMap();
		schema_spec.put("id", schema.id);

		// Build function args
		HashMap args = new HashMap();
		args.put("auth", conn.authMap());
		args.put("pool", pool_spec);
		args.put("schema", schema_spec);

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
	public static Pool get(Connection conn, Schema schema, Integer id) throws JnipapException {

		// Build pool spec
		HashMap pool_spec = new HashMap();
		pool_spec.put((Object)"id", (Object)id);

		List result = Pool.list(conn, schema, pool_spec);

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
	 * @param conn Connection with auth options
	 * @return Pool object
	 */
	public static Pool fromMap(Connection conn, Map input) throws JnipapException {

		Pool pool = new Pool();

		pool.id = (Integer)input.get("id");
		pool.name = (String)input.get("name");
		pool.schema = Schema.get(conn, (Integer)input.get("schema"));
		pool.description = (String)input.get("description");
		pool.default_type = (String)input.get("default_type");
		pool.ipv4_default_prefix_length = (Integer)input.get("ipv4_default_prefix_length");
		pool.ipv6_default_prefix_length = (Integer)input.get("ipv6_default_prefix_length");

		return pool;

	}

}
