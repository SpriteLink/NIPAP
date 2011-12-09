package jnipap;

import jnipap.Connection;

/**
 * Base class for all NIPAP object classes (Schema, Pool, Prefix).
 *
 * Maintains an XML-RPC connection to the NIPAP daemon.
 *
 * @author Lukas Garberg <lukas@spritelink.net>
 */
abstract public class Jnipap {

	public Integer id;

	protected Connection conn;

	/**
	 * Save the object to NIPAP
	 */
	abstract public void save(Connection auth) throws JnipapException;

	/**
	 * Remove object from NIPAP
	 */
	abstract public void remove(Connection auth) throws JnipapException;

}
