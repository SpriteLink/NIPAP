import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from nipapwww.lib.base import BaseController, render
from pynipap import VRF, Pool, Prefix, NipapNonExistentError

log = logging.getLogger(__name__)

class PrefixController(BaseController):

    def index(self):
        """ Index page

            Redirect to prefix list.
        """

        redirect(url(controller = 'prefix', action = 'list'))



    def list(self):
        """ Prefix list.
        """

        c.search_opt_parent = "all"
        c.search_opt_child = "none"

        return render('/prefix_list.html')



    def add(self):
        """ Add a prefix.
        """

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

        # find prefix
        c.prefix = Prefix.get(int(id))

        # we got a HTTP POST - edit object
        if request.method == 'POST':
            c.prefix.prefix = request.params['prefix_prefix']
            c.prefix.description = request.params['prefix_description']

            if request.params['prefix_node'].strip() == '':
                c.prefix.node = None
            else:
                c.prefix.node = request.params['prefix_node']

            if request.params['prefix_country'].strip() == '':
                c.prefix.country = None
            else:
                c.prefix.country = request.params['prefix_country']

            if request.params['prefix_comment'].strip() == '':
                c.prefix.comment = None
            else:
                c.prefix.comment = request.params['prefix_comment']

            if request.params['prefix_order_id'].strip() == '':
                c.prefix.order_id = None
            else:
                c.prefix.order_id = request.params['prefix_order_id']

            if request.params['prefix_vrf'].strip() == '':
                c.prefix.vrf = None
            else:
                # TODO: handle non-existent VRF...
                c.prefix.vrf = VRF.list({ 'rt': request.params['prefix_vrf'] })[0]

            if request.params.get('prefix_monitor') != None:
                c.prefix.monitor = True
            else:
                c.prefix.monitor = False

            c.prefix.alarm_priority = request.params['prefix_alarm_priority']
            c.prefix.save()
            redirect(url(controller='prefix', action='list'))


        return render('/prefix_edit.html')


    def remove(self, id):
        """ Remove a prefix.
        """

        # find prefix
        c.prefix = Prefix.get(int(id))

        if 'confirmed' not in request.params:
            return render('/prefix_remove_confirm.html')

        c.prefix.remove()
        redirect(url(controller='prefix', action='list'))
