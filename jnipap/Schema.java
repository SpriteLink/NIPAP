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
	public void save(AuthOptions auth) {

		// create hashmap of schema attributes

		// perform XML-RPC call

	}

	public void remove(AuthOptions auth) {

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

		Schema schema = new Schema();

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
		schema.id = (Integer)result_schema.get("id");
		schema.name = (String)result_schema.get("name");
		schema.description = (String)result_schema.get("description");
		schema.vrf = (String)result_schema.get("vrf");

		return schema;

	}
}
