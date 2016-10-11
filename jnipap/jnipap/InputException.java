package jnipap;

/**
 * General input error exception
 */
class InputException extends JnipapException {

	// version ID for serialization
	private static final long serialVersionUID = 0L;

	public InputException(String msg) {
		super(msg);
	}

	public InputException(Throwable cause) {
		super(cause);
	}

}
