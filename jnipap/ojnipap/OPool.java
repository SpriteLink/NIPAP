package ojnipap;

import java.math.BigDecimal;

import java.sql.SQLData;
import java.sql.SQLInput;
import java.sql.SQLOutput;
import java.sql.SQLException;

import jnipap.Schema;
import jnipap.Pool;

/**
 * SQLObject version of the Pool class
 */
public class OPool extends jnipap.Pool implements SQLData {

	public OSchema schema;

	public void readSQL(SQLInput stream, String typeName) throws SQLException {

		// Read data from stream
		id = new Integer(stream.readBigDecimal().intValue());
		name = stream.readString();
		schema = (OSchema)stream.readObject();
		description = stream.readString();
		default_type = stream.readString();
		ipv4_default_prefix_length = new Integer(stream.readBigDecimal().intValue());
		ipv6_default_prefix_length = new Integer(stream.readBigDecimal().intValue());

	}

	public void writeSQL(SQLOutput stream) throws SQLException {

		// Write data to stream
		stream.writeBigDecimal(new BigDecimal(id.intValue()));
		stream.writeString(name);
		stream.writeObject(schema);
		stream.writeString(description);
		stream.writeString(default_type);
		stream.writeBigDecimal(new BigDecimal(ipv4_default_prefix_length.intValue()));
		stream.writeBigDecimal(new BigDecimal(ipv6_default_prefix_length.intValue()));

	}

	public String getSQLTypeName() {

		return "NIPAP_POOL";

	}


}
