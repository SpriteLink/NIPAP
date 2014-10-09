import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from nipapwww.lib.base import BaseController, render

log = logging.getLogger(__name__)

class NgController(BaseController):
    """ Controller for handling pure AngularJS pages

        Used during the transition phase when the NIPAP web UI is built up
        partly by legacy Jinja2/jQuery and AngularJS components. At this stage
        each section of the NIPAP page (VRF, Prefix, Pool) gets its own action,
        basically just to avoid handling the hilighting of the active section
        in the top menu in AngularJS.
    """

    def index(self):
        redirect(url(controller = 'ng', action = 'prefix'))


    def pool(self):
        """ Action for handling the pool-section
        """
        return render('/ng-pool.html')


    def prefix(self):
        """ Action for handling the prefix-section
        """
        return render('/ng-prefix.html')


    def vrf(self):
        """ Action for handling the vrf-section
        """
        return render('/ng-vrf.html')
