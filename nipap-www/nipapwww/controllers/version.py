import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from nipapwww.lib.base import BaseController, render

import pynipap

log = logging.getLogger(__name__)

class VersionController(BaseController):

    def index(self):
        """ Display NIPAP version info
        """
        c.pynipap_version = pynipap.__version__
        try:
            c.nipapd_version = pynipap.nipapd_version()
        except:
            c.nipapd_version = 'unknown'

        c.nipap_db_version = pynipap.nipap_db_version()

        return render('/version.html')
