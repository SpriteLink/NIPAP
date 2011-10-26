import java.net.URL;
import java.util.HashMap;
import java.util.Hashtable;

import org.apache.xmlrpc.XmlRpcException;
import org.apache.xmlrpc.client.XmlRpcClient;
import org.apache.xmlrpc.client.XmlRpcClientConfigImpl;

import jnipap.Schema;
import jnipap.AuthOptions;
import jnipap.Connection;

public class Test {

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		// TODO Auto-generated method stub

		AuthOptions auth = new AuthOptions();

		try {
			URL u = new URL("http://127.0.0.1:1337/RPC2");
			Connection conn = Connection.getInstance(u, "dev@local",
                                "dev");
		} catch(Exception e) {
			System.out.println(e);
		}

		try {

			Schema s;
			s = Schema.get(auth, 162);
			System.out.println(s.toString());

			s.description = "Chop chop";
			s.save(auth);

		} catch(Exception e) {
			System.out.println(e);
		}


		/*
		try {

			Object[] params_arr = new Object[1];

			Hashtable<String, String> auth_options = new Hashtable<String, String>();
			auth_options.put("authoritative_source", "dev");
			//auth_options.put("tjong", null);

			Hashtable<String, String> schema_spec = new Hashtable<String, String>();
			schema_spec.put("name", "global");

			Hashtable<String, Hashtable> params = new Hashtable<String, Hashtable>();
			params.put("auth", auth_options);
			params.put("schema", schema_spec);
			
			params_arr[0] = params;

			
			/*
			 * It says in nipap/nipap.py that search_prefix should return a list of dicts
			 * A list is most close to the java ArrayList, and a dict is a sort of Map
			 * Unfortunately, that didin't work, but the following does...
			 */
			//HashMap<String, Object> result = (HashMap<String, Object>)client.execute("list_schema", params_arr);
/*			Object result = conn.connection.execute("list_schema", params_arr);

			Object[] o = (Object[])result;
			System.out.println(o.length);
			HashMap schema = (HashMap)o[0];
			System.out.println(schema);
			
		} catch (XmlRpcException exception) {
			System.err.println("Call: XML-RPC Fault #" +
					Integer.toString(exception.code) + ": " +
					exception.toString());
			exception.printStackTrace();
		} catch (Exception exception) {
			System.err.println("Call: " + exception.toString());
		}*/
	}
}
