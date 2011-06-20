import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from napwww.lib.base import BaseController, render
from napwww.model.napmodel import Schema

log = logging.getLogger(__name__)

class SchemaController(BaseController):

    def index(self):
        """ Index page - redirect to list.
        """
        redirect(url(controller="schema", action="list"))



    def list(self):
        """ List schemas.
        """

        if 'schema' in request.params:
            c.schema = Schema.get(int(request.params['schema']))

        c.schemas = Schema.list()
        return render('/schema_list.html')



    def edit(self, id):
        """ Edit a schema
        """

        c.action = 'edit'
        c.schema = Schema.get(int(id))

        # Did we have any action passed to us?
        if 'action' in request.params:

            if request.params['action'] == 'edit':
                c.schema.name = request.params['name']
                c.schema.description = request.params['description']
                c.schema.save()
                redirect(url(controller='schema', action='list'))

        return render('/schema_edit.html')



    def add(self):
        """ Add a new schema.
        """

        c.action = 'add'

        if 'action' in request.params:
            if request.params['action'] == 'add':
                s = Schema()
                s.name = request.params['name']
                s.description = request.params['description']
                s.save()
                redirect(url(controller='schema', action='list'))

        return render('/schema_add.html')



    def remove(self, id):
        """ Removes a schema.
        """

        s = Schema.get(int(id))
        s.remove()

        redirect(url(controller='schema', action='list'))
