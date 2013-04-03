package ojnipap;

import java.math.BigDecimal;

import java.sql.SQLInput;
import java.sql.SQLException;

class Helpers {

	/**
	 * Take string and return Oracle-friendly value
	 *
	 * As Oracle handles empty strings as null, it seems as empty strings needs
	 * to be converted to null before sent to writeString.
	 *
	 * @param str Input string
	 * @return String or null
	 */
	static String strOrNull(String str) {

		if (str == null) {
			return str;
		}

		if (str.length() == 0) {
			return null;
		} else {
			return str;
		}

	}

	/**
	 * Convert Boolean to BigDecimal
	 *
	 * As Oracle lacks a boolean type, they have in ojnipap been implemented as
	 * the type NUMBER(1). This function handles conversion from boolean to
	 * BigDecimal; if the input boolean is true the function returns a
	 * BigDecimal with the value 1, otherwise 0.
	 *
	 * @param b Boolean value
	 * @return A BigDecimal with values 0 or 1
	 */
	static BigDecimal bigDecBoolOrNull(Boolean b) {

		if (b == null) {
			return null;
		}

		return new BigDecimal(b.booleanValue() ? 1 : 0);

	}

	/**
	 * Take Integer and return Oracle-friendly value
	 *
	 * This function returns either a BigDecimal suitable for the
	 * writeBigDecimal function, or null if the input value is null.
	 *
	 * @param i Input integer
	 * @return BigDecimal with value of input integer, or null
	 */
	static BigDecimal bigDecOrNull(Integer i) {

		if (i == null) {
			return null;
		}
		
		return new BigDecimal(i.intValue());

	}

	/**
	 * Read BigDecimal value from stream and return Integer or null
	 *
	 * This helper function reads a BigDecimal from the stream. If the stream
	 * contains a null value, null is returned. Otherwise an Integer object
	 * with the requested value is returned.
	 *
	 * @param val stream to read data from
	 * @return Integer object
	 */
	static Integer integerOrNull(BigDecimal val) throws SQLException {

		if (val == null) {
			return null;
		}

		return new Integer(val.intValue());

	}

}
