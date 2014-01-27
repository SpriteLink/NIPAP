package ojnipap;

import java.util.HashMap;

import java.sql.SQLData;
import java.sql.SQLInput;
import java.sql.SQLOutput;
import java.sql.SQLException;

public class OSearchOptions extends HashMap implements SQLData {

	// version ID for serialization
	private static final long serialVersionUID = 0L;

	public void readSQL(SQLInput stream, String typeName) throws SQLException {

        put("max_result", new Integer(stream.readBigDecimal().intValue()));
        put("offset", new Integer(stream.readBigDecimal().intValue()));

    }

	public void writeSQL(SQLOutput stream) throws SQLException {

        stream.writeBigDecimal(Helpers.bigDecOrNull((Integer)get("max_result")));
        stream.writeBigDecimal(Helpers.bigDecOrNull((Integer)get("offset")));

    }

	public String getSQLTypeName() {

		return "NIPAP_SEARCH_OPTIONS";

	}

}
