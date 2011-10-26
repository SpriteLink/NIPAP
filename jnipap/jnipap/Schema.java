package jnipap;

import java.util.HashMap;
import java.util.Map;
import java.util.List;
import java.util.ArrayList;

import org.apache.xmlrpc.XmlRpcException;

import jnipap.NonExistentException;
import jnipap.ConnectionException;
import jnipap.Connection;

public class Schema extends Jnipap {

	// Schema attributes
	public String name;
	public String description;
	public String vrf;

	/**
	 * Creates new schema object
	 */
	public Schema() {

		this.conn = Connection.getInstance();

	}

	/**
	 * Save object to NIPAP
	 */
	public void save(AuthOptions auth) throws ConnectionException {

		// create hashmap of schema attributes
		HashMap<String, Object> attr = new HashMap<String, Object>();
		attr.put("name", this.name);
		attr.put("description", this.description);
		attr.put("vrf", this.vrf);

		// create schema spec
		HashMap<String, Object> schema_spec = new HashMap<String, Object>();
		schema_spec.put("id", this.id);

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

			// ID null - create new schema
			cmd = "add_schema";

		} else {

			// Schema exists - modify existing.
			args.put("schema", schema_spec);
			cmd = "edit_schema";

		}

		// perform operation
		Object[] result;
		try {
			result = (Object[])conn.connection.execute(cmd, params);
		} catch(XmlRpcException e) {
			throw new ConnectionException(e);
		}

		// If we added a new schema, fetch and set ID
		if (this.id == null) {
			this.id = (Integer)result[0];
		}

	}

	/**
	 * Remove object from NIPAP
	 */
	public void remove(AuthOptions auth) throws ConnectionException {

		// Build schema spec
		HashMap<String, Object> schema_spec = new HashMap<String, Object>();
		schema_spec.put("id", this.id);

		// Build function args
		HashMap<String, Map<String, Object>> args = new HashMap<String, Map<String, Object>>();
		args.put("auth", auth.toMap());
		args.put("schema", schema_spec);

		List<HashMap> params = new ArrayList<HashMap>();
		params.add(args);

		// execute query
		Object[] result;
		try {
			result = (Object[])conn.connection.execute("remove_schema", params);
		} catch(XmlRpcException e) {
			throw new ConnectionException(e);
		}

	}

	/**
	 * Return a string representation of a schema
	 */
	public String toString() {

		// Return string representation of a schema
		return getClass().getName() + " id: " + this.id +
			" name: " + this.name +
			" desc: " + this.description +
			" vrf: " + this.vrf;

	}

	/**
	 * Get schema from NIPAP by ID
	 *
	 * Fetch the schema from NIPAP by specifying its ID. If no matching schema
	 * was found, an exception is thrown.
	 *
	 * @param auth Authentication options
	 * @param id ID of requested schema
	 * @return The schema which was found
	 */
	public static Schema get(AuthOptions auth, int id) throws NonExistentException, ConnectionException {

		// Create XML-RPC connection
		Connection conn = Connection.getInstance();

		// Build schema spec
		HashMap<String, Object> schema_spec = new HashMap<String, Object>();
		schema_spec.put("id", id);

		// Build function args
		HashMap<String, Map<String, Object>> args = new HashMap<String, Map<String, Object>>();
		args.put("auth", auth.toMap());
		args.put("schema", schema_spec);

		List<HashMap> params = new ArrayList<HashMap>();
		params.add(args);

		// execute query
		Object[] result;
		try {
			result = (Object[])conn.connection.execute("list_schema", params);
		} catch(XmlRpcException e) {
			throw new ConnectionException(e);
		}

		// extract data from result
		if (result.length < 1) {
			throw new NonExistentException("no matching schema found");
		}

		HashMap<String, Object> result_schema = (HashMap<String, Object>)result[0];

		return Schema.fromMap(result_schema);

	}

	/**
	 * Create schema object from map of schema attributes
	 *
	 * Helper function for creating objects of data received over XML-RPC
	 *
	 * @param input Map with schema attributes
	 * @return Schema object
	 */
	public static Schema fromMap(Map<String, Object> input) {

		Schema schema = new Schema();

		schema.id = (Integer)input.get("id");
		schema.name = (String)input.get("name");
		schema.description = (String)input.get("description");
		schema.vrf = (String)input.get("vrf");

		return schema;

	}
}
