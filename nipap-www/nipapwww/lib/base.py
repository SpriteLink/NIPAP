""" The base Controller API

    Provides the BaseController class for subclassing.
"""
import logging

from pylons import request, session, url, tmpl_context as c
from pylons.controllers import WSGIController
from pylons.controllers.util import redirect
from pylons.templating import render_jinja2 as render

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


        # verify that user is logged in
        if self.requires_auth and 'user' not in session:
            # save path
            session['path_before_login'] = request.path_info
            session.save()
            redirect(url(controller='auth', action='login'))



    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        # WSGIController.__call__ dispatches to the Controller method
        # the request is routed to. This routing information is
        # available in environ['pylons.routes_dict']
        return WSGIController.__call__(self, environ, start_response)
