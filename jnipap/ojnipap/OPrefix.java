package ojnipap;

import java.sql.SQLData;
import java.sql.SQLInput;
import java.sql.SQLOutput;
import java.sql.SQLException;

import oracle.sql.STRUCT;

import jnipap.Connection;
import jnipap.Schema;
import jnipap.Pool;
import jnipap.Prefix;

/**
 * SQLObject version of the Prefix class
 */
public class OPrefix extends jnipap.Prefix implements SQLData {

	public void readSQL(SQLInput stream, String typeName) throws SQLException {

		// Read data from stream
		id = Helpers.integerOrNull(stream.readBigDecimal());
		family = Helpers.integerOrNull(stream.readBigDecimal());
		schema = (jnipap.Schema)OSchema.fromSTRUCT((STRUCT)stream.readObject());
		prefix = stream.readString();
		display_prefix = stream.readString();
		description = stream.readString();
		comment = stream.readString();
		node = stream.readString();
		pool = (jnipap.Pool)OPool.fromSTRUCT((STRUCT)stream.readObject());
		type = stream.readString();
		indent = Helpers.integerOrNull(stream.readBigDecimal());
		country = stream.readString();
		order_id = stream.readString();
		external_key = stream.readString();
		authoritative_source = stream.readString();
		alarm_priority = stream.readString();
		monitor = new Boolean(stream.readBoolean());

		// Skip display, match and children as these are "read-only"

	}

	public void writeSQL(SQLOutput stream) throws SQLException {

		// Write data to stream
		stream.writeBigDecimal(Helpers.bigDecOrNull(id));
		stream.writeBigDecimal(Helpers.bigDecOrNull(family));
		stream.writeObject((OSchema)schema);
		stream.writeString(Helpers.strOrNull(prefix));
		stream.writeString(Helpers.strOrNull(display_prefix));
		stream.writeString(Helpers.strOrNull(description));
		stream.writeString(Helpers.strOrNull(comment));
		stream.writeString(Helpers.strOrNull(node));
		stream.writeObject((OPool)pool);
		stream.writeString(Helpers.strOrNull(type));
		stream.writeBigDecimal(Helpers.bigDecOrNull(indent));
		stream.writeString(Helpers.strOrNull(country));
		stream.writeString(Helpers.strOrNull(order_id));
		stream.writeString(Helpers.strOrNull(external_key));
		stream.writeString(Helpers.strOrNull(authoritative_source));
		stream.writeString(Helpers.strOrNull(alarm_priority));
		stream.writeBigDecimal(Helpers.bigDecBoolOrNull(monitor));
		stream.writeBigDecimal(Helpers.bigDecBoolOrNull(display));
		stream.writeBigDecimal(Helpers.bigDecBoolOrNull(match));
		stream.writeBigDecimal(Helpers.bigDecOrNull(children));

	}

	public String getSQLTypeName() {

		return "NIPAP_PREFIX";

	}

}
