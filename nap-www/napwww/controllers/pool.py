import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from napwww.lib.base import BaseController, render
from napwww.model.napmodel import Schema, Pool

log = logging.getLogger(__name__)

class PoolController(BaseController):



    def index(self):
        # Return a rendered template
        #return render('/pool.mako')
        # or, return a string
        return 'Hello World'



    def list(self):
        """ Displays a list of pools.
        """

        if 'schema' not in request.params:
            redirect(url(controller = 'schema', action = 'list'))

        c.schema = Schema.get(int(request.params['schema']))
        c.pools = Pool.list(c.schema)

        return render('/pool_list.html')



    def add(self):
        """ Add a pool.
        """

        return "foo"
