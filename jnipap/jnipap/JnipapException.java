package jnipap;

/*
 * Jnipap exceptions
 *
 * TODO: some of these should probably inherit from the RuntimeError exception
 * instead, as they deal with programming errors (missing input, invalid operator)
 */

/**
 * Top-level Jnipap exception
 */
public class JnipapException extends Exception {

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
 * For example, when creating a VRF which already exists.
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

	public AuthFailedException(Throwable cause) {
		super(cause);
	}

}

/**
 * Thrown when invalid parameters were received
 */
class InvalidParameterException extends JnipapException {

	public InvalidParameterException(String msg) {
		super(msg);
	}

	public InvalidParameterException(Throwable cause) {
		super(cause);
	}

}
