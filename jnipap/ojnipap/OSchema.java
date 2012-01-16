package ojnipap;

import java.util.ArrayList;
import java.util.List;
import java.util.HashMap;

import java.math.BigDecimal;

import java.sql.Array;
import java.sql.SQLData;
import java.sql.SQLInput;
import java.sql.SQLOutput;
import java.sql.SQLException;

import oracle.sql.STRUCT;

import jnipap.Schema;
import jnipap.Pool;
import jnipap.Prefix;
import jnipap.Connection;
import jnipap.JnipapException;
import jnipap.Connection;

import ojnipap.OConnection;

/**
 * SQLObject version of the Schema class
 */
public class OSchema extends jnipap.Schema implements SQLData {

	public void readSQL(SQLInput stream, String typeName) throws SQLException {
		
		// Read data from stream
		id = Helpers.integerOrNull((BigDecimal)stream.readBigDecimal());
		name = stream.readString();
		description = stream.readString();
		vrf = stream.readString();

	}

	public void writeSQL(SQLOutput stream) throws SQLException {

		// Write data to stream
		stream.writeBigDecimal(Helpers.bigDecOrNull(id));
		stream.writeString(Helpers.strOrNull(name));
		stream.writeString(Helpers.strOrNull(description));
		stream.writeString(Helpers.strOrNull(vrf));

	}

	public String getSQLTypeName() {

		return "NIPAP_SCHEMA";

	}

	/**
	 * Create OSchema object from oracle.sql.STRUCT
	 *
	 * @param input STRUCT object contaning a NIPAP_SCHEMA Oracle object
	 * @return An OSchema instance
	 */
	static OSchema fromSTRUCT(STRUCT input) throws SQLException {

		if (input == null) {
			return null;
		}

		OSchema s = new OSchema();
		Object[] val = input.getAttributes();
		s.id = Helpers.integerOrNull((BigDecimal)val[0]);
		s.name = (String)val[1];
		s.description = (String)val[2];
		s.vrf = (String)val[3];

		return s;

	}

}
