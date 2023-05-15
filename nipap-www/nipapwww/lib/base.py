""" The base Controller API

    Provides the BaseController class for subclassing.
"""
import json
import jwt
import logging
import requests
import time

from pylons import request, response, session, url, tmpl_context as c
from pylons.controllers import WSGIController
from pylons.controllers.util import redirect
from pylons.templating import render_jinja2 as render

from nipap.nipapconfig import NipapConfig
from pynipap import AuthOptions
import nipapwww

log = logging.getLogger(__name__)

class BaseController(WSGIController):

    requires_auth = True


    def __before__(self):
        """ Perform actions before action method is invoked.
            Deals with authentication.
        """

        # Add version to template context
        c.www_version = nipapwww.__version__

        # set authentication options
        o = AuthOptions(
            {
                'username': session.get('user'),
                'full_name': session.get('full_name'),
                'authoritative_source': 'nipap',
                'readonly': session.get('readonly')
            })



        # An implementation of Single Sign On (SSO) using Authorization Code flow:
        # The user will try to access the application.
        # The application will redirect the user to the Identity Provider with a specific set of query parameters.
        # The user will then authenticate to authorize endpoint using predefined method.
        # The user is redirected back to the application with an authorization code.
        # The application uses the authorization code together with the ClientID and Client Secret to retrieve an ID Token from the /token endpoint of the Identity Provider.

        cfg = NipapConfig()
        c.SSO = cfg.get('www', 'login_type') == 'SSO'
        c.ssoErrorMessage = cfg.get('www', 'error_message')
        if str(cfg.get('www', 'login_type')) == 'SSO':
            if str(request.path_info) != '/code' and str(request.path_info) != '/auth/unauthorized':
                if 'user' in session:
                    jwt_decoded = jwt.decode(session['user']['oidc']['id_token'], verify=False)
                    # Check if jwt has expired
                    if jwt_decoded['exp'] < time.time():
                        # Get new token from WAME
                        token_request = {
                            'grant_type': 'refresh_token',
                            'client_id': cfg.get('www', 'client_id'),
                            'client_secret': cfg.get('www', 'client_secret'),
                            'refresh_token': session['user']['oidc']['refresh_token']
                        }
                        resp = requests.request(
                            method = 'POST',
                            url = cfg.get('www', 'baseUrl') + 'token',
                            data = token_request
                        )
                        if resp.status_code == 200:
                            self.raiseException()
                        # Get user and groups from JWT
                        groups = None
                        try:
                            groups = jwt_decoded[cfg.get('www', 'scope')]
                        except:
                            self.raiseException()
                        if cfg.get('www', 'read_write_access') not in groups and cfg.get('www', 'read_only_access') not in groups:
                            self.raiseException()
                        if not isinstance(groups, list):
                            groups = [groups]
                        # Update user info and groups in session
                        session['user'] = {
                            "username": jwt_decoded['sub'],
                            "groups": groups,
                            "oidc": {
                                "id_token": token_response['id_token'],
                                "access_token": token_response['access_token'],
                                "refresh_token": token_response['refresh_token']
                            }
                        }
                else:
                    if request.params and request.params['state'] and request.params['code']:
                        code = request.params['code']
                        state = request.params['state']
                        state_data = session.get(state)
                        if session.get(state):
                            session[state] = None
                            # Get token from WAME
                            token_request = {
                                'grant_type': 'authorization_code',
                                'client_id': cfg.get('www', 'client_id'),
                                'client_secret': cfg.get('www', 'client_secret'),
                                'code': code,
                                'redirect_uri': state_data['redirect']
                            }
                            resp = requests.request(
                                method = 'POST',
                                url = cfg.get('www', 'baseUrl') + 'token',
                                data = token_request
                            )
                            token_response = resp.json()
                            id = token_response.get('id_token')
                            decoded_jwt = None
                            try:
                                decoded_jwt = jwt.decode(str(id), verify=False)
                            except:
                                self.reiseException()
                            if state_data['nonce'] != decoded_jwt['nonce']:
                                self.raiseException()
                            # Get user and groups from JWT
                            groups = None
                            try:
                                groups = decoded_jwt[cfg.get('www', 'scope')]
                            except:
                                self.raiseException()
                            if cfg.get('www', 'read_write_access') not in groups:
                                self.raiseException()
                            if not isinstance(groups, list):
                                groups = [groups]
                            # Save user info and groups in session
                            session['user'] = {
                                "username": decoded_jwt['sub'],
                                "groups": groups,
                                "oidc": {
                                    "id_token": token_response['id_token'],
                                    "access_token": token_response['access_token'],
                                    "refresh_token": token_response['refresh_token']
                                }
                            }
                            session.save()
                            #redirect(state_data['redirect'])
                            #redirect(url(controller='prefix', action='list'))
                    else:
                        redirect(cfg.get('www', 'callbackUrl') + '/code')

        # verify that user is logged in
        if self.requires_auth and 'user' not in session:
            # save path
            session['path_before_login'] = request.path_info
            session.save()
            if str(cfg.get('www', 'login_type')) != 'SSO':
                redirect(url(controller='auth', action='login'))

    def raiseException(self):
            if 'user' in session:
                session['user'] = None
            session.delete()
            redirect(url(controller='auth', action='unauthorized'))

    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        # WSGIController.__call__ dispatches to the Controller method
        # the request is routed to. This routing information is
        # available in environ['pylons.routes_dict']
        return WSGIController.__call__(self, environ, start_response)
