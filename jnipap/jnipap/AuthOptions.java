package jnipap;

import java.util.HashMap;
import java.util.Map;

/**
 * NIPAP authentication options
 * 
 * A class which contains the different authentication options which can be
 * used in API NIPAP calls.
 * 
 * @author Lukas Garberg <lukas@spritelink.net>
 */
public class AuthOptions {

	public String full_name;
	public String authoritative_source = "jnipap";
	public String username;

	/**
	 * Dummy constructor
	 */
	public AuthOptions() {
		super();
	}

	/**
	 * Return a Map-representation of the auth options
	 *
	 * @return Map of authentication options
	 */
	public Map<String, Object> toMap() {
 
		HashMap<String, Object> map = new HashMap<String, Object>();

		// Add non-null elements
		if (this.full_name != null) {
			map.put("full_name", this.full_name);
		}

		if (this.authoritative_source != null) {
			map.put("authoritative_source", this.authoritative_source);
		}

		if (this.username != null) {
			map.put("username", this.username);
		}

		return (Map<String, Object>)map;

	}

}
