package jnipap;

/**
 * The requested addition/change violates unique constraints
 *
 * For example, when creating a VRF which already exists.
 */
class DuplicateException extends JnipapException {

	// version ID for serialization
	private static final long serialVersionUID = 0L;

	public DuplicateException(String msg) {
		super(msg);
	}

	public DuplicateException(Throwable cause) {
		super(cause);
	}

}
