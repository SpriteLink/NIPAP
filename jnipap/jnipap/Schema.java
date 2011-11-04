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

public class Schema extends Jnipap {

	// Schema attributes
	public String name;
	public String description;
	public String vrf;

	/**
	 * Creates new schema object
	 */
	public Schema() {

		super();

	}

	/**
	 * Save object to NIPAP
	 *
	 * @param auth Authentication options
	 */
	public void save(AuthOptions auth) throws JnipapException {

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
		Integer result = (Integer)conn.execute(cmd, params);

		// If we added a new schema, fetch and set ID
		if (this.id == null) {
			this.id = result;
		}

	}

	/**
	 * Remove object from NIPAP
	 *
	 * @param auth Authentication options
	 */
	public void remove(AuthOptions auth) throws JnipapException {

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
		Object[] result = (Object[])conn.execute("remove_schema", params);

	}

	/**
	 * Return a string representation of a schema
	 *
	 * @return String describing the schema and its attributes
	 */
	public String toString() {

		// Return string representation of a schema
		return getClass().getName() + " id: " + this.id +
			" name: " + this.name +
			" desc: " + this.description +
			" vrf: " + this.vrf;

	}

	/**
	 * Get list of schemas from NIPAP by its attributes
	 *
	 * @param auth Authentication options
	 * @param query Map describing the search query
	 * @param search_options Search options
	 * @return A list of Schema objects matching the attributes in the schema_spec
	 */
	public static Map<String, Object> search(AuthOptions auth, Map<String, Object> query, Map<String, Object> search_options) throws JnipapException {

		// Create XML-RPC connection
		Connection conn = Connection.getInstance();

		// Build function args
		HashMap<String, Map<String, Object>> args = new HashMap<String, Map<String, Object>>();
		args.put("auth", auth.toMap());
		args.put("query", query);
		args.put("search_options", search_options);

		List<HashMap> params = new ArrayList<HashMap>();
		params.add(args);

		// execute query
		Map result = (Map)conn.execute("search_schema", params);

		// extract data from result
		HashMap<String, Object> ret = new HashMap<String, Object>();
		ret.put("search_options", (Map)result.get("search_options"));
		ArrayList<Schema> ret_schemas = new ArrayList<Schema>();

		Object[] result_schemas = (Object[])result.get("result");

		for (int i = 0; i < result_schemas.length; i++) {
			Map<String, Object> result_schema = (Map<String, Object>)result_schemas[i];
			ret_schemas.add(Schema.fromMap(result_schema));
		}

		ret.put("result", ret_schemas);

		return ret;

	}

	/**
	 * Get list of schemas from NIPAP by a string
	 *
	 * @param auth Authentication options
	 * @param query Search string
	 * @param search_options Search options
	 * @return A list of Schema objects matching the attributes in the schema_spec
	 */
	public static Map<String, Object> search(AuthOptions auth, String query, Map<String, Object> search_options) throws JnipapException {

		// Create XML-RPC connection
		Connection conn = Connection.getInstance();

		// Build function args
		HashMap<String, Object> args = new HashMap<String, Object>();
		args.put("auth", auth.toMap());
		args.put("query_string", query);
		args.put("search_options", search_options);

		List<HashMap> params = new ArrayList<HashMap>();
		params.add(args);

		// execute query
		Map result = (Map)conn.execute("smart_search_schema", params);

		// extract data from result
		HashMap<String, Object> ret = new HashMap<String, Object>();
		ret.put("search_options", (Map)result.get("search_options"));

		Object[] interpretation_result = (Object[])result.get("interpretation");
		List<Map> ret_interpretation = new ArrayList<Map>();
		for (int i = 0; i < interpretation_result.length; i++) {
			ret_interpretation.add((Map)interpretation_result[i]);
		}
		ret.put("interpretation", ret_interpretation);

		ArrayList<Schema> ret_schemas = new ArrayList<Schema>();
		Object[] result_schemas = (Object[])result.get("result");
		for (int i = 0; i < result_schemas.length; i++) {
			Map<String, Object> result_schema = (Map<String, Object>)result_schemas[i];
			ret_schemas.add(Schema.fromMap(result_schema));
		}
		ret.put("result", ret_schemas);

		return ret;

	}

	/**
	 * List schemas having specified attributes
	 *
	 * @param auth Authentication options
	 * @param schema_spec Map where attributes can be specified
	 */
	public static List<Schema> list(AuthOptions auth, Map<String, Object> schema_spec) throws JnipapException {

		// Create XML-RPC connection
		Connection conn = Connection.getInstance();

		// Build function args
		HashMap<String, Map<String, Object>> args = new HashMap<String, Map<String, Object>>();
		args.put("auth", auth.toMap());
		args.put("schema", schema_spec);

		List<HashMap> params = new ArrayList<HashMap>();
		params.add(args);

		// execute query
		Object[] result = (Object[])conn.execute("list_schema", params);

		// extract data from result
		ArrayList<Schema> ret = new ArrayList<Schema>();

		for (int i = 0; i < result.length; i++) {
			Map<String, Object> result_schema = (	Map<String, Object>)result[i];
			ret.add(Schema.fromMap(result_schema));
		}

		return ret;

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
	public static Schema get(AuthOptions auth, int id) throws JnipapException {

		// Build schema spec
		HashMap<String, Object> schema_spec = new HashMap<String, Object>();
		schema_spec.put("id", id);

		List<Schema> result = Schema.list(auth, schema_spec);

		// extract data from result
		if (result.size() < 1) {
			throw new NonExistentException("no matching schema found");
		}

		return result.get(0);

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
