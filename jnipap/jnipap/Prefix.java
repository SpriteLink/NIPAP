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
import jnipap.Pool;


public class Prefix extends Jnipap {

	// Prefix attributes
	public Integer family;
	public Schema schema;
	public String prefix;
	public String display_prefix;
	public String description;
	public String comment;
	public String node;
	public Pool pool;
	public String type;
	public Integer indent;
	public String country;
	public String order_id;
	public String external_key;
	public String authoritative_source;
	public String alarm_priority;
	public Boolean monitor;
	public Boolean display;
	public Boolean match;
	public Integer children = new Integer(-2);

	/**
	 * Save object to NIPAP - assign prefix from pool
	 */
	 /*
	public void save(AuthOptions auth, Pool from_pool, Integer inet_family) throws JnipapException {

		// id should be null when assigning new prefixes
		if (this.id != null) {
			throw new IllegalStateException("attempting to assign prefix from pool when prefix already exists");
		}

		HashMap<String, Object> attr = this.toAttr();
		attr.put("schema", this.schema.id);
		attr.put("family", this.family);

		HashMap<String, Object> schema_spec = new HashMap<String, Object>();
		schema_spec.put("id", this.schema.id);

		// create args map
		HashMap<String, Map<String, Object>> args = new HashMap<String, Map<String, Object>>();
		args.put("auth", auth.toMap());
		args.put("attr", attr);
		args.put("schema", schema_spec);

		// create params list
		List<HashMap> params = new ArrayList<HashMap>();
		params.add(args);

		// perform operation
		this.id = (Integer)conn.execute(cmd, params);

	}
	*/


	/**
	 * Save object to NIPAP - assing prefix from prefix
	 */
	 /*
	public void save(AuthOptions auth, Prefix from_prefix, Integer prefix_length) throws JnipapException {

		// id should be null when assigning new prefixes
		if (this.id != null) {
			throw new IllegalStateException("attempting to assign prefix from prefix when prefix already exists");
		}

		HashMap<String, Object> attr = this.toAttr();
		attr.put("schema", this.schema.id);

		HashMap<String, Object> schema_spec = new HashMap<String, Object>();
		schema_spec.put("id", this.schema.id);

		// create args map
		HashMap<String, Map<String, Object>> args = new HashMap<String, Map<String, Object>>();
		args.put("auth", auth.toMap());
		args.put("attr", attr);
		args.put("schema", schema_spec);

		// create params list
		List<HashMap> params = new ArrayList<HashMap>();
		params.add(args);


		// perform operation
		this.id = (Integer)conn.execute(cmd, params);

	}
	*/

	/**
	 * Returns a HashMap of a few of the prefix attributes
	 *
	 * @return Prefix attributes
	 */
	private HashMap toAttr() {

		// TODO: handle schema = null

		// create hashmap of prefix attributes
		HashMap attr = new HashMap();
		putUnlessNull(attr, "description", this.description);
		putUnlessNull(attr, "comment", this.comment);
		putUnlessNull(attr, "node", this.node);
		putUnlessNull(attr, "type", this.type);
		putUnlessNull(attr, "country", this.country);
		putUnlessNull(attr, "order_id", this.order_id);
		putUnlessNull(attr, "external_key", this.external_key);
		putUnlessNull(attr, "alarm_priority", this.alarm_priority);
		putUnlessNull(attr, "monitor", this.monitor);
		putUnlessNull(attr, "prefix", this.prefix);

		// Pool assigned?
		if (this.pool != null) {
			attr.put("pool", this.pool.id);
		}

		return attr;

	}
	

	/**
	 * Save object to NIPAP
	 *
	 * @param conn Connection with auth options
	 */
	public void save(Connection conn, HashMap assign_args) throws JnipapException {

		HashMap attr = this.toAttr();

		// create schema spec
		HashMap schema_spec = new HashMap();
		if (this.schema != null) { 
			schema_spec.put("id", this.schema.id);
		} else {
			// throw exception?
		}

/*
		HashMap<String, Object> assign_args_out = new HashMap<String, Object>();
		if ("from-pool") {
			assign_args_out.put("from-pool", assign_args.get("from-pool"));
		}
		if ("from-prefix") {
			assign_args_out.put("from-prefix", assign_args.get("from-prefix"));
		}
		if ("family") {
			assign_args_out.put("family", assign_args.get("family"));
		}
		if ("prefix_length") {
			assign_args_out.put("prefix_length", assign_args.get("prefix_length"));
		}
*/

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

			// ID null - create new prefix
			if (this.schema != null) {
				attr.put("schema", this.schema.id);
			}
			cmd = "add_prefix";
			args.put("args", assign_args);

		} else {

			// Prefix exists - modify existing.
			HashMap prefix_spec = new HashMap();
			prefix_spec.put("id", this.id);
			args.put("prefix", prefix_spec);
			cmd = "edit_prefix";

		}

		// perform operation
		Integer result = (Integer)conn.execute(cmd, params);

		// If we added a new prefix, fetch and set ID
		if (this.id == null) {
			this.id = result;

			// Get new prefix data
			Prefix p = Prefix.get(conn, this.schema, this.id);
			this.prefix = p.prefix;
			this.display_prefix = p.display_prefix;
			this.indent = p.indent;
			this.family = p.family;
			this.authoritative_source = p.authoritative_source;
			this.alarm_priority = p.alarm_priority;
			this.monitor = p.monitor;
		}

	}

	/**
	 * Save object to NIPAP
	 *
	 * @param conn Connection with auth options
	 */
	public void save(Connection conn) throws JnipapException {

		HashMap assign_args = new HashMap();
		this.save(conn, assign_args);

	}

	/**
	 * Remove object from NIPAP
	 *
	 * @param conn Connection with auth options
	 */
	public void remove(Connection conn) throws JnipapException {

		// Build prefix spec
		HashMap prefix_spec = new HashMap();
		prefix_spec.put("id", this.id);

		HashMap schema_spec = new HashMap();
		schema_spec.put("id", this.schema.id);

		// Build function args
		HashMap args = new HashMap();
		args.put("auth", conn.authMap());
		args.put("schema", schema_spec);
		args.put("prefix", prefix_spec);

		List params = new ArrayList();
		params.add(args);

		// execute query
		Object[] result = (Object[])conn.execute("remove_prefix", params);

	}

	/**
	 * Return a string representation of a prefix
	 *
	 * @return String describing the prefix and its attributes
	 */
	public String toString() {

		// Return string representation of a prefix
		return getClass().getName() + " id: " + this.id +
			" prefix: " + this.prefix +
			" display_prefix: " + this.display_prefix +
			" desc: " + this.description +
			" type: " + this.type;
	}

	/**
	 * Search NIPAP prefixes by specifying a specifically crafted map
	 *
	 * @param conn Connection with auth options
	 * @param schema Schema to search
	 * @param query Map describing the search query
	 * @param search_options Search options
	 * @return A map containing search result and metadata
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
		Map result = (Map)conn.execute("search_prefix", params);

		// extract data from result
		HashMap ret = new HashMap();
		ret.put("search_options", (Map)result.get("search_options"));
		ArrayList ret_prefixes = new ArrayList();

		Object[] result_prefixes = (Object[])result.get("result");

		for (int i = 0; i < result_prefixes.length; i++) {
			Map result_prefix = (Map)result_prefixes[i];
			ret_prefixes.add(Prefix.fromMap(conn, result_prefix));
		}

		ret.put("result", ret_prefixes);

		return ret;

	}

	/**
	 * Search NIPAP prefixes by specifying a search string
	 *
	 * @param conn Connection with auth options
	 * @param schema Schema to search
	 * @param query Search string
	 * @param search_options Search options
	 * @return A map containing search result and metadata 
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
		Map result = (Map)conn.execute("smart_search_prefix", params);

		// extract data from result
		HashMap ret = new HashMap();
		ret.put("search_options", (Map)result.get("search_options"));

		Object[] interpretation_result = (Object[])result.get("interpretation");
		List ret_interpretation = new ArrayList();
		for (int i = 0; i < interpretation_result.length; i++) {
			ret_interpretation.add((Map)interpretation_result[i]);
		}
		ret.put("interpretation", ret_interpretation);

		ArrayList ret_prefixes = new ArrayList();
		Object[] result_prefixes = (Object[])result.get("result");
		for (int i = 0; i < result_prefixes.length; i++) {
			Map result_prefix = (Map)result_prefixes[i];
			ret_prefixes.add(Prefix.fromMap(conn, result_prefix));
		}
		ret.put("result", ret_prefixes);

		return ret;

	}

	/**
	 * List prefixes with specified attributes
	 *
	 * @param conn Connection with auth options
	 * @param prefix_spec Map of prefix attributes
	 * @return List of prefixes matching the attributes
	 */
	public static List list(Connection conn, Schema schema, Map prefix_spec) throws JnipapException {

		HashMap schema_spec = new HashMap();
		schema_spec.put("id", schema.id);

		// Build function args
		HashMap args = new HashMap();
		args.put("auth", conn.authMap());
		args.put("schema", schema_spec);
		args.put("prefix", prefix_spec);

		List params = new ArrayList();
		params.add(args);

		// execute query
		Object[] result = (Object[])conn.execute("list_prefix", params);

		// extract data from result
		ArrayList ret = new ArrayList();

		for (int i = 0; i < result.length; i++) {
			Map result_prefix = (Map)result[i];
			ret.add(Prefix.fromMap(conn, result_prefix));
		}

		return ret;

	}

	/**
	 * Get prefix from NIPAP by ID
	 *
	 * Fetch a prefix from NIPAP by specifying its ID. If no matching prefix
	 * was found, an exception is thrown.
	 *
	 * @param conn Connection with auth options
	 * @param id ID of requested prefix
	 * @return The prefix which was found
	 */
	public static Prefix get(Connection conn, Schema schema, Integer id) throws JnipapException {

		// Build prefix spec
		HashMap prefix_spec = new HashMap();
		prefix_spec.put("id", id);

		List result = Prefix.list(conn, schema, prefix_spec);

		// extract data from result
		if (result.size() < 1) {
			throw new NonExistentException("no matching prefix found");
		}

		return (Prefix)result.get(0);

	}

	/**
	 * Create prefix object from map of prefix attributes
	 *
	 * Helper function for creating objects of data received over XML-RPC
	 *
	 * @param input Map with prefix attributes
	 * @param conn Connection with auth options
	 * @return Prefix object
	 */
	public static Prefix fromMap(Connection conn, Map input) throws JnipapException {

		Prefix prefix = new Prefix();

		prefix.id = (Integer)input.get("id");
		prefix.family = (Integer)input.get("family");
		prefix.schema = Schema.get(conn, (Integer)input.get("schema"));
		prefix.prefix = (String)input.get("prefix");
		prefix.display_prefix = (String)input.get("display_prefix");
		prefix.description = (String)input.get("description");
		prefix.comment = (String)input.get("comment");
		prefix.node = (String)input.get("node");
		prefix.type = (String)input.get("type");
		prefix.indent = (Integer)input.get("indent");
		prefix.country = (String)input.get("country");
		prefix.order_id = (String)input.get("order_id");
		prefix.external_key = (String)input.get("external_key");
		prefix.authoritative_source = (String)input.get("authoritative_source");
		prefix.alarm_priority = (String)input.get("alarm_priority");
		prefix.monitor = (Boolean)input.get("monitor");
		prefix.display = (Boolean)input.get("display");
		prefix.match = (Boolean)input.get("match");
		prefix.children = (Integer)input.get("children");

		// If pool is not null, fetch pool object
		if (input.get("pool") != null) {
			prefix.pool = Pool.get(conn, prefix.schema, (Integer)input.get("pool"));
		}

		return prefix;

	}

}
