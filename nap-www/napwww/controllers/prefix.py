import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from napwww.lib.base import BaseController, render
from napwww.model.napmodel import Schema, Pool, Prefix

log = logging.getLogger(__name__)

class PrefixController(BaseController):

    def index(self):
        """ Index page

            If schema is set, redirect to prefix list.
            Otherwise, redirect to schema selection page.
        """

        if 'view' in request.params:
            view = request.params['view']
        else:
            view = 'prefix'

        if 'schema' not in request.params:
            redirect(url(controller = 'prefix', action = 'change_schema', view = view))

        redirect(url(controller = 'prefix', action = 'list', schema = request.params['schema'], view = view))



    def list(self):
        """ Prefix list.
        """

        # Handle schema in session.
        if 'schema' in request.params:
            try:
                c.schema = Schema.list({'id': int(request.params['schema'])})[0]
            except IndexError:
                redirect(url(controller = 'prefix', action = 'change_schema'))
        else:
            redirect(url(controller = 'prefix', action = 'change_schema'))

        c.search_opt_parent = 'immediate';
        c.search_opt_child = 'all';

        return render('/index.html')



    def change_schema(self):
        """ Change current schema.
        """

        if 'schema' in request.params:
            c.schema = Schema.list({'id': int(request.params['schema'])})[0]

        c.schema_list = Schema.list()

        return render('/change_schema.html')
