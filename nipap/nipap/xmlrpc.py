""" NIPAP XML-RPC
    =============
    This module contains the actual functions presented over the XML-RPC API. All
    functions are quite thin and mostly wrap around the functionality provided by
    the backend module.
"""

import datetime
import logging
import time
import pytz
from functools import wraps
from flask import Flask, current_app
from flask import request, Response
from flask_xmlrpcre.xmlrpcre import XMLRPCHandler, Fault
from flask_compress import Compress

from .nipapconfig import NipapConfig
from .backend import Nipap, NipapError
import nipap
from .authlib import AuthFactory, AuthError


def setup():
    app = Flask('nipap.xmlrpc')
    Compress(app)

    handler = XMLRPCHandler('XMLRPC')
    handler.connect(app, '/RPC2')
    handler.connect(app, '/XMLRPC')
    handler.register_instance(NipapXMLRPC())

    return app


def _mangle_prefix(res):
    """ Mangle prefix result
    """
    # fugly cast from large numbers to string to deal with XML-RPC
    res['total_addresses'] = str(res['total_addresses'])
    res['used_addresses'] = str(res['used_addresses'])
    res['free_addresses'] = str(res['free_addresses'])

    # postgres has notion of infinite while datetime hasn't, if expires
    # is equal to the max datetime we assume it is infinity and instead
    # represent that as None
    if res['expires'].tzinfo is None:
        res['expires'] = pytz.utc.localize(res['expires'])
    if res['expires'] == pytz.utc.localize(datetime.datetime.max):
        res['expires'] = None

    return res


def authenticate():
    """ Sends a 401 response that enables basic auth
    """
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    """ Class decorator for XML-RPC functions that requires auth
    """
    @wraps(f)
    def decorated(self, *args, **kwargs):
        """
        """

        self.logger.debug("authenticating call with args %s and kwargs %s", args, kwargs)
        # Fetch auth options from args
        auth_options = {}
        nipap_args = {}

        # validate function arguments
        if len(args) == 1:
            nipap_args = args[0]
        else:
            self.logger.debug("Malformed request: got %s parameters", len(args))
            raise Fault(1000, "NIPAP API functions take exactly 1 argument ({} given)".format(len(args)))

        if not isinstance(nipap_args, dict):
            self.logger.debug("Function argument is not struct")
            raise Fault(1000, ("Function argument must be XML-RPC struct/Python dict (Python {} given).".format(
                type(nipap_args).__name__ )))

        # fetch auth options
        try:
            auth_options = nipap_args['auth']
            if not isinstance(auth_options, dict):
                raise ValueError()
        except (KeyError, ValueError):
            self.logger.debug("Missing/invalid authentication options in request.")
            raise Fault(1000, ("Missing/invalid authentication options in request."))

        # fetch authoritative source
        try:
            auth_source = auth_options['authoritative_source']
        except KeyError:
            self.logger.debug("Missing authoritative source in auth options.")
            raise Fault(1000, ("Missing authoritative source in auth options."))

        if not request.authorization:
            return authenticate()

        self.logger.debug('About to initialize auth factory..')
        try:
            # init AuthFacory()
            af = AuthFactory()
            auth = af.get_auth(request.authorization.username,
                    request.authorization.password, auth_source, auth_options or {})

            # authenticated?
            if not auth.authenticate():
                self.logger.debug("Incorrect username or password.")
                raise Fault(1510, ("Incorrect username or password."))

            # Replace auth options in API call arguments with auth object
            new_args = dict(args[0])
            new_args['auth'] = auth

            self.logger.debug('Call authenticated - calling.. with new_args: %s', new_args)
            return f(self, *(new_args,), **kwargs)
        except Exception as e:
            self.logger.exception(e)
            raise e

    return decorated


def xmlrpc_bignum2str(res, keys=['num_prefixes', 'total_addresses', 'used_addresses', 'free_addresses']):
    """
    Cast from large numbers to string to deal with XML-RPC -
    Performance seems equivalent to preexisting blocks, and improves readability IMO
    Since targeted keys (quantity) all start with ['num_', 'total_', 'used_', 'free_'] a different version was tried
    using .startswith(), however this proved less performing..

    :param dict[str, dict] res: psql result to cast
    :param list[str] keys: list of keys to cast to string if required
    :rtype: dict[str, dict]
    """
    if isinstance(res, dict):
        if 'result' in res:
            for entry in res['result']:
                for v in ['_v4', '_v6']:
                    for key in [k+v for k in keys]:
                        if entry[key] is not None and not isinstance(entry[key], str):
                            entry[key] = str(entry[key])
        elif 'id' in res:
            for v in ['_v4', '_v6']:
                for key in [k + v for k in keys]:
                    if res[key] is not None and not isinstance(res[key], str):
                        res[key] = str(res[key])
        else:
            raise ValueError('Illegal result: {}'.format(res))

    elif isinstance(res, list):
        for entry in res:
            for v in ['_v4', '_v6']:
                for key in [k+v for k in keys]:
                    if entry[key] is not None and not isinstance(entry[key], str):
                        entry[key] = str(entry[key])
    else:
        raise ValueError('Illegal result: {}'.format(res))
    return res


class NipapXMLRPC:
    """ NIPAP XML-RPC API
    """
    def __init__(self):
        self.nip = Nipap()
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)

    @requires_auth
    def echo(self, args):
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

    @requires_auth
    def version(self, args):
        """ Returns nipapd version

            Returns a string.
        """
        return nipap.__version__

    @requires_auth
    def db_version(self, args):
        """ Returns schema version of nipap psql db

            Returns a string.
        """
        return self.nip._get_db_version()

    #
    # VRF FUNCTIONS
    #
    @requires_auth
    def add_vrf(self, args):
        """ Add a new VRF.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `attr` [struct]
                VRF attributes.

            Returns the internal database ID for the VRF.
        """
        try:
            res = self.nip.add_vrf(args.get('auth'), args.get('attr'))
            # fugly cast from large numbers to string to deal with XML-RPC
            res = xmlrpc_bignum2str(res, ['num_prefixes', 'total_addresses', 'used_addresses', 'free_addresses'])
            return res
        except (AuthError, NipapError) as exc:
            self.logger.debug(str(exc))
            raise Fault(exc.error_code, str(exc))

    @requires_auth
    def remove_vrf(self, args):
        """ Removes a VRF.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `vrf` [struct]
                A VRF spec.
        """
        try:
            self.nip.remove_vrf(args.get('auth'), args.get('vrf'))
        except (AuthError, NipapError) as exc:
            self.logger.debug(str(exc))
            raise Fault(exc.error_code, str(exc))

    @requires_auth
    def list_vrf(self, args):
        """List VRFs.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `vrf` [struct]
                Specifies VRF attributes to match (optional).

            Returns a list of structs matching the VRF spec.
        """
        try:
            res = self.nip.list_vrf(args.get('auth'), args.get('vrf'))

            # fugly cast from large numbers to string to deal with XML-RPC
            res = xmlrpc_bignum2str(res, ['num_prefixes', 'total_addresses', 'used_addresses', 'free_addresses'])

            return res
        except (AuthError, NipapError) as exc:
            self.logger.debug(str(exc))
            raise Fault(exc.error_code, str(exc))

    @requires_auth
    def edit_vrf(self, args):
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
            res = self.nip.edit_vrf(args.get('auth'), args.get('vrf'), args.get('attr'))

            # fugly cast from large numbers to string to deal with XML-RPC
            res = xmlrpc_bignum2str(res, ['num_prefixes', 'total_addresses', 'used_addresses', 'free_addresses'])

            return res
        except (AuthError, NipapError) as exc:
            self.logger.debug(str(exc))
            raise Fault(exc.error_code, str(exc))

    @requires_auth
    def search_vrf(self, args):
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
            res = self.nip.search_vrf(args.get('auth'), args.get('query'), args.get('search_options') or {})

            # fugly cast from large numbers to string to deal with XML-RPC
            res = xmlrpc_bignum2str(res, ['num_prefixes', 'total_addresses', 'used_addresses', 'free_addresses'])

            return res
        except (AuthError, NipapError) as exc:
            self.logger.debug(str(exc))
            raise Fault(exc.error_code, str(exc))

    @requires_auth
    def smart_search_vrf(self, args):
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
            res = self.nip.smart_search_vrf(
                args.get('auth'),
                args.get('query_string'),
                args.get('search_options', {}),
                args.get('extra_query'),
            )

            # fugly cast from large numbers to string to deal with XML-RPC
            res = xmlrpc_bignum2str(res, ['num_prefixes', 'total_addresses', 'used_addresses', 'free_addresses'])

            return res
        except (AuthError, NipapError) as exc:
            self.logger.debug(str(exc))
            raise Fault(exc.error_code, str(exc))

    #
    # POOL FUNCTIONS
    #
    @requires_auth
    def add_pool(self, args):
        """ Add a pool.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `attr` [struct]
                Attributes which will be set on the new pool.

            Returns ID of created pool.
        """
        try:
            res = self.nip.add_pool(args.get('auth'), args.get('attr'))

            # fugly cast from large numbers to string to deal with XML-RPC
            res = xmlrpc_bignum2str(res, ['member_prefixes', 'used_prefixes', 'free_prefixes', 'total_prefixes',
                                          'total_addresses', 'used_addresses', 'free_addresses'])

            return res
        except (AuthError, NipapError) as exc:
            self.logger.debug(str(exc))
            raise Fault(exc.error_code, str(exc))

    @requires_auth
    def remove_pool(self, args):
        """ Remove a pool.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `pool` [struct]
                Specifies what pool(s) to remove.
        """
        try:
            self.nip.remove_pool(args.get('auth'), args.get('pool'))
        except (AuthError, NipapError) as exc:
            self.logger.debug(str(exc))
            raise Fault(exc.error_code, str(exc))

    @requires_auth
    def list_pool(self, args):
        """ List pools.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `pool` [struct]
                Specifies pool attributes which will be matched.

            Returns a list of structs describing the matching pools.
        """
        try:
            res = self.nip.list_pool(args.get('auth'), args.get('pool'))

            # fugly cast from large numbers to string to deal with XML-RPC
            res = xmlrpc_bignum2str(res, ['member_prefixes', 'used_prefixes', 'free_prefixes', 'total_prefixes',
                                          'total_addresses', 'used_addresses', 'free_addresses'])

            return res
        except (AuthError, NipapError) as exc:
            self.logger.debug(str(exc))
            raise Fault(exc.error_code, str(exc))

    @requires_auth
    def edit_pool(self, args):
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
            res = self.nip.edit_pool(args.get('auth'), args.get('pool'), args.get('attr'))

            # fugly cast from large numbers to string to deal with XML-RPC
            res = xmlrpc_bignum2str(res, ['member_prefixes', 'used_prefixes', 'free_prefixes', 'total_prefixes',
                                          'total_addresses', 'used_addresses', 'free_addresses'])

            return res
        except (AuthError, NipapError) as exc:
            self.logger.debug(str(exc))
            raise Fault(exc.error_code, str(exc))

    @requires_auth
    def search_pool(self, args):
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
            res = self.nip.search_pool(args.get('auth'), args.get('query'), args.get('search_options') or {})

            # fugly cast from large numbers to string to deal with XML-RPC
            res = xmlrpc_bignum2str(res, ['member_prefixes', 'used_prefixes', 'free_prefixes', 'total_prefixes',
                                          'total_addresses', 'used_addresses', 'free_addresses'])

            return res
        except (AuthError, NipapError) as exc:
            self.logger.debug(str(exc))
            raise Fault(exc.error_code, str(exc))

    @requires_auth
    def smart_search_pool(self, args):
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
            res = self.nip.smart_search_pool(
                args.get('auth'),
                args.get('query_string'),
                args.get('search_options') or {},
                args.get('extra_query'),
            )

            # fugly cast from large numbers to string to deal with XML-RPC
            res = xmlrpc_bignum2str(res, ['member_prefixes', 'used_prefixes', 'free_prefixes', 'total_prefixes',
                                          'total_addresses', 'used_addresses', 'free_addresses'])

            return res
        except (AuthError, NipapError) as exc:
            self.logger.debug(str(exc))
            raise Fault(exc.error_code, str(exc))

    #
    # PREFIX FUNCTIONS
    #
    @requires_auth
    def add_prefix(self, args):
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
            res = self.nip.add_prefix(args.get('auth'), args.get('attr'), args.get('args'))
            # mangle result
            res = _mangle_prefix(res)
            return res
        except (AuthError, NipapError) as exc:
            self.logger.debug(str(exc))
            raise Fault(exc.error_code, str(exc))

    @requires_auth
    def list_prefix(self, args):
        """ List prefixes.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `prefix` [struct]
                Prefix attributes to match.

            Returns a list of structs describing the matching prefixes.

            Certain values are casted from numbers to strings because XML-RPC
            simply cannot handle anything bigger than an integer.
        """
        try:
            res = self.nip.list_prefix(args.get('auth'), args.get('prefix') or {})
            # mangle result
            for prefix in res:
                prefix = _mangle_prefix(prefix)
            return res
        except (AuthError, NipapError) as exc:
            self.logger.debug(str(exc))
            raise Fault(exc.error_code, str(exc))

    @requires_auth
    def edit_prefix(self, args):
        """Edit prefix.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `prefix` [struct]
                Prefix attributes which describes what prefix(es) to edit.
            * `attr` [struct]
                Attributes to set on the new prefix.
        """
        try:
            res = self.nip.edit_prefix(args.get('auth'), args.get('prefix'), args.get('attr'))
            # mangle result
            for prefix in res:
                prefix = _mangle_prefix(prefix)
            return res
        except (AuthError, NipapError) as exc:
            self.logger.debug(str(exc))
            raise Fault(exc.error_code, str(exc))

    @requires_auth
    def remove_prefix(self, args):
        """ Remove a prefix.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `prefix` [struct]
                Attributes used to select what prefix to remove.
            * `recursive` [boolean]
                When set to 1, also remove child prefixes.
        """
        try:
            return self.nip.remove_prefix(args.get('auth'), args.get('prefix'), args.get('recursive'))
        except (AuthError, NipapError) as exc:
            self.logger.debug(str(exc))
            raise Fault(exc.error_code, str(exc))

    @requires_auth
    def search_prefix(self, args):
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

            Certain values are casted from numbers to strings because XML-RPC
            simply cannot handle anything bigger than an integer.
        """
        try:
            res = self.nip.search_prefix(args.get('auth'), args.get('query'), args.get('search_options') or {})
            # mangle result
            for prefix in res['result']:
                prefix = _mangle_prefix(prefix)
            return res
        except (AuthError, NipapError) as exc:
            self.logger.debug(str(exc))
            raise Fault(exc.error_code, str(exc))

    @requires_auth
    def smart_search_prefix(self, args):
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

            Certain values are casted from numbers to strings because XML-RPC
            simply cannot handle anything bigger than an integer.
        """

        try:
            self.logger.debug('Entering ssp')
            res = self.nip.smart_search_prefix(
                args.get('auth'),
                args.get('query_string'),
                args.get('search_options') or {},
                args.get('extra_query'),
            )
            # mangle result
            for prefix in res['result']:
                prefix = _mangle_prefix(prefix)
            return res
        except (AuthError, NipapError) as exc:
            self.logger.debug(str(exc))
            self.logger.exception('unhandled..', exc)
            raise Fault(exc.error_code, str(exc))
        except Exception as e:
            self.logger.exception('unhandled..', e)


    @requires_auth
    def find_free_prefix(self, args):
        """ Find a free prefix.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `args` [struct]
                Arguments for the find_free_prefix-function such as what prefix
                or pool to allocate from.
        """

        try:
            return self.nip.find_free_prefix(args.get('auth'), args.get('vrf'), args.get('args'))
        except NipapError as exc:
            self.logger.debug(str(exc))
            raise Fault(exc.error_code, str(exc))

    #
    # ASN FUNCTIONS
    #
    @requires_auth
    def add_asn(self, args):
        """ Add a new ASN.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `attr` [struct]
                ASN attributes.

            Returns the ASN.
        """

        try:
            return self.nip.add_asn(args.get('auth'), args.get('attr'))
        except (AuthError, NipapError) as exc:
            self.logger.debug(str(exc))
            raise Fault(exc.error_code, str(exc))

    @requires_auth
    def remove_asn(self, args):
        """ Removes an ASN.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `asn` [integer]
                An ASN.
        """

        try:
            self.nip.remove_asn(args.get('auth'), args.get('asn'))
        except (AuthError, NipapError) as exc:
            self.logger.debug(str(exc))
            raise Fault(exc.error_code, str(exc))

    @requires_auth
    def list_asn(self, args):
        """ List ASNs.

            Valid keys in the `args`-struct:

            * `auth` [struct]
                Authentication options passed to the :class:`AuthFactory`.
            * `asn` [struct]
                Specifies ASN attributes to match (optional).

            Returns a list of ASNs matching the ASN spec as a list of structs.
        """

        try:
            return self.nip.list_asn(args.get('auth'), args.get('asn') or {})
        except (AuthError, NipapError) as exc:
            self.logger.debug(str(exc))
            raise Fault(exc.error_code, str(exc))

    @requires_auth
    def edit_asn(self, args):
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
            return self.nip.edit_asn(args.get('auth'), args.get('asn'), args.get('attr'))
        except (AuthError, NipapError) as exc:
            self.logger.debug(str(exc))
            raise Fault(exc.error_code, str(exc))

    @requires_auth
    def search_asn(self, args):
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
            return self.nip.search_asn(args.get('auth'), args.get('query'), args.get('search_options') or {})
        except (AuthError, NipapError) as exc:
            self.logger.debug(str(exc))
            raise Fault(exc.error_code, str(exc))

    @requires_auth
    def smart_search_asn(self, args):
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
            return self.nip.smart_search_asn(
                args.get('auth'),
                args.get('query_string'),
                args.get('search_options') or {},
                args.get('extra_query'),
            )
        except (AuthError, NipapError) as exc:
            self.logger.debug(str(exc))
            raise Fault(exc.error_code, str(exc))


if __name__ == '__main__':
    if 'app' not in locals() and 'app' not in globals():
        app = current_app()
    app.run()
