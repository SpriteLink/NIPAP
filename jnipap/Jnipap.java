package jnipap;

import jnipap.Connection;
import jnipap.AuthOptions;

/**
 * Base class for all NIPAP object classes (Schema, Pool, Prefix).
 *
 * Maintains an XML-RPC connection to the NIPAP daemon.
 *
 * @author Lukas Garberg <lukas@spritelink.net>
 */
abstract public class Jnipap {

	public int id;

	protected Connection conn;

	/**
	 * Create Jnipap object
	 *
	 * Used by NIPAP object classes to get XML-RPC connection and such things.
	 */
	protected Jnipap() {

		this.conn = Connection.getInstance();

	}

	/**
	 * Save the object to NIPAP
	 */
	abstract public void save(AuthOptions auth);

	/**
	 * Remove object from NIPAP
	 */
	abstract public void remove(AuthOptions auth);

}


/*
 * Jnipap exceptions
 */

/**
 * Top-level Jnipap exception
 *
 * @author Lukas Garberg <lukas@spritelink.net>
 */
class JnipapException extends Exception {

	public JnipapException(String msg) {
		super(msg);
	}

	public JnipapException(Throwable cause) {
		super(cause);
	}

}

class NonExistentException extends JnipapException {

	public NonExistentException(String msg) {
		super(msg);
	}

	public NonExistentException(Throwable cause) {
		super(cause);
	}

}

class InputException extends JnipapException {

	public InputException(String msg) {
		super(msg);
	}

	public InputException(Throwable cause) {
		super(cause);
	}

}

class ConnectionException extends JnipapException {

	public ConnectionException(String msg) {
		super(msg);
	}

	public ConnectionException(Throwable cause) {
		super(cause);
	}

}
