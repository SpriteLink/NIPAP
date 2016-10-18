package jnipap;

/**
 * Invalid value specified
 * Thrown for example when an integer is specified when an IP address is
 * expected.
 */
class ValueException extends JnipapException {

	// version ID for serialization
	private static final long serialVersionUID = 0L;

	public ValueException(String msg) {
		super(msg);
	}

	public ValueException(Throwable cause) {
		super(cause);
	}

}
