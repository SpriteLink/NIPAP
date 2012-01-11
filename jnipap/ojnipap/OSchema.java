package ojnipap;

import java.sql.Array;
import java.sql.SQLData;
import java.sql.SQLInput;
import java.sql.SQLOutput;
import java.sql.SQLException;

import jnipap.Schema;
import jnipap.Pool;
import jnipap.Prefix;
import jnipap.Connection;
import jnipap.JnipapException;
import jnipap.Connection;

import ojnipap.OConnection;

import java.util.ArrayList;
import java.util.List;
import java.util.HashMap;

/**
 * SQLObject version of the Schema class
 */
public class OSchema extends jnipap.Schema implements SQLData {

	public void readSQL(SQLInput stream, String typeName) throws SQLException {
		
		// Read data from stream
		id = new Integer(stream.readBigDecimal().intValue());
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

}
