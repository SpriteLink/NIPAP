package jnipap;

/**
 * Thrown when invalid parameters were received
 */
class InvalidParameterException extends JnipapException {

	// version ID for serialization
	private static final long serialVersionUID = 0L;

	public InvalidParameterException(String msg) {
		super(msg);
	}

	public InvalidParameterException(Throwable cause) {
		super(cause);
	}

}
