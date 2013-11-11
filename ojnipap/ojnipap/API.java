package ojnipap;

import java.util.List;
import java.util.ArrayList;
import java.util.Map;
import java.util.HashMap;

import java.sql.DriverManager;
import java.sql.SQLException;

import oracle.sql.ArrayDescriptor;
import oracle.sql.ARRAY;

import jnipap.VRF;
import jnipap.Pool;
import jnipap.Prefix;
import jnipap.Connection;
import jnipap.JnipapException;

import ojnipap.OVRF;
import ojnipap.OPool;
import ojnipap.OConnection;
import ojnipap.OAddPrefixOptions;

public class API {

	/**
	 * Get a VRF from ID
	 *
	 * @param conn Connection object
	 * @param id VRF ID to search for
	 * @return VRF with id `id`
	 */
	public static OVRF getVRF(OConnection conn, int id) throws JnipapException {

		VRF s = VRF.get((jnipap.Connection)conn, new Integer(id));
		return toSQLObj(s);

	}

	/**
	 * Get a list of VRFs
	 *
	 * Returns a list of all VRFs.
	 *
	 * @param conn Connection object
	 * @return All OVRF objects
	 */
	public static ARRAY listVRF(OConnection conn) throws JnipapException {

		HashMap args = new HashMap();
		List result = VRF.list((Connection)conn, args);

		OVRF[] ret = new OVRF[result.size()];
		for (int i = 0; i < result.size(); i++) {
			ret[i] = toSQLObj((VRF)result.get(i));
		}

		return getARRAY("NIPAP_VRF_TBL", (Object)ret);

	}

	/**
	 * Perform a smart VRF search
	 *
	 * @param conn Connection object
	 * @param query Search string
	 * @return Matching VRFs
	 */
	public static ARRAY searchVRF(OConnection conn, String query) throws JnipapException {

		Map result = VRF.search((Connection)conn, query, new HashMap());
		List raw_vrfs = (List)result.get("result");

		OVRF[] ret = new OVRF[raw_vrfs.size()];

		for (int i = 0; i < raw_vrfs.size(); i++) {
			ret[i] = toSQLObj((VRF)raw_vrfs.get(i));
		}

		return getARRAY("NIPAP_VRF_TBL", (Object)ret);

	}

	/**
	 * Get a pool from ID
	 *
	 * @param conn Connection object
	 * @param id Pool ID to search for
	 * @return Pool with ID 'id'
	 */
	public static OPool getPool(OConnection conn, int id) throws JnipapException {

		Pool p = Pool.get((Connection)conn, new Integer(id));
		return toSQLObj(p);

	}

	/**
	 * List pools
	 *
	 * Returns a list of all pools.
	 *
	 * @param conn Connection object
	 * @param All pools
	 */
	public static ARRAY listPool(OConnection conn) throws JnipapException {

		Map pool_spec = new HashMap();
		List result = Pool.list((Connection)conn, pool_spec);

		OPool[] ret = new OPool[result.size()];
		for (int i = 0; i < result.size(); i++) {
			ret[i] = toSQLObj((Pool)result.get(i));
		}

		return getARRAY("NIPAP_POOL_TBL", (Object)ret);

	}

	/**
	 * Perform a smart pool search
	 *
	 * @param conn Connection object
	 * @param query Search string
	 * @return List of search results
	 */
	public static ARRAY searchPool(OConnection conn, String query) throws JnipapException {

		Map result = Pool.search((Connection)conn, query, new HashMap());
		List raw_pools = (List)result.get("result");

		OPool[] ret = new OPool[raw_pools.size()];

		for (int i = 0; i < raw_pools.size(); i++) {
			ret[i] = toSQLObj((Pool)raw_pools.get(i));
		}

		return getARRAY("NIPAP_POOL_TBL", (Object)ret);

	}
	

	/**
	 * Get a prefix from ID
	 *
	 * @param conn Connection object
	 * @param id Prefix ID to search for
	 * @return Prefix with id 'id'
	 */
	public static OPrefix getPrefix(OConnection conn, int id) throws JnipapException {

		Prefix p = Prefix.get((jnipap.Connection)conn, new Integer(id));
		return toSQLObj(p);

	}

	/**
	 * Perform a smart prefix search
	 *
	 * @param conn Connection object
	 * @param query Search string
	 * @param search_options A map of search options
	 * @return List of search results
	 */
	public static ARRAY searchPrefix(OConnection conn, String query, OSearchOptions search_options) throws JnipapException {

		Map result = Prefix.search((jnipap.Connection)conn, query, search_options);
		List raw_prefixes = (List)result.get("result");

		OPrefix[] ret = new OPrefix[raw_prefixes.size()];

		for (int i = 0; i < raw_prefixes.size(); i++) {
			ret[i] = toSQLObj((Prefix)raw_prefixes.get(i));
		}

		return getARRAY("NIPAP_PREFIX_TBL", (Object)ret);

	}

	/**
	 * Perform a smart prefix search
	 *
	 * @param conn Connection object
	 * @param query Search string
	 * @return List of search results
	 */
	public static ARRAY searchPrefix(OConnection conn, String query) throws JnipapException {

		return searchPrefix(conn, query, new OSearchOptions());

	}

	/**
	 * Perform a search in the external_key field.
	 *
	 * Returns a list of prefixes having the external_key attribute set to
	 * `query`. The search is performed using the `equals` operator.
	 *
	 * @param conn Connection object
	 * @param query String to search
	 * @param search_options Search options such as limiting the number of results
	 * @return An array of OPrefix objects matching the search query
	 */
	public static ARRAY searchPrefixExtKey(OConnection conn, String query, OSearchOptions search_options) throws JnipapException {

		// Build search query map
		HashMap search_query = new HashMap();
		search_query.put("operator", "equals");
		search_query.put("val1", "external_key");
		search_query.put("val2", query);

		// Perform search
		Map result = Prefix.search((jnipap.Connection)conn, search_query, search_options);

		// Extract & convert data
		List raw_prefixes = (List)result.get("result");
		OPrefix[] ret = new OPrefix[raw_prefixes.size()];
		for (int i = 0; i < raw_prefixes.size(); i++) {
			ret[i] = toSQLObj((Prefix)raw_prefixes.get(i));
		}

		return getARRAY("NIPAP_PREFIX_TBL", (Object)ret);

	}

	/**
	 * Add prefix from pool
	 *
	 * Create a prefix allocated from the pool 'pool'. The parameter 'pref' is
	 * a prefix object containing the wanted prefix attributes. make sure not
	 * to set the 'prefix' or 'id' attribute, as these will be allocated
	 * automatically.
	 *
	 * @param conn Connection object
	 * @param pref Prefix object which holds attributes
	 * @param pool The pool from which the prefix should be allocated
	 * @param opts Prefix options such as prefix length and family
	 * @return The created prefix object
	 */
	public static OPrefix addPrefix(OConnection conn, OPrefix pref, OPool pool, OAddPrefixOptions opts) throws JnipapException {

		pref.save(conn, pool, opts);
		return toSQLObj(pref);

	}

	/**
	 * Add prefix from prefix
	 *
	 * Create a prefix allocated from another prefix. The parameter 'pref' is a
	 * a prefix object containing the wanted prefix attributes. make sure not
	 * to set the 'prefix' or 'id' attribute, as these will be allocated
	 * automatically.
	 *
	 * @param conn Connection object
	 * @param pref Prefix object which holds attributes
	 * @param from_pref The prefix from which the prefix should be allocated
	 * @param opts Prefix options such as prefix length
	 * @return The created prefix object
	 */
	public static OPrefix addPrefix(OConnection conn, OPrefix pref, OPrefix from_pref, OAddPrefixOptions opts) throws JnipapException {

		pref.save(conn, from_pref, opts);
		return toSQLObj(pref);

	}

	/**
	 * Add completely defined prefix or save changes
	 *
	 * Save changes made to a prefix OR add a completely defined prefix, that
	 * is, not allocated from a pool or another prefix.  If the prefix
	 * attribute 'id' is set, the action will be to save changes, otherwise a
	 * new prefix will be created.
	 *
	 * @param conn Connection object
	 * @param pref Prefix object which holds attributes
	 * @return The created prefix object
	 */
	public static OPrefix addPrefix(OConnection conn, OPrefix pref) throws JnipapException {

		pref.save(conn);
		return toSQLObj(pref);

	}

	/**
	 * Convert VRF to SQLData version
	 *
	 * @param v VRF to convert
	 * @return SQLData-compliant VRF object
	 */
	private static OVRF toSQLObj(VRF v) {

		OVRF sqlobj = new OVRF();
		sqlobj.id = v.id;
		sqlobj.rt = v.rt;
		sqlobj.name = v.name;
		sqlobj.description = v.description;

		return sqlobj;

	}

	/**
	 * Convert Pool to SQLData version
	 *
	 * @param p Pool to convert
	 * @return SQLData-compliant pool object
	 */
	private static OPool toSQLObj(Pool p) {

		OPool sqlobj = new OPool();
		sqlobj.id = p.id;
		sqlobj.name = p.name;
		sqlobj.description = p.description;
		sqlobj.default_type = p.default_type;
		sqlobj.ipv4_default_prefix_length = p.ipv4_default_prefix_length;
		sqlobj.ipv6_default_prefix_length = p.ipv6_default_prefix_length;
		if (p.vrf != null) {
			sqlobj.vrf = toSQLObj(p.vrf);
		}

		return sqlobj;

	}

	/**
	 * Convert Prefix to SQLData version
	 *
	 * @param p Prefix to convert
	 * @return SQLData-compliant prefix object
	 */
	private static OPrefix toSQLObj(Prefix p) {

		OPrefix sqlobj = new OPrefix();
		sqlobj.id = p.id;
		if (p.vrf != null) {
			sqlobj.vrf = toSQLObj(p.vrf);
		}
		sqlobj.prefix = p.prefix;
		sqlobj.display_prefix = p.display_prefix;
		sqlobj.description = p.description;
		sqlobj.node = p.node;
		if (p.pool != null) {
			sqlobj.pool = toSQLObj(p.pool);
		}
		sqlobj.type = p.type;
		sqlobj.indent = p.indent;
		sqlobj.country = p.country;
		sqlobj.order_id = p.order_id;
		sqlobj.customer_id = p.customer_id;
		sqlobj.external_key = p.external_key;
		sqlobj.authoritative_source = p.authoritative_source;
		sqlobj.alarm_priority = p.alarm_priority;
		sqlobj.monitor = p.monitor;
		sqlobj.display = p.display;
		sqlobj.match = p.match;
		sqlobj.children = p.children;

		return sqlobj;

	}

	/**
	 * Create Oracle-style ARRAY
	 *
	 * @param type_name Name of the table type in Oracle
	 * @param data Data to place in the array
	 */
	private static ARRAY getARRAY(String type_name, Object data) throws JnipapException {

		// Create Oracle-friendly array...
		java.sql.Connection oconn;
		ArrayDescriptor desc;
		ARRAY ret;
		try {
			oconn = DriverManager.getConnection("jdbc:default:connection:");
			desc = ArrayDescriptor.createDescriptor(type_name, oconn);
			ret = new ARRAY(desc, oconn, data);
		} catch(SQLException e) {
			throw new JnipapException(e.toString());
		}

		return ret;

	}

}
