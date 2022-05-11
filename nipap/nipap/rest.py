""" NIPAP REST
    ==============
    This module contains the actual functions presented over the REST API. All
    functions are quite thin and mostly wrap around the functionalty provided by
    the backend module.
"""

import datetime
import logging
import time
import pytz
import json
from functools import wraps
from flask import Flask, request, Response, got_request_exception, jsonify
from flask_restful import Resource, Api, abort

from backend import Nipap, NipapError
import nipap
from authlib import AuthFactory, AuthError

def setup(app):
    api = Api(app, prefix="/rest/v1")
    api.add_resource(NipapPrefixRest, "/prefixes")

    return app


def combine_request_args():
        args = {}

        request_authoritative_source = request.headers.get('NIPAP-Authoritative-Source')
        request_nipap_username = request.headers.get('NIPAP-Username')
        request_nipap_fullname = request.headers.get('NIPAP-Full-Name')
        request_authorization_header = request.headers.get('Authorization')

        request_body = request.json
        request_queries = request.args.to_dict()

        if request_authoritative_source:
            authoritative_source = { 'auth':{'authoritative_source': request_authoritative_source}}
            args.update(authoritative_source)

            if request_nipap_username:
                args['auth'].update({'username': request_nipap_username})

            if request_nipap_fullname:
                args['auth'].update({'full_name': request_nipap_fullname})
        elif request_authorization_header and \
                request_authorization_header.startswith('Bearer'):
            authoritative_source = {'auth': {'authoritative_source': 'jwt'}}
            args.update(authoritative_source)

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
    res['total_addresses'] = unicode(res['total_addresses'])
    res['used_addresses'] = unicode(res['used_addresses'])
    res['free_addresses'] = unicode(res['free_addresses'])

    # postgres has notion of infinite while datetime hasn't, if expires
    # is equal to the max datetime we assume it is infinity and instead
    # represent that as None
    if res['expires'].tzinfo is None:
        res['expires'] = pytz.utc.localize(res['expires'])
    if res['expires'] == pytz.utc.localize(datetime.datetime.max):
        res['expires'] = None

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

        if type(nipap_args) != dict:
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
                return authenticate()

        # init AuthFacory()
        af = AuthFactory()
        auth = None
        if bearer_token:
            auth = af.get_auth_bearer_token(bearer_token, auth_source,
                                            auth_options or {})

            # authenticated?
            if not auth.authenticate():
                self.logger.debug("Invalid bearer token.")
                abort(401, error={"code": 401,
                                  "message": "Invalid bearer token."})
        else:
            auth = af.get_auth(request.authorization.username,
                    request.authorization.password, auth_source, auth_options or {})

            # authenticated?
            if not auth.authenticate():
                self.logger.debug("Incorrect username or password.")
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


class NipapPrefixRest(Resource):

    def __init__(self):
        self.nip = Nipap()
        self.logger = logging.getLogger(self.__class__.__name__)


    @requires_auth
    def get(self, args):

        query = args.get('prefix')
        search_query = {}
        if query is not None:
            # Create search query dict from request params
            query_parts = []
            for field, search_value in query.items():
                query_parts.append(get_query_for_field(field, search_value))
            search_query = query_parts[0]
            for query_part in query_parts[1:]:
                search_query = {
                    "val1": search_query,
                    "operator": "and",
                    "val2": query_part
                }

        try:
            result = self.nip.search_prefix(args.get('auth'), search_query)

            # mangle result
            for prefix in result['result']:
                prefix = _mangle_prefix(prefix)

            result = jsonify(result['result'])
            return result

        except (AuthError, NipapError) as exc:
            self.logger.debug(unicode(exc))
            abort(500, error={"code": exc.error_code, "message": str(exc)})
        except Exception as err:
            self.logger.error(unicode(err))
            abort(500, error={"code": 500, "message": "Internal error"})


    @requires_auth
    def post(self, args):
        try:
            result = self.nip.add_prefix(
                args.get('auth'), args.get('attr'), args.get('args'))

            result["free_addresses"] = str(result.get("free_addresses"))
            result["total_addresses"] = str(result.get("total_addresses"))
            result["added"] = result.get("added").isoformat()
            result["expires"] = result.get("expires").isoformat()
            result["last_modified"] = result.get("last_modified").isoformat()
            result["used_addresses"] = str(result.get("used_addresses"))
            result = jsonify(result)
            return result
        except (AuthError, NipapError) as exc:
            self.logger.debug(unicode(exc))
            abort(500, error={"code": exc.error_code, "message": str(exc)})
        except Exception as err:
            self.logger.error(unicode(err))
            abort(500, error={"code": 500, "message": "Internal error"})


    @requires_auth
    def delete(self, args):
        try:
            # as of now remove_prefix doesn't return any values
            self.nip.remove_prefix(args.get('auth'), args.get('prefix'))
            return jsonify(args.get('prefix'))
        except (AuthError, NipapError) as exc:
            self.logger.debug(unicode(exc))
            abort(500, error={"code": exc.error_code, "message": str(exc)})
        except Exception as err:
            self.logger.error(unicode(err))
            abort(500, error={"code": 500, "message": "Internal error"})
