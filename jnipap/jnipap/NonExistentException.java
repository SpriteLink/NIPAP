package jnipap;

/**
 * A non-existent object was specified
 *
 * Thrown when for example trying to get a prefix from a pool which does not
 * exist or using the .get()-method on an ID which does not exist.
 */
class NonExistentException extends JnipapException {

	// version ID for serialization
	private static final long serialVersionUID = 0L;

	public NonExistentException(String msg) {
		super(msg);
	}

	public NonExistentException(Throwable cause) {
		super(cause);
	}

}
