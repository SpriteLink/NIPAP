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

	public Integer id;

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
	abstract public void save(AuthOptions auth) throws JnipapException;

	/**
	 * Remove object from NIPAP
	 */
	abstract public void remove(AuthOptions auth) throws ConnectionException;

}


/*
 * Jnipap exceptions
 *
 * TODO: some of these should probably inherit from the RuntimeError exception
 * instead, as they deal with programming errors (missing input, invalid operator)
 */

/**
 * Top-level Jnipap exception
 */
class JnipapException extends Exception {

	public JnipapException(String msg) {
		super(msg);
	}

	public JnipapException(Throwable cause) {
		super(cause);
	}

}

/**
 * General input error exception
 */
class InputException extends JnipapException {

	public InputException(String msg) {
		super(msg);
	}

	public InputException(Throwable cause) {
		super(cause);
	}

}

/**
 * Missing input data to a remote procedure call
 *
 * This can probably be a RuntimeError instead
 */
class MissingInputException extends InputException {

	public MissingInputException(String msg) {
		super(msg);
	}

	public MissingInputException(Throwable cause) {
		super(cause);
	}

}

/**
 * A non-existens object was specified
 *
 * Thrown when for example trying to get a prefix from a pool which does not
 * exist or using the .get()-method on an ID which does not exist.
 */
class NonExistentException extends JnipapException {

	public NonExistentException(String msg) {
		super(msg);
	}

	public NonExistentException(Throwable cause) {
		super(cause);
	}

}

/**
 * Invalid value specified
 * Thrown for example when an integer is specified when an IP address is
 * expected.
 */
class ValueException extends JnipapException {

	public ValueException(String msg) {
		super(msg);
	}

	public ValueException(Throwable cause) {
		super(cause);
	}

}

/**
 * The requested addition/change viloates unique constraints
 *
 * For example, create a schema with a name of an already existing one.
 */
class DuplicateException extends JnipapException {

	public DuplicateException(String msg) {
		super(msg);
	}

	public DuplicateException(Throwable cause) {
		super(cause);
	}

}

/**
 * Connection related errors
 *
 * Timeouts, ...
 */
class ConnectionException extends JnipapException {

	public ConnectionException(String msg) {
		super(msg);
	}

	public ConnectionException(Throwable cause) {
		super(cause);
	}

}

/**
 * Thrown when authentication against NIPAP service fails.
 */
class AuthFailedException extends JnipapException {

	public AuthFailedException(String msg) {
		super(msg);
	}

}
