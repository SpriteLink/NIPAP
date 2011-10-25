package jnipap;

import org.apache.ws.commons.util.NamespaceContextImpl;
import org.apache.xmlrpc.common.TypeFactoryImpl;
import org.apache.xmlrpc.common.XmlRpcController;
import org.apache.xmlrpc.common.XmlRpcStreamConfig;
import org.apache.xmlrpc.parser.NullParser;
import org.apache.xmlrpc.parser.TypeParser;
import org.apache.xmlrpc.serializer.NullSerializer;

/**
 * Class which handles parsing of <nil> values
 *
 * As the Apache XML-RPC client implementation only accepts nil values in the
 * ex namespace (<ex:nil>), this parser is implemented to make it handle nil
 * without the namespace.
 *
 * This is how the Twisted XML-RPC-daemon handles nil.
 */
public class NonExNullParser extends TypeFactoryImpl {

	/**
	 * Create instance.
	 *
	 * @param pController
	 */
	public NonExNullParser(XmlRpcController pController) {
		super(pController);
	}

	public TypeParser getParser(XmlRpcStreamConfig pConfig,
								NamespaceContextImpl pContext, String pURI,
								String pLocalName) {

		if ("".equals(pURI) && NullSerializer.NIL_TAG.equals(pLocalName)) {
			return new NullParser();
		} else {
			return super.getParser(pConfig, pContext, pURI, pLocalName);
		}
	}
}
