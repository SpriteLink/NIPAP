import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to

from nap.lib.base import BaseController, render
import nap.model.nap

log = logging.getLogger(__name__)

class PrefixController(BaseController):

    def index(self):

        return render('/prefix.html')
