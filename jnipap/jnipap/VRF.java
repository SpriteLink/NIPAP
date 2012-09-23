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

public class VRF extends Jnipap {

	// VRF attributes
	public String rt;
	public String name;
	public String description;

	/**
	 * Save object to NIPAP
	 *
	 * @param auth Authentication options
	 */
	public void save(Connection conn) throws JnipapException {

		// create hashmap of VRF attributes
		HashMap attr = new HashMap();
		attr.put("rt", this.rt);
		attr.put("name", this.name);
		attr.put("description", this.description);

		// create VRF spec
		HashMap vrf_spec = new HashMap();
		vrf_spec.put("id", this.id);

		// create args map
		HashMap args = new HashMap();
		args.put("auth", conn.authMap());
		args.put("attr", attr);

		// create params list
		List params = new ArrayList();
		params.add(args);

		// Create new or modify old?
		String cmd;
		if (this.id == null) {

			// ID null - create new VRF
			cmd = "add_vrf";

		} else {

			// VRF exists - modify existing.
			args.put("vrf", vrf_spec);
			cmd = "edit_vrf";

		}

		// perform operation
		Integer result = (Integer)conn.execute(cmd, params);

		// If we added a new VRF, fetch and set ID
		if (this.id == null) {
			this.id = result;
		}

	}

	/**
	 * Remove object from NIPAP
	 *
	 * @param auth Authentication options
	 */
	public void remove(Connection conn) throws JnipapException {

		// Build VRF spec
		HashMap vrf_spec = new HashMap();
		vrf_spec.put("id", this.id);

		// Build function args
		HashMap args = new HashMap();
		args.put("auth", conn.authMap());
		args.put("vrf", vrf_spec);

		List params = new ArrayList();
		params.add(args);

		// execute query
		Object[] result = (Object[])conn.execute("remove_vrf", params);

	}

	/**
	 * Return a string representation of a VRF
	 *
	 * @return String describing the VRF and its attributes
	 */
	public String toString() {

		// Return string representation of a VRF
		return getClass().getName() + " id: " + this.id +
			" rt: " + this.rt +
			" name: " + this.name +
			" desc: " + this.description;

	}

	/**
	 * Get list of VRFs from NIPAP by its attributes
	 *
	 * @param auth Authentication options
	 * @param query Map describing the search query
	 * @param search_options Search options
	 * @return A list of VRF objects matching the attributes in the vrf_spec
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
		Map result = (Map)conn.execute("search_vrf", params);

		// extract data from result
		HashMap ret = new HashMap();
		ret.put("search_options", (Map)result.get("search_options"));
		ArrayList ret_vrfs = new ArrayList();

		Object[] result_vrfs = (Object[])result.get("result");

		for (int i = 0; i < result_vrfs.length; i++) {
			Map result_vrf = (Map)result_vrfs[i];
			ret_vrfs.add(VRF.fromMap(result_vrf));
		}

		ret.put("result", ret_vrfs);

		return ret;

	}

	/**
	 * Get list of VRFs from NIPAP by a string
	 *
	 * @param auth Authentication options
	 * @param query Search string
	 * @param search_options Search options
	 * @return A list of VRF objects matching the attributes in the vrf_spec
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
		Map result = (Map)conn.execute("smart_search_vrf", params);

		// extract data from result
		HashMap ret = new HashMap();
		ret.put("search_options", (Map)result.get("search_options"));

		Object[] interpretation_result = (Object[])result.get("interpretation");
		List ret_interpretation = new ArrayList();
		for (int i = 0; i < interpretation_result.length; i++) {
			ret_interpretation.add((Map)interpretation_result[i]);
		}
		ret.put("interpretation", ret_interpretation);

		ArrayList ret_vrfs = new ArrayList();
		Object[] result_vrfs = (Object[])result.get("result");
		for (int i = 0; i < result_vrfs.length; i++) {
			Map result_vrf = (Map)result_vrfs[i];
			ret_vrfs.add(VRF.fromMap(result_vrf));
		}
		ret.put("result", ret_vrfs);

		return ret;

	}

	/**
	 * List VRFs having specified attributes
	 *
	 * @param auth Authentication options
	 * @param vrf_spec Map where attributes can be specified
	 */
	public static List list(Connection conn, Map vrf_spec) throws JnipapException {

		// Build function args
		HashMap args = new HashMap();
		args.put("auth", conn.authMap());
		args.put("vrf", vrf_spec);

		List params = new ArrayList();
		params.add(args);

		// execute query
		Object[] result = (Object[])conn.execute("list_vrf", params);

		// extract data from result
		ArrayList ret = new ArrayList();

		for (int i = 0; i < result.length; i++) {
			Map result_vrf = (Map)result[i];
			ret.add(VRF.fromMap(result_vrf));
		}

		return ret;

	}

	/**
	 * Get VRF from NIPAP by ID
	 *
	 * Fetch the VRF from NIPAP by specifying its ID. If no matching VRF
	 * is found, an exception is thrown.
	 *
	 * @param auth Authentication options
	 * @param id ID of requested VRF
	 * @return The VRF which was found
	 */
	public static VRF get(Connection conn, Integer id) throws JnipapException {

		// Build VRF spec
		HashMap vrf_spec = new HashMap();
		vrf_spec.put("id", id);

		List result = VRF.list(conn, vrf_spec);

		// extract data from result
		if (result.size() < 1) {
			throw new NonExistentException("no matching VRF found");
		}

		return (VRF)result.get(0);

	}

	/**
	 * Create VRF object from map of VRF attributes
	 *
	 * Helper function for creating objects of data received over XML-RPC
	 *
	 * @param input Map with VRF attributes
	 * @return VRF object
	 */
	public static VRF fromMap(Map input) {

		VRF vrf = new VRF();

		vrf.id = (Integer)input.get("id");
		vrf.rt = (String)input.get("rt");
		vrf.name = (String)input.get("name");
		vrf.description = (String)input.get("description");

		return vrf;

	}

}
