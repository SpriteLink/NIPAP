import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from napwww.lib.base import BaseController, render
from napwww.model.napmodel import Schema, Pool, Prefix

log = logging.getLogger(__name__)

class PoolController(BaseController):



    def index(self):

        if 'schema' not in request.params:
            redirect(url(controller = 'schema', action = 'list'))
        schema = Schema.get(int(request.params['schema']))

        redirect(url(controller = 'pool', action = 'list', schema = schema.id))



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

        if 'schema' not in request.params:
            redirect(url(controller = 'schema', action = 'list'))
        c.schema = Schema.get(int(request.params['schema']))

        # Adding to Nap
        if request.method == 'POST':
            p = Pool()
            p.schema = c.schema
            p.name = request.params['name']
            p.description = request.params['description']
            if 'default_type' in request.params:
                p.default_type = request.params['default_type']
            else:
                p.default_type = None

            if request.params['ipv4_default_prefix_length'].strip() == '':
                p.ipv4_default_prefix_length = None
            else:
                p.ipv4_default_prefix_length = int(request.params['ipv4_default_prefix_length'])

            if request.params['ipv6_default_prefix_length'].strip() == '':
                p.ipv6_default_prefix_length = None
            else:
                p.ipv6_default_prefix_length = int(request.params['ipv6_default_prefix_length'])

            p.save()
            redirect(url(controller = 'pool', action = 'list', schema = c.schema.id))

        return render("/pool_add.html")



    def edit(self, id):
        """ Edit a pool.
        """

        if 'schema' not in request.params:
            redirect(url(controller = 'schema', action = 'list'))
        c.schema = Schema.get(int(request.params['schema']))

        c.pool = Pool.get(c.schema, int(id))
        c.prefix_list = Prefix.list(c.schema, {'pool': c.pool.id})

        # save changes to Nap
        if request.method == 'POST':
            c.pool.name = request.params['name']
            c.pool.description = request.params['description']
            c.pool.default_type = request.params['default_type']
            if request.params['ipv4_default_prefix_length'].strip() == '':
                c.pool.ipv4_default_prefix_length = None
            else:
                c.pool.ipv4_default_prefix_length = int(request.params['ipv4_default_prefix_length'])
            if request.params['ipv6_default_prefix_length'].strip() == '':
                c.pool.ipv6_default_prefix_length = None
            else:
                c.pool.ipv6_default_prefix_length = int(request.params['ipv6_default_prefix_length'])
            c.pool.save()
            redirect(url(controller = 'pool', action = 'list', schema = c.schema.id))

        return render("/pool_edit.html")



    def remove(self, id):
        """ Remove pool.
        """

        if 'schema' not in request.params:
            redirect(url(controller = 'schema', action = 'list'))
        schema = Schema.get(int(request.params['schema']))

        p = Pool.get(schema, int(id))
        p.remove()
        redirect(url(controller = 'pool', action = 'list', schema = schema.id))



    def remove_prefix(self, id):
        """ Remove a prefix from pool 'id'.
        """

        if 'schema' not in request.params:
            redirect(url(controller = 'schema', action = 'list'))
        schema = Schema.get(int(request.params['schema']))

        if 'prefix' not in request.params:
            abort(400, 'Missing prefix.')
        prefix = Prefix.get(schema, int(request.params['prefix']))
        prefix.pool = None
        prefix.save()

        redirect(url(controller = 'pool', action = 'edit', id = id, schema = schema.id))



    def add_prefix(self, id):
        """ Add a prefix to pool 'id'
        """

        if 'schema' not in request.params:
            redirect(url(controller = 'schema', action = 'list'))
        schema = Schema.get(int(request.params['schema']))

        if 'prefix' not in request.params:
            abort(400, 'Missing prefix.')

        pool = Pool.get(schema, int(id))

        prefix = Prefix.get(schema, int(request.params['prefix']))
        prefix.pool = pool
        prefix.save()

        redirect(url(controller = 'pool', action = 'edit', id = id, schema = schema.id))
