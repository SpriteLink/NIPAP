""" The base Controller API

    Provides the BaseController class for subclassing.
"""
import logging

from pylons import request, session, url
from pylons.controllers import WSGIController
from pylons.controllers.util import redirect
from pylons.templating import render_jinja2 as render

from napwww.model.napmodel import AuthOptions

log = logging.getLogger(__name__)

class BaseController(WSGIController):

    requires_auth = True


    def __before__(self):
        """ Perform actions before action method is invoked.
            Deals with authentication.
        """

        # set authentication options
        o = AuthOptions(
            {
                'username': session.get('user'),
                'authoritative_source': 'nipap'
            })


        # verify that user is logged in
        if self.requires_auth and 'user' not in session:
            log.error(self.requires_auth)
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
