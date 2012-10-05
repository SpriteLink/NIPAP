import java.net.URL;
import java.util.HashMap;
import java.util.Hashtable;
import java.util.ArrayList;
import java.util.List;

import org.apache.xmlrpc.XmlRpcException;

import jnipap.VRF;
import jnipap.Prefix;
import jnipap.Connection;
import jnipap.AddPrefixOptions;

public class Test {

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		// TODO Auto-generated method stub

		try {

			// Set up connection & auth
			URL u = new URL("http://127.0.0.1:1337/RPC2");
			Connection conn = new Connection(u, "dev", "dev");
			conn.authoritative_source = "test";

			// fetch a VRF
			VRF v = VRF.get(conn, new Integer(151));
			System.out.println("Found VRF " + v.rt);

			// Search prefixes in VRF
			HashMap spec = new HashMap();
			spec.put("vrf_id", new Integer(151));
			List plist = Prefix.list(conn, spec);
			for (int i = 0; i < plist.size(); i++) {
				System.out.println(plist.get(i).toString());
			}

			// Add prefix from prefix
			Prefix f_pref = Prefix.get(conn, new Integer(231));
			Prefix n_pref = new Prefix();
			AddPrefixOptions opts = new AddPrefixOptions();
			opts.put("prefix_length", new Integer(27));
			n_pref.type = "assignment";
			n_pref.description = "Java-jox";
			n_pref.country = "SE";
			n_pref.save(conn, f_pref, opts);


		} catch(Exception e) {
			System.out.println(e);
		}

	}
}
