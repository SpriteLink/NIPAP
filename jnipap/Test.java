import java.net.URL;
import java.util.HashMap;
import java.util.Hashtable;
import java.util.ArrayList;
import java.util.List;

import org.apache.xmlrpc.XmlRpcException;

import jnipap.Schema;
import jnipap.Connection;

public class Test {

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		// TODO Auto-generated method stub

		try {

			// Set up connection & auth
			URL u = new URL("http://127.0.0.1:1337/RPC2");
			Connection conn = new Connection(u, "dev@local", "dev");
			conn.authoritative_source = "test";

			// fetch a schema
			Schema s = Schema.get(conn, new Integer(1));
			System.out.println("Found schema " + s.name);

		} catch(Exception e) {
			System.out.println(e);
		}

	}
}
