import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from napwww.lib.base import BaseController, render
from napwww.model.napmodel import Schema, Pool, Prefix, NapNonExistentError

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
                c.schema = Schema.get(int(request.params['schema']))
            except NapNonExistentError, e:
                redirect(url(controller = 'prefix', action = 'change_schema'))
        else:
            redirect(url(controller = 'prefix', action = 'change_schema'))

        c.search_opt_parent = "all"
        c.search_opt_child = "none"

        return render('/prefix_list.html')



    def change_schema(self):
        """ Change current schema.
        """

        if 'schema' in request.params:
            c.schema = Schema.get(int(request.params['schema']))

        c.schema_list = Schema.list()

        return render('/change_schema.html')



    def add(self):
        """ Add a prefix.
        """

        # make sure we have a schema
        try:
            c.schema = Schema.get(int(request.params['schema']))
        except (KeyError, NapNonExistentError), e:
            redirect(url(controller='prefix', action='change_schema'))

        # pass prefix to template - if we have any
        if 'prefix' in request.params:
            c.prefix = request.params['prefix']
        else:
            c.prefix = ''

        return render('/prefix_add.html')
