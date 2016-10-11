package jnipap;

/**
 * Connection related errors
 *
 * Timeouts, ...
 */
public class ConnectionException extends JnipapException {

	// version ID for serialization
	private static final long serialVersionUID = 0L;

	public ConnectionException(String msg) {
		super(msg);
	}

	public ConnectionException(Throwable cause) {
		super(cause);
	}

}
