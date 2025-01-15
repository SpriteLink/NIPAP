""" NIPAP REST
    ==============
    This module contains the actual functions presented over the REST API. All
    functions are quite thin and mostly wrap around the functionalty provided by
    the backend module.
"""

import datetime
import logging
import pytz
from functools import wraps
from flask import request, Response, jsonify
from flask_restx import Resource, Api, Namespace, abort

from .backend import Nipap, NipapError, prefix_search_options_spec
from .authlib import AuthFactory, AuthError
from .tracing import create_span_rest

logger = logging.getLogger(__name__)

prefix_ns = Namespace(name="prefixes", description="Prefix operations", validate=True)

def setup(app):
    api = Api(app, prefix="/rest/v1")
    api.add_namespace(prefix_ns, path="/prefixes")

    return app


def combine_request_args():
        args = {}

        request_authoritative_source = request.headers.get('NIPAP-Authoritative-Source')
        request_nipap_username = request.headers.get('NIPAP-Username')
        request_nipap_fullname = request.headers.get('NIPAP-Full-Name')

        if request.method in ("POST", "PUT"):
            request_body = request.json
        else:
            request_body = None
        request_queries = request.args.to_dict()

        if request_authoritative_source:
            authoritative_source = { 'auth':{'authoritative_source': request_authoritative_source}}
            args.update(authoritative_source)

            if request_nipap_username:
                args['auth'].update({'username': request_nipap_username})

            if request_nipap_fullname:
                args['auth'].update({'full_name': request_nipap_fullname})

        if request_queries and request.method == 'POST':
            temp_args = {}
            if request_queries.get("fromPoolName"):
                from_pool_name = {"from-pool": {"name": str(request_queries.get("fromPoolName"))}}
                family = {"family": request_queries.get("family")}
                prefix_length = {"prefix_length": int(request_queries.get("prefixLength"))}
                temp_args.update(from_pool_name)
                temp_args.update(family)
                temp_args.update(prefix_length)
            else:
                from_prefix = {"from-prefix": [request_queries.get("fromPrefix")]}
                prefix_length = {"prefix_length": request_queries.get("prefixLength")}
                temp_args.update(from_prefix)
                temp_args.update(prefix_length)

            args.update({'args': temp_args})

        elif request_queries and not request.method == 'POST':
            args.update({'prefix': request_queries})

        if request_body:
            args['attr'] = request_body

        return args


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
    if res['expires'] == pytz.utc.localize(datetime.datetime.max):
        res['expires'] = None
    else:
        res['expires'] = res['expires'].isoformat()

    # cast of datetime so that JSON is in correct format
    res['added'] = res['added'].isoformat()
    res['last_modified'] = res['last_modified'].isoformat()

    return res


def authenticate():
    """ Sends a 401 response that enables basic auth
    """
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    """ Class decorator for REST functions that requires auth
    """
    @wraps(f)
    def decorated(self, *args, **kwargs):
        """
        """

        # small hack
        args = args + (combine_request_args(),)

        # Fetch auth options from args
        auth_options = {}
        nipap_args = {}

        # validate function arguments
        if len(args) == 1:
            nipap_args = args[0]
        else:
            self.logger.debug("Malformed request: got %d parameters" % len(args))
            abort(401, error={"code": 401, "message": "Malformed request: got %d parameters" % len(args)})

        if type(nipap_args) is not dict:
            self.logger.debug("Function argument is not struct")
            abort(401, error={"code": 401, "message": "Function argument is not struct"})

        # fetch auth options
        try:
            auth_options = nipap_args['auth']
            if type(auth_options) is not dict:
                raise ValueError()
        except (KeyError, ValueError):
            self.logger.debug("Missing/invalid authentication options in request.")
            abort(401, error={"code": 401, "message": "Missing/invalid authentication options in request."})

        # fetch authoritative source
        try:
            auth_source = auth_options['authoritative_source']
        except KeyError:
            self.logger.debug("Missing authoritative source in auth options.")
            abort(401, error={"code": 401, "message": "Missing authoritative source in auth options."})

        bearer_token = None
        if not request.authorization:
            # Check for bearer auth, Werkzeug only supports BASIC and DIGEST
            auth_header = request.headers.get("Authorization", None)
            if auth_header and auth_header.startswith("Bearer"):
                bearer_token = auth_header.split(" ")[1]
            if not bearer_token:
                logger.info("Authentication failed, missing auth method")
                abort(authenticate())

        # init AuthFacory()
        af = AuthFactory()
        auth = None
        if bearer_token:
            auth = af.get_auth_bearer_token(bearer_token, auth_source,
                                            auth_options or {})

            # authenticated?
            if not auth.authenticate():
                abort(401, error={"code": 401,
                                  "message": "Invalid bearer token"})
        else:
            auth = af.get_auth(request.authorization.username,
                    request.authorization.password, auth_source, auth_options or {})

            # authenticated?
            if not auth.authenticate():
                abort(401, error={"code": 401, "message": "Incorrect username or password"})

        # Replace auth options in API call arguments with auth object
        new_args = dict(args[0])
        new_args['auth'] = auth

        return f(self, *(new_args,), **kwargs)

    return decorated


def get_query_for_field(field, search_value):

    operator = "="

    fields_supporting_case_insesitive_search = ['description',
                                                'comment',
                                                'node',
                                                'country',
                                                'customer_id',
                                                'authoritative_source',
                                                'order_id']
    if field in fields_supporting_case_insesitive_search:
        operator = "~*"
        search_value = '^' + search_value + '$'

    return {
            'operator': operator,
            'val1': field,
            'val2': search_value
        }


@prefix_ns.route("")
class NipapPrefix(Resource):

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)

        self.nip = Nipap()
        self.logger = logging.getLogger(self.__class__.__name__)


    @requires_auth
    @create_span_rest
    def get(self, args):
        """ Search/list prefixes
        """

        query = args.get('prefix')
        search_query = {}
        search_options = {}
        if query is not None:
            # Create search query dict from request params
            query_parts = []
            for field, value in list(query.items()):
                if field in prefix_search_options_spec.keys():
                    search_options[field] = value
                else:
                    query_parts.append(get_query_for_field(field, value))
            search_query = query_parts[0]
            for query_part in query_parts[1:]:
                search_query = {
                    "val1": search_query,
                    "operator": "and",
                    "val2": query_part
                }

        try:
            result = self.nip.search_prefix(args.get('auth'), search_query, search_options)

            # mangle result
            result['result'] = [ _mangle_prefix(prefix) for prefix in result['result'] ]

            return jsonify(result['result'])

        except (AuthError, NipapError) as exc:
            self.logger.debug(str(exc))
            abort(500, error={"code": exc.error_code, "message": str(exc)})
        except Exception as err:
            self.logger.error(str(err))
            abort(500, error={"code": 500, "message": "Internal error"})

    @requires_auth
    @create_span_rest
    def post(self, args):
        """ Add prefix
        """
        try:
            result = self.nip.add_prefix(args.get('auth'),
                                         args.get('attr'),
                                         args.get('args'))

            return jsonify(_mangle_prefix(result))

        except (AuthError, NipapError) as exc:
            self.logger.debug(str(exc))
            abort(500, error={"code": exc.error_code, "message": str(exc)})
        except Exception as err:
            self.logger.error(str(err))
            abort(500, error={"code": 500, "message": "Internal error"})


    @requires_auth
    @create_span_rest
    def put(self, args):
        """ Edit prefix
        """
        try:
            result = self.nip.edit_prefix(args.get('auth'),
                                          args.get('prefix'),
                                          args.get('attr'))

            result = [_mangle_prefix(prefix) for prefix in result]
            return jsonify(result)

        except (AuthError, NipapError) as exc:
            self.logger.debug(str(exc))
            abort(500, error={"code": exc.error_code, "message": str(exc)})
        except Exception as err:
            self.logger.error(str(err))
            abort(500, error={"code": 500, "message": "Internal error"})


    @requires_auth
    @create_span_rest
    def delete(self, args):
        """ Remove prefix
        """
        try:
            # as of now remove_prefix doesn't return any values
            self.nip.remove_prefix(args.get('auth'), args.get('prefix'))
            return jsonify(args.get('prefix'))
        except (AuthError, NipapError) as exc:
            self.logger.debug(str(exc))
            abort(500, error={"code": exc.error_code, "message": str(exc)})
        except Exception as err:
            self.logger.error(str(err))
            abort(500, error={"code": 500, "message": "Internal error"})
