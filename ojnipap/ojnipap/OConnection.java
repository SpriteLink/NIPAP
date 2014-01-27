package ojnipap;

import java.net.URL;

import java.sql.SQLData;
import java.sql.SQLInput;
import java.sql.SQLOutput;
import java.sql.SQLException;
import java.net.MalformedURLException;

import jnipap.Connection;

/**
 * SQLObject version of the Connection class
 */
public class OConnection extends jnipap.Connection implements SQLData {

	private static final long serialVersionUID = 0;

	/**
	 * Create instance from SQL.
	 */
	public void readSQL(SQLInput stream, String typeName) throws SQLException {

		try {
			srv_url = new URL(stream.readString());
		} catch(MalformedURLException e) {
			throw new SQLException(e);
		}

		full_name = stream.readString();
		authoritative_source = stream.readString();
		auth_username = stream.readString();
		username = stream.readString();
		password = stream.readString();

		setup();

	}

	/**
	 * Write data back to SQL.
	 */
	public void writeSQL(SQLOutput stream) throws SQLException {

		stream.writeString(srv_url.toString());
		stream.writeString(full_name);
		stream.writeString(authoritative_source);
		stream.writeString(auth_username);
		stream.writeString(password);

	}

	/**
	 * Get name of the corresponding SQL type.
	 *
	 * @return Name of type.
	 */
	public String getSQLTypeName() {
		return "NIPAP_CONNECTION";
	}

}
