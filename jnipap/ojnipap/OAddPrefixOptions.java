package ojnipap;

import java.math.BigDecimal;

import java.sql.SQLData;
import java.sql.SQLInput;
import java.sql.SQLOutput;
import java.sql.SQLException;

import jnipap.AddPrefixOptions;

public class OAddPrefixOptions extends AddPrefixOptions implements SQLData {

	public void readSQL(SQLInput stream, String typeName) throws SQLException {

		// Read data
		BigDecimal family = stream.readBigDecimal();
		BigDecimal prefLength = stream.readBigDecimal();

		// Add the keys which have a non-null value
		if (family != null) {
			put("family", new Integer(family.intValue()));
		}
		if (prefLength != null) {
			put("prefix_length", new Integer(prefLength.intValue()));
		}

    }

	public void writeSQL(SQLOutput stream) throws SQLException {

		Integer family;

		// Write values to stream if defined, otherwise write null.
		if (containsKey("family")) {
			stream.writeBigDecimal(new BigDecimal(((Integer)get("family")).intValue()));
		} else {
			stream.writeBigDecimal(null);
		}
		if (containsKey("prefix_length")) {
			stream.writeBigDecimal(new BigDecimal(((Integer)get("prefix_length")).intValue()));
		} else {
			stream.writeBigDecimal(null);
		}

    }

	public String getSQLTypeName() {

		return "NIPAP_ADD_PREFIX_OPTIONS";

	}

}
