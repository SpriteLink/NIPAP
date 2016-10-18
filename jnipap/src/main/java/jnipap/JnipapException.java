package jnipap;

/**
 * Top-level Jnipap exception
 */
public class JnipapException extends Exception {

	// version ID for serialization
	private static final long serialVersionUID = 0L;

	public JnipapException(String msg) {
		super(msg);
	}

	public JnipapException(Throwable cause) {
		super(cause);
	}

}
