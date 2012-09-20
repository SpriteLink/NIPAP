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

import jnipap.VRF;
import jnipap.Pool;
import jnipap.Prefix;
import jnipap.Connection;
import jnipap.JnipapException;
import jnipap.Connection;

import ojnipap.OConnection;

/**
 * SQLObject version of the VRF class
 */
public class OVRF extends jnipap.VRF implements SQLData {

	public void readSQL(SQLInput stream, String typeName) throws SQLException {
		
		// Read data from stream
		id = Helpers.integerOrNull((BigDecimal)stream.readBigDecimal());
		vrf = stream.readString();
		name = stream.readString();
		description = stream.readString();

	}

	public void writeSQL(SQLOutput stream) throws SQLException {

		// Write data to stream
		stream.writeBigDecimal(Helpers.bigDecOrNull(id));
		stream.writeString(Helpers.strOrNull(vrf));
		stream.writeString(Helpers.strOrNull(name));
		stream.writeString(Helpers.strOrNull(description));

	}

	public String getSQLTypeName() {

		return "NIPAP_VRF";

	}

	/**
	 * Create OVRF object from oracle.sql.STRUCT
	 *
	 * @param input STRUCT object contaning a NIPAP_VRF Oracle object
	 * @return An OVRF instance
	 */
	static OVRF fromSTRUCT(STRUCT input) throws SQLException {

		if (input == null) {
			return null;
		}

		OVRF s = new OVRF();
		Object[] val = input.getAttributes();
		s.id = Helpers.integerOrNull((BigDecimal)val[0]);
		s.vrf = (String)val[1];
		s.name = (String)val[2];
		s.description = (String)val[3];

		return s;

	}

}
