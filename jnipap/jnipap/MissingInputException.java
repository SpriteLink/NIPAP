package jnipap;

/**
 * Missing input data to a remote procedure call
 *
 * This can probably be a RuntimeError instead
 */
class MissingInputException extends InputException {

	// version ID for serialization
	private static final long serialVersionUID = 0L;

	public MissingInputException(String msg) {
		super(msg);
	}

	public MissingInputException(Throwable cause) {
		super(cause);
	}

}
