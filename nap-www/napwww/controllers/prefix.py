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
            redirect(url(controller = 'schema', action = 'list'))

        redirect(url(controller = 'prefix', action = 'list', schema = request.params['schema'], view = view))



    def list(self):
        """ Prefix list.
        """

        # Handle schema in session.
        if 'schema' in request.params:
            try:
                c.schema = Schema.get(int(request.params['schema']))
            except NapNonExistentError, e:
                redirect(url(controller = 'schema', action = 'list'))
        else:
            redirect(url(controller = 'schema', action = 'list'))

        c.search_opt_parent = "all"
        c.search_opt_child = "none"

        return render('/prefix_list.html')



    def add(self):
        """ Add a prefix.
        """

        # make sure we have a schema
        try:
            c.schema = Schema.get(int(request.params['schema']))
        except (KeyError, NapNonExistentError), e:
            redirect(url(controller = 'schema', action = 'list'))

        # pass prefix to template - if we have any
        if 'prefix' in request.params:
            c.prefix = request.params['prefix']
        else:
            c.prefix = ''

        c.search_opt_parent = "all"
        c.search_opt_child = "none"

        return render('/prefix_add.html')



    def edit(self, id):
        """ Edit a prefix.
        """

        # make sure we have a schema
        try:
            c.schema = Schema.get(int(request.params['schema']))
        except (KeyError, NapNonExistentError), e:
            redirect(url(controller = 'schema', action = 'list'))

        # find prefix
        c.prefix = Prefix.get(c.schema, int(id))

        # we got a HTTP POST - edit object
        if request.method == 'POST':
            c.prefix.prefix = request.params['prefix_prefix']
            c.prefix.description = request.params['prefix_description']
            c.prefix.node = request.params['prefix_node']
            c.prefix.country = request.params['prefix_country']
            c.prefix.alarm_priority = request.params['prefix_alarm_priority']
            c.prefix.comment = request.params['prefix_comment']
            if request.params['prefix_span_order'] == '':
                c.prefix.span_order = None
            else:
                c.prefix.span_order = int(request.params['prefix_span_order'])
            if request.params.get('prefix_monitor') != None:
                c.prefix.monitor = True
            else:
                c.prefix.monitor = False
            c.prefix.save()
            redirect(url(controller='prefix', action='list', schema=c.schema.id))


        return render('/prefix_edit.html')
