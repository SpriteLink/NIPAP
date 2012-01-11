package ojnipap;

import java.sql.SQLData;
import java.sql.SQLInput;
import java.sql.SQLOutput;
import java.sql.SQLException;

import jnipap.Connection;
import jnipap.Schema;
import jnipap.Pool;
import jnipap.Prefix;

/**
 * SQLObject version of the Prefix class
 */
public class OPrefix extends jnipap.Prefix implements SQLData {

	public OSchema schema;
	public OPool pool;

	public void readSQL(SQLInput stream, String typeName) throws SQLException {

		// Read data from stream
		id = new Integer(stream.readBigDecimal().intValue());
		family = new Integer(stream.readBigDecimal().intValue());
		schema = (OSchema)stream.readObject();
		prefix = stream.readString();
		display_prefix = stream.readString();
		description = stream.readString();
		comment = stream.readString();
		node = stream.readString();
		pool = (OPool)stream.readObject();
		type = stream.readString();
		indent = new Integer(stream.readBigDecimal().intValue());
		country = stream.readString();
		order_id = stream.readString();
		external_key = stream.readString();
		authoritative_source = stream.readString();
		alarm_priority = stream.readString();
		monitor = new Boolean(stream.readBoolean());
		display = new Boolean(stream.readBoolean());
		match = new Boolean(stream.readBoolean());
		children = new Integer(stream.readBigDecimal().intValue());

	}

	public void writeSQL(SQLOutput stream) throws SQLException {

		// Write data to stream
		stream.writeBigDecimal(Helpers.bigDecOrNull(id));
		stream.writeBigDecimal(Helpers.bigDecOrNull(family));
		stream.writeObject(schema);
		stream.writeString(Helpers.strOrNull(prefix));
		stream.writeString(Helpers.strOrNull(display_prefix));
		stream.writeString(Helpers.strOrNull(description));
		stream.writeString(Helpers.strOrNull(comment));
		stream.writeString(Helpers.strOrNull(node));
		stream.writeObject(pool);
		stream.writeString(Helpers.strOrNull(type));
		stream.writeBigDecimal(Helpers.bigDecOrNull(indent));
		stream.writeString(Helpers.strOrNull(country));
		stream.writeString(Helpers.strOrNull(order_id));
		stream.writeString(Helpers.strOrNull(external_key));
		stream.writeString(Helpers.strOrNull(authoritative_source));
		stream.writeString(Helpers.strOrNull(alarm_priority));
		stream.writeBigDecimal(Helpers.bigDecBoolOrNull(monitor));
		stream.writeBigDecimal(Helpers.bigDecBoolOrNull(display));
		stream.writeBigDecimal(Helpers.bigDecOrNull(children));

	}

	public String getSQLTypeName() {

		return "NIPAP_PREFIX";

	}

}
