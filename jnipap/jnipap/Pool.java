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

	// Schema attributes
	public String name;
	public Schema schema;
	public String description;
	public String default_type;
	public Integer ipv4_default_prefix_length;
	public Integer ipv6_default_prefix_length;

	/**
	 * Creates new pool object
	 */
	public Pool() {

		super();

	}

	/**
	 * Save object to NIPAP
	 */
	public void save(AuthOptions auth) throws JnipapException {

		// TODO: handle schema = null

		// create hashmap of schema attributes
		HashMap<String, Object> attr = new HashMap<String, Object>();
		attr.put("name", this.name);
		attr.put("description", this.description);
		attr.put("default_type", this.default_type);
		attr.put("ipv4_default_prefix_length", this.ipv4_default_prefix_length);
		attr.put("ipv6_default_prefix_length", this.ipv6_default_prefix_length);

		// create pool spec
		HashMap<String, Object> pool_spec = new HashMap<String, Object>();
		pool_spec.put("id", this.id);

		// create args map
		HashMap<String, Map<String, Object>> args = new HashMap<String, Map<String, Object>>();
		args.put("auth", auth.toMap());
		args.put("attr", attr);

		// create params list
		List<HashMap> params = new ArrayList<HashMap>();
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
		Integer result;
		result = (Integer)conn.execute(cmd, params);

		// If we added a new pool, fetch and set ID
		if (this.id == null) {
			this.id = result;
		}

	}

	/**
	 * Remove object from NIPAP
	 */
	public void remove(AuthOptions auth) throws ConnectionException {

		// Build pool spec
		HashMap<String, Object> pool_spec = new HashMap<String, Object>();
		pool_spec.put("id", this.id);

		// Build function args
		HashMap<String, Map<String, Object>> args = new HashMap<String, Map<String, Object>>();
		args.put("auth", auth.toMap());
		args.put("pool", pool_spec);

		List<HashMap> params = new ArrayList<HashMap>();
		params.add(args);

		// execute query
		Object[] result;
		try {
			result = (Object[])conn.connection.execute("remove_pool", params);
		} catch(XmlRpcException e) {
			throw new ConnectionException(e);
		}

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
	 * @param auth Authentication options
	 * @param schema Schema to search
	 * @param query Map describing the search query
	 * @param search_options Search options
	 * @return A list of Pool objects matching the attributes in the query map
	 */
	public static Map<String, Object> search(AuthOptions auth, Schema schema, Map<String, Object> query, Map<String, Object> search_options) throws JnipapException {

		// Create XML-RPC connection
		Connection conn = Connection.getInstance();

		HashMap<String, Object> schema_spec = new HashMap<String, Object>();
		schema_spec.put("id", schema.id);

		// Build function args
		HashMap<String, Map<String, Object>> args = new HashMap<String, Map<String, Object>>();
		args.put("auth", auth.toMap());
		args.put("schema", schema_spec);
		args.put("query", query);
		args.put("search_options", search_options);

		List<HashMap> params = new ArrayList<HashMap>();
		params.add(args);

		// execute query
		Map result = (Map)conn.execute("search_pool", params);

		// extract data from result
		HashMap<String, Object> ret = new HashMap<String, Object>();
		ret.put("search_options", (Map)result.get("search_options"));
		ArrayList<Pool> ret_pools = new ArrayList<Pool>();

		Object[] result_pools = (Object[])result.get("result");

		for (int i = 0; i < result_pools.length; i++) {
			Map<String, Object> result_pool = (Map<String, Object>)result_pools[i];
			ret_pools.add(Pool.fromMap(auth, result_pool));
		}

		ret.put("result", ret_pools);

		return ret;

	}

	/**
	 * Get list of pools from NIPAP matching a search string
	 *
	 * @param auth Authentication options
	 * @param schema Schema to search
	 * @param query Search string
	 * @param search_options Search options
	 * @return A list of Pool objects matching the query string
	 */
	public static Map<String, Object> search(AuthOptions auth, Schema schema, String query, Map<String, Object> search_options) throws JnipapException {

		// Create XML-RPC connection
		Connection conn = Connection.getInstance();

		HashMap<String, Object> schema_spec = new HashMap<String, Object>();
		schema_spec.put("id", schema.id);

		// Build function args
		HashMap<String, Object> args = new HashMap<String, Object>();
		args.put("auth", auth.toMap());
		args.put("schema", schema_spec);
		args.put("query_string", query);
		args.put("search_options", search_options);

		List<HashMap> params = new ArrayList<HashMap>();
		params.add(args);

		// execute query
		Map result = (Map)conn.execute("smart_search_pool", params);

		// extract data from result
		HashMap<String, Object> ret = new HashMap<String, Object>();
		ret.put("search_options", (Map)result.get("search_options"));

		Object[] interpretation_result = (Object[])result.get("interpretation");
		List<Map> ret_interpretation = new ArrayList<Map>();
		for (int i = 0; i < interpretation_result.length; i++) {
			ret_interpretation.add((Map)interpretation_result[i]);
		}
		ret.put("interpretation", ret_interpretation);

		ArrayList<Pool> ret_pools = new ArrayList<Pool>();
		Object[] result_pools = (Object[])result.get("result");
		for (int i = 0; i < result_pools.length; i++) {
			Map<String, Object> result_pool = (Map<String, Object>)result_pools[i];
			ret_pools.add(Pool.fromMap(auth, result_pool));
		}
		ret.put("result", ret_pools);

		return ret;

	}

	/**
	 * List pools with specified attributes
	 *
	 * @param auth Authentication options
	 * @param pool_spec Map of pool attributes
	 * @return List of pools matching the attributes
	 */
	public static List<Pool> list(AuthOptions auth, Map<String, Object> pool_spec) throws JnipapException {

		// Create XML-RPC connection
		Connection conn = Connection.getInstance();

		// Build function args
		HashMap<String, Map<String, Object>> args = new HashMap<String, Map<String, Object>>();
		args.put("auth", auth.toMap());
		args.put("pool", pool_spec);

		List<HashMap> params = new ArrayList<HashMap>();
		params.add(args);

		// execute query
		Object[] result = (Object[])conn.execute("list_pool", params);

		// extract data from result
		ArrayList<Pool> ret = new ArrayList<Pool>();

		for (int i = 0; i < result.length; i++) {
			Map<String, Object> result_pool = (Map<String, Object>)result[i];
			ret.add(Pool.fromMap(auth, result_pool));
		}

		return ret;

	}

	/**
	 * Get pool from NIPAP by ID
	 *
	 * Fetch a pool from NIPAP by specifying its ID. If no matching pool
	 * was found, an exception is thrown.
	 *
	 * @param auth Authentication options
	 * @param id ID of requested pool
	 * @return The pool which was found
	 */
	public static Pool get(AuthOptions auth, int id) throws JnipapException {

		// Build pool spec
		HashMap<String, Object> pool_spec = new HashMap<String, Object>();
		pool_spec.put("id", id);

		List<Pool> result = Pool.list(auth, pool_spec);

		// extract data from result
		if (result.size() < 1) {
			throw new NonExistentException("no matching pool found");
		}

		return result.get(0);

	}

	/**
	 * Create pool object from map of pool attributes
	 *
	 * Helper function for creating objects of data received over XML-RPC
	 *
	 * @param input Map with pool attributes
	 * @param auth Authentication options
	 * @return Pool object
	 */
	public static Pool fromMap(AuthOptions auth, Map<String, Object> input) throws JnipapException {

		Pool pool = new Pool();

		pool.id = (Integer)input.get("id");
		pool.name = (String)input.get("name");
		pool.schema = Schema.get(auth, (Integer)input.get("schema"));
		pool.description = (String)input.get("description");
		pool.default_type = (String)input.get("default_type");
		pool.ipv4_default_prefix_length = (Integer)input.get("ipv4_default_prefix_length");
		pool.ipv6_default_prefix_length = (Integer)input.get("ipv6_default_prefix_length");

		return pool;

	}

}
