package jnipap;

/**
 * Thrown when authentication against NIPAP service fails.
 */
class AuthFailedException extends JnipapException {

	// version ID for serialization
	private static final long serialVersionUID = 0L;

	public AuthFailedException(String msg) {
		super(msg);
	}

	public AuthFailedException(Throwable cause) {
		super(cause);
	}

}
