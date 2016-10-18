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
import jnipap.VRF;
import jnipap.Pool;


public class Prefix extends Jnipap {

	// Prefix attributes
	public Integer family;
	public VRF vrf;
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
	public String customer_id;
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
	public void save(Connection conn, Pool from_pool, AddPrefixOptions opts) throws JnipapException {

		// id should be null when assigning new prefixes
		if (this.id != null) {
			throw new IllegalStateException("prefix id is defined; attempting to assign prefix from prefix when prefix already exists");
		}

		HashMap attr = this.toAttr();

		// add pool to options map
		HashMap pool_spec = new HashMap();
		pool_spec.put("id", from_pool.id);
		opts.put("from-pool", pool_spec);

		// create args map
		HashMap args = new HashMap();
		args.put("auth", conn.authMap());
		args.put("attr", attr);
		args.put("args", opts);

		// create params list
		List params = new ArrayList();
		params.add(args);

		// perform operation
		Map pref = (Map)conn.execute("add_prefix", params);
		Prefix.fromMap(conn, pref, this);

	}

	/**
	 * Save object to NIPAP - assing prefix from prefix
	 */
	public void save(Connection conn, Prefix from_prefix, AddPrefixOptions opts) throws JnipapException {

		// id should be null when assigning new prefixes
		if (this.id != null) {
			throw new IllegalStateException("prefix id is defined; attempting to assign prefix from prefix when prefix already exists");
		}

		HashMap attr = this.toAttr();

		// add prefix to options map - THIS MODIFIES THE MAP WE GOT PASSED
		// Maybe we should create a copy...?
		ArrayList pref_list = new ArrayList();
		pref_list.add(from_prefix.prefix);
		opts.put("from-prefix", pref_list);

		// create args map
		HashMap args = new HashMap();
		args.put("auth", conn.authMap());
		args.put("attr", attr);
		args.put("args", opts);

		// create params list
		List params = new ArrayList();
		params.add(args);

		// perform operation
		Map pref = (Map)conn.execute("add_prefix", params);
		Prefix.fromMap(conn, pref, this);

	}

	/**
	 * Save changes made to existing prefix OR create new fully defined (not
	 * assigned from pool or other prefix) prefix
	 */
	public void save(Connection conn) throws JnipapException {

		HashMap attr = this.toAttr();

		// create args map
		HashMap args = new HashMap();
		args.put("auth", conn.authMap());
		args.put("attr", attr);

		// create params list
		List params = new ArrayList();
		params.add(args);

		// Create new or modify old?
		Map pref;
		if (id == null) {

			// ID null - create new prefix
			pref = (Map)conn.execute("add_prefix", params);


		} else {

			// Prefix exists - modify existing.
			HashMap prefix_spec = new HashMap();
			prefix_spec.put("id", id);
			args.put("prefix", prefix_spec);

			Object[] result = (Object[])conn.execute("edit_prefix", params);

			if (result.length != 1) {
				throw new JnipapException("Prefix edit returned " + result.length + " entries, should be 1.");
			}

			pref = (Map)result[0];

		}

		Prefix.fromMap(conn, pref, this);

	}

	/**
	 * Returns a HashMap of a few of the prefix attributes
	 *
	 * @return Prefix attributes
	 */
	private HashMap toAttr() {

		// create hashmap of prefix attributes
		HashMap attr = new HashMap();
		putUnlessNull(attr, "description", this.description);
		putUnlessNull(attr, "comment", this.comment);
		putUnlessNull(attr, "node", this.node);
		putUnlessNull(attr, "type", this.type);
		putUnlessNull(attr, "country", this.country);
		putUnlessNull(attr, "order_id", this.order_id);
		putUnlessNull(attr, "customer_id", this.customer_id);
		putUnlessNull(attr, "external_key", this.external_key);
		putUnlessNull(attr, "alarm_priority", this.alarm_priority);
		putUnlessNull(attr, "monitor", this.monitor);
		putUnlessNull(attr, "prefix", this.prefix);

		// Pool assigned?
		if (this.pool != null) {
			attr.put("pool_id", this.pool.id);
		}

		// VRF assigned?
		if (this.vrf != null) {
			attr.put("vrf_id", this.vrf.id);
		}

		return attr;

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

		// Build function args
		HashMap args = new HashMap();
		args.put("auth", conn.authMap());
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
			" type: " + this.type +
			" VRF: " + this.vrf;
	}

	/**
	 * Search NIPAP prefixes by specifying a specifically crafted map
	 *
	 * @param conn Connection with auth options
	 * @param query Map describing the search query
	 * @param search_options Search options
	 * @return A map containing search result and metadata
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
	 * @param query Search string
	 * @param search_options Search options
	 * @return A map containing search result and metadata
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
		Map result = (Map)conn.execute("smart_search_prefix", params);

		// extract data from result
		HashMap ret = new HashMap();
		ret.put("search_options", (Map)result.get("search_options"));
		ret.put("interpretation", (Map)result.get("interpretation"));

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
	public static List list(Connection conn, Map prefix_spec) throws JnipapException {

		// Build function args
		HashMap args = new HashMap();
		args.put("auth", conn.authMap());
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
	public static Prefix get(Connection conn, Integer id) throws JnipapException {


		// Build prefix spec
		HashMap prefix_spec = new HashMap();
		prefix_spec.put("id", id);

		List result = Prefix.list(conn, prefix_spec);

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

		return Prefix.fromMap(conn, input, new Prefix());

	}

	/**
	 * Create prefix object from map of prefix attributes
	 *
	 * Update a Prefix object with attributes from map as received over
	 * XML-RPC.
	 *
	 * @param input Map with prefix attributes
	 * @param conn Connection with auth options
	 * @param prefix Prefix object to populate with attributes from map
	 * @return Prefix object
	 */
	public static Prefix fromMap(Connection conn, Map input, Prefix prefix) throws JnipapException {

		prefix.id = (Integer)input.get("id");
		prefix.family = (Integer)input.get("family");
		prefix.prefix = (String)input.get("prefix");
		prefix.display_prefix = (String)input.get("display_prefix");
		prefix.description = (String)input.get("description");
		prefix.comment = (String)input.get("comment");
		prefix.node = (String)input.get("node");
		prefix.type = (String)input.get("type");
		prefix.indent = (Integer)input.get("indent");
		prefix.country = (String)input.get("country");
		prefix.order_id = (String)input.get("order_id");
		prefix.customer_id = (String)input.get("customer_id");
		prefix.external_key = (String)input.get("external_key");
		prefix.authoritative_source = (String)input.get("authoritative_source");
		prefix.alarm_priority = (String)input.get("alarm_priority");
		prefix.monitor = (Boolean)input.get("monitor");
		prefix.display = (Boolean)input.get("display");
		prefix.match = (Boolean)input.get("match");
		prefix.children = (Integer)input.get("children");

		// If pool is not null, fetch pool object
		if (input.get("pool_id") != null) {
			prefix.pool = Pool.get(conn, (Integer)input.get("pool_id"));
		}

		// If VRF is not null, fetch VRF object
		if (input.get("vrf_id") != null) {
			prefix.vrf = VRF.get(conn, (Integer)input.get("vrf_id"));
		}

		return prefix;

	}

	/**
	 * Compute hash of prefix
	 */
	public int hashCode() {

		int hash = super.hashCode();
		hash = hash * 31 + (family == null ? 0 : family.hashCode());
		hash = hash * 31 + (vrf == null ? 0 : vrf.hashCode());
		hash = hash * 31 + (prefix == null ? 0 : prefix.hashCode());
		hash = hash * 31 + (display_prefix == null ? 0 : display_prefix.hashCode());
		hash = hash * 31 + (description == null ? 0 : description.hashCode());
		hash = hash * 31 + (comment == null ? 0 : comment.hashCode());
		hash = hash * 31 + (node == null ? 0 : node.hashCode());
		hash = hash * 31 + (pool == null ? 0 : pool.hashCode());
		hash = hash * 31 + (type == null ? 0 : type.hashCode());
		hash = hash * 31 + (indent == null ? 0 : indent.hashCode());
		hash = hash * 31 + (country == null ? 0 : country.hashCode());
		hash = hash * 31 + (order_id == null ? 0 : order_id.hashCode());
		hash = hash * 31 + (customer_id == null ? 0 : customer_id.hashCode());
		hash = hash * 31 + (external_key == null ? 0 : external_key.hashCode());
		hash = hash * 31 +
			(authoritative_source == null ? 0 : authoritative_source.hashCode());
		hash = hash * 31 + (alarm_priority == null ? 0 : alarm_priority.hashCode());
		hash = hash * 31 + (monitor == null ? 0 : monitor.hashCode());
		hash = hash * 31 + (display == null ? 0 : display.hashCode());
		hash = hash * 31 + (match == null ? 0 : match.hashCode());
		hash = hash * 31 + (children == null ? 0 : children.hashCode());

		return hash;

	}

	/**
	 * Verify equality
	 */
	public boolean equals(Object other) {

		if (!super.equals(other)) return false;
		Prefix pref = (Prefix)other;

		return (
			(family == pref.family ||
				(family != null && family.equals(pref.family))) &&
			(vrf == pref.vrf ||
				(vrf != null && vrf.equals(pref.vrf))) &&
			(description == pref.description ||
				(description != null &&
					description.equals(pref.description))) &&
			(prefix == pref.prefix ||
				(prefix != null && prefix.equals(pref.prefix))) &&
			(display_prefix == pref.display_prefix ||
				(display_prefix != null &&
					display_prefix.equals(pref.display_prefix))) &&
			(description == pref.description ||
				(description != null &&
					description.equals(pref.description))) &&
			(comment == pref.comment ||
				(comment != null &&
					comment.equals(pref.comment))) &&
			(node == pref.node ||
				(node != null && node.equals(pref.node))) &&
			(pool == pref.pool ||
				(pool != null && pool.equals(pref.pool))) &&
			(type == pref.type ||
				(type != null && type.equals(pref.type))) &&
			(indent == pref.indent ||
				(indent != null && indent.equals(pref.indent))) &&
			(country == pref.country ||
				(country != null && country.equals(pref.country))) &&
			(order_id == pref.order_id ||
				(order_id != null && order_id.equals(pref.order_id))) &&
            (customer_id == pref.customer_id ||
				(customer_id != null && customer_id.equals(pref.customer_id))) &&
			(external_key == pref.external_key ||
				(external_key != null &&
					external_key.equals(pref.external_key))) &&
			(authoritative_source == pref.authoritative_source ||
				(authoritative_source != null &&
					authoritative_source.equals(pref.authoritative_source))) &&
			(alarm_priority == pref.alarm_priority ||
				(alarm_priority != null &&
					alarm_priority.equals(pref.alarm_priority))) &&
			(monitor == pref.monitor ||
				(monitor != null && monitor.equals(pref.monitor))) &&
			(display == pref.display ||
				(display != null && display.equals(pref.display))) &&
			(match == pref.match ||
				(match != null && match.equals(pref.match))) &&
			(children == pref.children ||
				(children != null && children.equals(pref.children)))
		);

	}

}
