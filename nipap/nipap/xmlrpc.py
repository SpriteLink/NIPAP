#!/usr/bin/env python

import time
from functools import wraps
from flask import Flask
from flask import request, Response
from flaskext.xmlrpc import XMLRPCHandler, Fault

app = Flask(__name__)

handler = XMLRPCHandler('XMLRPC')
handler.connect(app, '/RPC2')
handler.connect(app, '/XMLRPC')

from nipapconfig import NipapConfig
from backend import Nipap, NipapError
import nipap
from authlib import AuthFactory, AuthError


nip = Nipap()

def check_auth(username, password, auth_source, auth_options = False):
    """This function is called to check if a username /
    password combination is valid.
    """
    af = AuthFactory()
    try:
        auth = af.get_auth(username, password, auth_source, auth_options or {})
    except AuthError, exp:
        return False

    if not auth.authenticate():
        return False

    return auth

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)

    def decorated(*args, **kwargs):
        """
        """

        # Fetch auth options from args
        auth_options = {}
        nipap_args = {}

        # validate function arguments
        if len(args) == 1:
            nipap_args = args[0]
        else:
            #logger.info("Malformed request: got %d parameters" % len(args))
            raise Fault(1000, ("NIPAP API functions take exactly 1 argument (%d given)") % len(args))

        if type(nipap_args) != dict:
            raise Fault(1000, ("Function argument must be XML-RPC struct/Python dict (Python %s given)." %
                type(nipap_args).__name__ ))

        # fetch auth options
        try:
            auth_options = nipap_args['auth']
            if type(auth_options) is not dict:
                raise ValueError()
        except (KeyError, ValueError):
            raise Fault(1000, ("Missing/invalid authentication options in request."))

        # fetch authoritative source
        try:
            auth_source = auth_options['authoritative_source']
        except KeyError:
            raise Fault(1000, ("Missing authoritative source in auth options."))

        if not request.authorization:
            return authenticate()

        # init AuthFacory()
        af = AuthFactory()
        auth = af.get_auth(request.authorization.username,
                request.authorization.password, auth_source, auth_options or {})

        # authenticated?
        if not auth.authenticate():
            return authenticate()

        # Replace auth options in API call arguments with auth object
        new_args = dict(args[0])
        new_args['auth'] = auth

        return f(*(new_args,), **kwargs)

    return decorated


@handler.register
@requires_auth
def echo(args):
    """ An echo function

        An API test function which simply echoes what is is passed in the
        'message' element in the args-dict..

        Valid keys in the `args`-struct:

        * `auth` [struct]
            Authentication options passed to the :class:`AuthFactory`.
        * `message` [string]
            String to echo.
        * `sleep` [integer]
            Number of seconds to sleep before echoing.

        Returns a string.
    """
    if args.get('sleep'):
        time.sleep(args.get('sleep'))
    if args.get('message') is not None:
        return args.get('message')

@handler.register
@requires_auth
def version():
    """ Returns nipapd version

        Returns a string.
    """
    return nipap.__version__


#
# VRF FUNCTIONS
#
@handler.register
@requires_auth
def add_vrf(args):
    """ Add a new VRF.

        Valid keys in the `args`-struct:

        * `auth` [struct]
            Authentication options passed to the :class:`AuthFactory`.
        * `attr` [struct]
            VRF attributes.

        Returns the internal database ID for the VRF.
    """

    try:
        return nip.add_vrf(args.get('auth'), args.get('attr'))
    except NipapError, e:
        raise Fault(e.error_code, str(e))


@handler.register
@requires_auth
def remove_vrf(args):
    """ Removes a VRF.

        Valid keys in the `args`-struct:

        * `auth` [struct]
            Authentication options passed to the :class:`AuthFactory`.
        * `vrf` [struct]
            A VRF spec.
    """

    try:
        nip.remove_vrf(args.get('auth'), args.get('vrf'))
    except NipapError, e:
        raise Fault(e.error_code, str(e))


@handler.register
@requires_auth
def list_vrf(args):
    """ List VRFs.

        Valid keys in the `args`-struct:

        * `auth` [struct]
            Authentication options passed to the :class:`AuthFactory`.
        * `vrf` [struct]
            Specifies VRF attributes to match (optional).

        Returns a list of structs matching the VRF spec.
    """

    try:
        return nip.list_vrf(args.get('auth'), args.get('vrf'))
    except NipapError, e:
        raise Fault(e.error_code, str(e))


@handler.register
@requires_auth
def edit_vrf(args):
    """ Edit a VRF.

        Valid keys in the `args`-struct:

        * `auth` [struct]
            Authentication options passed to the :class:`AuthFactory`.
        * `vrf` [struct]
            A VRF spec specifying which VRF(s) to edit.
        * `attr` [struct]
            VRF attributes.
    """

    try:
        return nip.edit_vrf(args.get('auth'), args.get('vrf'), args.get('attr'))
    except NipapError, e:
        raise Fault(e.error_code, str(e))


@handler.register
@requires_auth
def search_vrf(args):
    """ Search for VRFs.

        Valid keys in the `args`-struct:

        * `auth` [struct]
            Authentication options passed to the :class:`AuthFactory`.
        * `query` [struct]
            A struct specifying the search query.
        * `search_options` [struct]
            Options for the search query, such as limiting the number
            of results returned.

        Returns a struct containing search result and the search options
        used.
    """

    try:
        return nip.search_vrf(args.get('auth'), args.get('query'), args.get('search_options') or {})
    except NipapError, e:
        raise Fault(e.error_code, str(e))


@handler.register
@requires_auth
def smart_search_vrf(args):
    """ Perform a smart search.

        Valid keys in the `args`-struct:

        * `auth` [struct]
            Authentication options passed to the :class:`AuthFactory`.
        * `query_string` [string]
            The search string.
        * `search_options` [struct]
            Options for the search query, such as limiting the number
            of results returned.

        Returns a struct containing search result, interpretation of the
        search string and the search options used.
    """

    try:
        return nip.smart_search_vrf(args.get('auth'),
                args.get('query_string'), args.get('search_options', {}),
                args.get('extra_query'))
    except NipapError, e:
        raise Fault(e.error_code, str(e))


#
# POOL FUNCTIONS
#
@handler.register
@requires_auth
def add_pool(args):
    """ Add a pool.

        Valid keys in the `args`-struct:

        * `auth` [struct]
            Authentication options passed to the :class:`AuthFactory`.
        * `attr` [struct]
            Attributes which will be set on the new pool.

        Returns ID of created pool.
    """

    try:
        return nip.add_pool(args.get('auth'), args.get('attr'))
    except NipapError, e:
        raise Fault(e.error_code, str(e))


@handler.register
@requires_auth
def remove_pool(args):
    """ Remove a pool.

        Valid keys in the `args`-struct:

        * `auth` [struct]
            Authentication options passed to the :class:`AuthFactory`.
        * `pool` [struct]
            Specifies what pool(s) to remove.
    """

    try:
        nip.remove_pool(args.get('auth'), args.get('pool'))
    except NipapError, e:
        raise Fault(e.error_code, str(e))


@handler.register
@requires_auth
def list_pool(args):
    """ List pools.

        Valid keys in the `args`-struct:

        * `auth` [struct]
            Authentication options passed to the :class:`AuthFactory`.
        * `pool` [struct]
            Specifies pool attributes which will be matched.

        Returns a list of structs describing the matching pools.
    """

    try:
        return nip.list_pool(args.get('auth'), args.get('pool'))
    except NipapError, e:
        raise Fault(e.error_code, str(e))


@handler.register
@requires_auth
def edit_pool(args):
    """ Edit pool.

        Valid keys in the `args`-struct:

        * `auth` [struct]
            Authentication options passed to the :class:`AuthFactory`.
        * `pool` [struct]
            Specifies pool attributes to match.
        * `attr` [struct]
            Pool attributes to set.
    """

    try:
        return nip.edit_pool(args.get('auth'), args.get('pool'), args.get('attr'))
    except NipapError, e:
        raise Fault(e.error_code, str(e))


@handler.register
@requires_auth
def search_pool(args):
    """ Search for pools.

        Valid keys in the `args`-struct:

        * `auth` [struct]
            Authentication options passed to the :class:`AuthFactory`.
        * `query` [struct]
            A struct specifying the search query.
        * `search_options` [struct]
            Options for the search query, such as limiting the number
            of results returned.

        Returns a struct containing search result and the search options
        used.
    """

    try:
        return nip.search_pool(args.get('auth'), args.get('query'), args.get('search_options') or {})
    except NipapError, e:
        raise Fault(e.error_code, str(e))


@handler.register
@requires_auth
def smart_search_pool(args):
    """ Perform a smart search.

        Valid keys in the `args`-struct:

        * `auth` [struct]
            Authentication options passed to the :class:`AuthFactory`.
        * `query` [string]
            The search string.
        * `search_options` [struct]
            Options for the search query, such as limiting the number
            of results returned.

        Returns a struct containing search result, interpretation of the
        query string and the search options used.
    """

    try:
        return nip.smart_search_pool(args.get('auth'),
                args.get('query_string'), args.get('search_options') or {},
                args.get('extra_query', {}))
    except NipapError, e:
        raise Fault(e.error_code, str(e))


#
# PREFIX FUNCTIONS
#


@handler.register
@requires_auth
def add_prefix(args):
    """ Add a prefix.

        Valid keys in the `args`-struct:

        * `auth` [struct]
            Authentication options passed to the :class:`AuthFactory`.
        * `attr` [struct]
            Attributes to set on the new prefix.
        * `args` [srgs]
            Arguments for addition of prefix, such as what pool or prefix
            it should be allocated from.

        Returns ID of created prefix.
    """

    try:
        return nip.add_prefix(args.get('auth'), args.get('attr'), args.get('args'))
    except NipapError, e:
        raise Fault(e.error_code, str(e))



@handler.register
@requires_auth
def list_prefix(args):
    """ List prefixes.

        Valid keys in the `args`-struct:

        * `auth` [struct]
            Authentication options passed to the :class:`AuthFactory`.
        * `prefix` [struct]
            Prefix attributes to match.

        Returns a list of structs describing the matching prefixes.
    """

    try:
        return nip.list_prefix(args.get('auth'), args.get('prefix') or {})
    except NipapError, e:
        raise Fault(e.error_code, str(e))



@handler.register
@requires_auth
def edit_prefix(args):
    """ Edit prefix.

        Valid keys in the `args`-struct:

        * `auth` [struct]
            Authentication options passed to the :class:`AuthFactory`.
        * `prefix` [struct]
            Prefix attributes which describes what prefix(es) to edit.
        * `attr` [struct]
            Attribuets to set on the new prefix.
    """

    try:
        return nip.edit_prefix(args.get('auth'), args.get('prefix'), args.get('attr'))
    except NipapError, e:
        raise Fault(e.error_code, str(e))



@handler.register
@requires_auth
def remove_prefix(args):
    """ Remove a prefix.

        Valid keys in the `args`-struct:

        * `auth` [struct]
            Authentication options passed to the :class:`AuthFactory`.
        * `prefix` [struct]
            Attributes used to select what prefix to remove.
    """

    try:
        return nip.remove_prefix(args.get('auth'), args.get('prefix'), args.get('recursive'))
    except NipapError, e:
        raise Fault(e.error_code, str(e))



@handler.register
@requires_auth
def search_prefix(args):
    """ Search for prefixes.

        Valid keys in the `args`-struct:

        * `auth` [struct]
            Authentication options passed to the :class:`AuthFactory`.
        * `query` [struct]
            A struct specifying the search query.
        * `search_options` [struct]
            Options for the search query, such as limiting the number
            of results returned.

        Returns a struct containing the search result together with the
        search options used.
    """

    try:
        return nip.search_prefix(args.get('auth'), args.get('query'), args.get('search_options') or {})
    except NipapError, e:
        raise Fault(e.error_code, str(e))



@handler.register
@requires_auth
def smart_search_prefix(args):
    """ Perform a smart search.

        Valid keys in the `args`-struct:

        * `auth` [struct]
            Authentication options passed to the :class:`AuthFactory`.
        * `query_string` [string]
            The search string.
        * `search_options` [struct]
            Options for the search query, such as limiting the number
            of results returned.
        * `extra_query` [struct]
            Extra search terms, will be AND:ed together with what is
            extracted from the query string.

        Returns a struct containing search result, interpretation of the
        query string and the search options used.
    """

    try:
        return nip.smart_search_prefix(args.get('auth'),
                args.get('query_string'), args.get('search_options') or {},
                args.get('extra_query'))
    except NipapError, e:
        raise Fault(e.error_code, str(e))



@handler.register
@requires_auth
def find_free_prefix(args):
    """ Find a free prefix.

        Valid keys in the `args`-struct:

        * `auth` [struct]
            Authentication options passed to the :class:`AuthFactory`.
        * `args` [struct]
            Arguments for the find_free_prefix-function such as what prefix
            or pool to allocate from.
    """

    try:
        return nip.find_free_prefix(args.get('auth'), args.get('args'))
    except NipapError, e:
        raise Fault(e.error_code, str(e))



#
# ASN FUNCTIONS
#
@handler.register
@requires_auth
def add_asn(args):
    """ Add a new ASN.

        Valid keys in the `args`-struct:

        * `auth` [struct]
            Authentication options passed to the :class:`AuthFactory`.
        * `attr` [struct]
            ASN attributes.

        Returns the ASN.
    """

    try:
        return nip.add_asn(args.get('auth'), args.get('attr'))
    except NipapError, e:
        raise Fault(e.error_code, str(e))



@handler.register
@requires_auth
def remove_asn(args):
    """ Removes an ASN.

        Valid keys in the `args`-struct:

        * `auth` [struct]
            Authentication options passed to the :class:`AuthFactory`.
        * `asn` [integer]
            An ASN.
    """

    try:
        nip.remove_asn(args.get('auth'), args.get('asn'))
    except NipapError, e:
        raise Fault(e.error_code, str(e))



@handler.register
@requires_auth
def list_asn(args):
    """ List ASNs.

        Valid keys in the `args`-struct:

        * `auth` [struct]
            Authentication options passed to the :class:`AuthFactory`.
        * `asn` [struct]
            Specifies ASN attributes to match (optional).

        Returns a list of ASNs matching the ASN spec as a list of structs.
    """

    try:
        return nip.list_asn(args.get('auth'), args.get('asn') or {})
    except NipapError, e:
        raise Fault(e.error_code, str(e))



@handler.register
@requires_auth
def edit_asn(args):
    """ Edit an ASN.

        Valid keys in the `args`-struct:

        * `auth` [struct]
            Authentication options passed to the :class:`AuthFactory`.
        * `asn` [integer]
            An integer specifying which ASN to edit.
        * `attr` [struct]
            ASN attributes.
    """

    try:
        return nip.edit_asn(args.get('auth'), args.get('asn'), args.get('attr'))
    except NipapError, e:
        raise Fault(e.error_code, str(e))



@handler.register
@requires_auth
def search_asn(args):
    """ Search ASNs.

        Valid keys in the `args`-struct:

        * `auth` [struct]
            Authentication options passed to the :class:`AuthFactory`.
        * `query` [struct]
            A struct specifying the search query.
        * `search_options` [struct]
            Options for the search query, such as limiting the number
            of results returned.

        Returns a struct containing search result and the search options
        used.
    """

    try:
        return nip.search_asn(args.get('auth'), args.get('query'), args.get('search_options') or {})
    except NipapError, e:
        raise Fault(e.error_code, str(e))



@handler.register
@requires_auth
def smart_search_asn(args):
    """ Perform a smart search among ASNs.

        Valid keys in the `args`-struct:

        * `auth` [struct]
            Authentication options passed to the :class:`AuthFactory`.
        * `query_string` [string]
            The search string.
        * `search_options` [struct]
            Options for the search query, such as limiting the number
            of results returned.

        Returns a struct containing search result, interpretation of the
        search string and the search options used.
    """

    try:
        return nip.smart_search_asn(args.get('auth'), args.get('query_string'), args.get('search_options') or {})
    except NipapError, e:
        raise Fault(e.error_code, str(e))


if __name__ == '__main__':
    app.run()
