package jnipap;

import java.net.URL;
import java.util.List;
import java.util.HashMap;
import java.util.Map;

import org.apache.xmlrpc.XmlRpcException;
import org.apache.xmlrpc.client.XmlRpcHttpTransportException;
import org.apache.xmlrpc.client.XmlRpcClient;
import org.apache.xmlrpc.client.XmlRpcClientConfigImpl;

import jnipap.JnipapException;
import jnipap.InputException;
import jnipap.MissingInputException;
import jnipap.NonExistentException;
import jnipap.DuplicateException;
import jnipap.ConnectionException;
import jnipap.InvalidParameterException;

/**
 * A class containing a connection to the NIPAP XML-RPC server
 *
 * This class is used by all NIPAP mapped objects to obtain a connection to
 * the NIPAP XML-RPC server.
 *
 * @author Lukas Garberg <lukas@spritelink.net>
 */
public class Connection {

	private XmlRpcClient connection;
	private XmlRpcClientConfigImpl config;
	protected static URL srv_url;

	public String full_name;
	public String authoritative_source;
	public String auth_username;
	public String password;
	public String username;

	/**
	 * Creates a Connection.
	 *
	 * @param srv_url URL to the NIPAP server
	 */
	public Connection(URL srv_url, String auth_username, String password) {

		Connection.srv_url = srv_url;
		this.username = auth_username;
		this.auth_username = auth_username;
		this.password = password;

		setup();

	}

	/**
	 * Creates a connection.
	 *
	 * Used by subclasses where the class is instanciated before the options
	 * are known.
	 */
	protected Connection() {}


	/**
	 * Set up the connection objects.
	 */
	protected void setup() {

		// Create configuration object
		config = new XmlRpcClientConfigImpl();
		config.setServerURL(srv_url);
		config.setEnabledForExtensions(true);
		config.setBasicUserName(auth_username);
		config.setBasicPassword(password);

		// Create client object
		connection = new XmlRpcClient();
		connection.setConfig(config);
		connection.setTypeFactory(new NonExNullParser(connection));

	}


	/**
	 * Impersonate other user.
	 *
	 * This function is used to set a different username than the one used for
	 * authentication as responsible for the changes. For this to work, the
	 * user used for authentication must be "trusted", which means that it has
	 * permission to impersonate other users.
	 *
	 * @param username Username which will be responsible for all actions.
	 */
	public void setUsername(String username) {
		this.username = username;
	}

	/**
	 * Return a Map-representation of the auth options
	 *
	 * @return Map of authentication options
	 */
	public Map authMap() {

		HashMap map = new HashMap();

		// Add non-null elements
		if (full_name != null) {
			map.put("full_name", full_name);
		}

		if (authoritative_source != null) {
			map.put("authoritative_source", authoritative_source);
		}

		if (username != null) {
			map.put("username", username);
		}

		return (Map)map;

	}

	public Object execute(String pMethodName, Object[] pParams) throws JnipapException {
		try {
			return connection.execute(pMethodName, pParams);
		} catch(XmlRpcException e) {
			throw (JnipapException)xmlRpcExceptionToJnipapException(e);
		}
	}

	public Object execute(String pMethodName, List pParams) throws JnipapException {
		try {
			return connection.execute(pMethodName, pParams);
		} catch(XmlRpcException e) {
			throw (JnipapException)xmlRpcExceptionToJnipapException(e);
		}
	}

	/**
	 * Converts an XmlRpcException to a JnipapException
	 *
	 * @param e XmlRpcException to convert
	 * @return A JnipapException or subclass of it describing the error
	 */
	private Exception xmlRpcExceptionToJnipapException(XmlRpcException e) {

		if (e instanceof XmlRpcHttpTransportException ) {

			XmlRpcHttpTransportException e2 = (XmlRpcHttpTransportException)e;

			// Failed authentications turn up here
			if (e2.getStatusCode() == 401) {
				return new AuthFailedException("Authentication failed.");
			} else {
				return new ConnectionException(e2);
			}

		} else {

			// one of our own NIPAP-errors?
			switch (e.code) {
				case 1000:
					return new JnipapException(e.getMessage());
				case 1100:
					return new InputException(e.getMessage());
				case 1110:
					return new MissingInputException(e.getMessage());
				case 1120:
					return new InvalidParameterException(e.getMessage());
				case 1130:
					return new InvalidParameterException(e.getMessage());
				case 1200:
					return new InvalidParameterException(e.getMessage());
				case 1300:
					return new NonExistentException(e.getMessage());
				case 1400:
					return new DuplicateException(e.getMessage());
				default:
					return new JnipapException(e);
			}

		}

	}

}
