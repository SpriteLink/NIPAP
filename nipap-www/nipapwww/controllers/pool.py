import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from nipapwww.lib.base import BaseController, render
from pynipap import Pool, Prefix

log = logging.getLogger(__name__)

class PoolController(BaseController):



    def index(self):
        redirect(url(controller = 'pool', action = 'list'))



    def list(self):
        """ Displays a list of pools.
        """

        return render('/pool_list.html')



    def add(self):
        """ Add a pool.
        """

        # Adding to NIPAP
        if request.method == 'POST':
            p = Pool()
            p.name = request.params.get('name')
            p.description = request.params.get('description')
            p.default_type = request.params.get('default_type')

            if request.params['ipv4_default_prefix_length'].strip() != '':
                p.ipv4_default_prefix_length = request.params['ipv4_default_prefix_length']

            if request.params['ipv6_default_prefix_length'].strip() != '':
                p.ipv6_default_prefix_length = request.params['ipv6_default_prefix_length']

            p.save()
            redirect(url(controller = 'pool', action = 'list'))

        return render("/pool_add.html")



    def edit(self, id):
        """ Edit a pool.
        """

        c.pool = Pool.get(int(id))
        c.prefix_list = Prefix.list({ 'pool_id': c.pool.id })
        c.prefix = ''

        # save changes to NIPAP
        if request.method == 'POST':
            c.pool.name = request.params['name']
            c.pool.description = request.params['description']
            c.pool.default_type = request.params['default_type']
            if request.params['ipv4_default_prefix_length'].strip() == '':
                c.pool.ipv4_default_prefix_length = None
            else:
                c.pool.ipv4_default_prefix_length = request.params['ipv4_default_prefix_length']
            if request.params['ipv6_default_prefix_length'].strip() == '':
                c.pool.ipv6_default_prefix_length = None
            else:
                c.pool.ipv6_default_prefix_length = request.params['ipv6_default_prefix_length']
            c.pool.save()
            redirect(url(controller = 'pool', action = 'list'))

        c.search_opt_parent = 'all'
        c.search_opt_child = 'none'

        return render("/pool_edit.html")



    def remove(self, id):
        """ Remove pool.
        """

        p = Pool.get(int(id))
        p.remove()
        redirect(url(controller = 'pool', action = 'list'))



    def remove_prefix(self, id):
        """ Remove a prefix from pool 'id'.
        """

        if 'prefix' not in request.params:
            abort(400, 'Missing prefix.')
        prefix = Prefix.get(int(request.params['prefix']))
        prefix.pool = None
        prefix.save()

        redirect(url(controller = 'pool', action = 'edit', id = id))



    def add_prefix(self, id):
        """ Add a prefix to pool 'id'
        """

        if 'prefix' not in request.params:
            abort(400, 'Missing prefix.')

        pool = Pool.get(int(id))

        prefix = Prefix.get(int(request.params['prefix']))
        prefix.pool = pool
        prefix.save()

        redirect(url(controller = 'pool', action = 'edit', id = id))
