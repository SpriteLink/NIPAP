import java.net.URL;
import java.util.List;
import java.util.Map;
import java.util.HashMap;
import java.util.ArrayList;

import jnipap.Connection;
import jnipap.VRF;
import jnipap.Pool;
import jnipap.Prefix;
import jnipap.Connection;
import jnipap.AddPrefixOptions;
import jnipap.JnipapException;

import org.junit.Before;
import org.junit.After;
import org.junit.Test;
import org.junit.Ignore;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.fail;


/**
 * Unit tests for jnipap
 *
 * @author Lukas Garberg <lukas@spritelink.net>
 */
@RunWith(JUnit4.class)
public class JnipapTester {

	public Connection connection;

	/**
	 * Create connection to NIPAP server
	 */
	@Before
	public void createConnection() {

		URL url;
		try {
			url = new URL("http://127.0.0.1:1337/RPC2");
			this.connection = new Connection(url, "unittest", "gottatest");
			this.connection.authoritative_source = "test";
		} catch (Exception e) {
			fail("Operation resulted in " + e.getClass().getName() + " with message \"" + e.getMessage() + "\"");
		}

	}

	/**
	 * Test adding and getting a VRF
	 */
	@Test
	public void addGetVrf() {

		VRF vrf1, vrf2;

		vrf1 = new VRF();
		vrf1.rt = "123:456";
		vrf1.name = "Test VRF #1";
		vrf1.description = "A test VRF.";

		try {
			vrf1.save(this.connection);
			vrf2 = VRF.get(this.connection, vrf1.id);
		} catch (JnipapException e) {
			fail("Operation resulted in exception " + e.getMessage());
			return;
		}

		assertEquals("Added VRF differs from fetched VRF",
			vrf1, vrf2);

	}

	/**
	 * Test adding a VRF and (smart) searching for it
	 */
	@Test
	public void addSmartSearchVrf() {

		VRF vrf1;

		vrf1 = new VRF();
		vrf1.rt = "1234:5678";
		vrf1.name = "Test VRF #2";
		vrf1.description = "Another test VRF.";

		try {
			vrf1.save(this.connection);
		} catch (JnipapException e) {
			fail("Operation resulted in exception " + e.getMessage());
			return;
		}

		// Search!
		try {
			Map result = VRF.search(this.connection, "1234:5678", new HashMap<>());

			int len = ((List)result.get("result")).size();
			if (len < 1) {
				fail("Smart search operation returned to few elements (" + len + ")");
			}

		} catch (JnipapException e) {
			fail("Smart seach operation resulted in " + e.getClass().getName() + " with message \"" + e.getMessage() + "\"");
			return;
		}

	}

	/**
	 * Test adding and getting a pool
	 */
	@Test
	public void addGetPool() {

		Pool pool1, pool2;

		pool1 = new Pool();
		pool1.name = "Test pool #1";
		pool1.description = "A first test pool.";
		pool1.default_type = "assignment";
		pool1.ipv4_default_prefix_length = 28;
		pool1.ipv6_default_prefix_length = 64;

		try {
			pool1.save(this.connection);
			pool2 = Pool.get(this.connection, pool1.id);
		} catch (JnipapException e) {
			fail("Operation resulted in " + e.getClass().getName() + " with message \"" + e.getMessage() + "\"");
			return;
		}

		assertEquals("Added pool differs from fetched pool",
			pool1, pool2);

	}

	/**
	 * Test adding a pool and (smart) searching for it
	 */
	@Test
	public void addSmartSearchPool() {

		Pool pool1;

		pool1 = new Pool();
		pool1.name = "Test pool #2";
		pool1.description = "A second test pool.";
		pool1.default_type = "assignment";
		pool1.ipv4_default_prefix_length = 28;
		pool1.ipv6_default_prefix_length = 64;

		try {
			pool1.save(this.connection);
		} catch (JnipapException e) {
			fail("Save operation resulted in " + e.getClass().getName() + " with message \"" + e.getMessage() + "\"");
			return;
		}

		// Search!
		try {
			Map result = Pool.search(this.connection, "pool", new HashMap<>());

			int len = ((List)result.get("result")).size();
			if (len < 1) {
				fail("Smart search operation returned to few elements (" + len + ")");
			}

		} catch (JnipapException e) {
			fail("Smart seach operation resulted in " + e.getClass().getName() + " with message \"" + e.getMessage() + "\"");
		}

	}

	/**
	 * Test adding and getting a prefix
	 */
	@Test
	public void addGetPrefix() {

		Prefix prefix1, prefix2;

		prefix1 = new Prefix();
		prefix1.prefix = "192.168.0.0/16";
		prefix1.type = "reservation";
		prefix1.description = "RFC1918 class B block";

		try {
			prefix1.save(this.connection);
			prefix2 = Prefix.get(this.connection, prefix1.id);
		} catch (JnipapException e) {
			fail("Operation resulted in " + e.getClass().getName() + " with message \"" + e.getMessage() + "\"");
			return;
		}

		assertEquals("Added prefix differs from fetched prefix",
			prefix1, prefix2);

	}


	/**
	 * Test adding prefixes and (smart) searching for them
	 */
	@Test
	public void addSmartSearchPrefix() {

		// Add three prefixes so we have some data to search for
		Prefix prefix1, prefix2, prefix3;
		prefix1 = new Prefix();
		prefix1.prefix = "10.0.0.0/8";
		prefix1.type = "reservation";
		prefix1.description = "RFC1918 class A block";

		prefix2 = new Prefix();
		prefix2.prefix = "10.0.0.0/24";
		prefix2.type = "assignment";
		prefix2.description = "subnet";

		prefix3 = new Prefix();
		prefix3.prefix = "10.0.0.1/32";
		prefix3.type = "host";
		prefix3.description = "TEST TEST";

		try {
			prefix1.save(this.connection);
			prefix2.save(this.connection);
			prefix3.save(this.connection);
		} catch (JnipapException e) {
			fail("Save operation resulted in " + e.getClass().getName() + " with message \"" + e.getMessage() + "\"");
		}

		// Search!
		try {
			Map result = Prefix.search(this.connection, "TEST TEST", new HashMap<>());

			int len = ((List)result.get("result")).size();
			if (len < 1) {
				fail("Smart search operation returned to few elements (" + len + ")");
			}

		} catch (JnipapException e) {
			fail("Smart seach operation resulted in " + e.getClass().getName() + " with message \"" + e.getMessage() + "\"");
		}


	}

}
