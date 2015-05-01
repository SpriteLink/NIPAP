import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from nipapwww.lib.base import BaseController, render
from pynipap import VRF

log = logging.getLogger(__name__)

class VrfController(BaseController):


    def index(self):
        """ Index page - redirect to list.
        """
        redirect(url(controller="vrf", action="list"))



    def list(self):
        """ List VRFs.
        """

        return render('/vrf_list.html')



    def edit(self, id):
        """ Edit a VRF
        """

        c.action = 'edit'
        c.edit_vrf = VRF.get(int(id))

        # Did we have any action passed to us?
        if 'action' in request.params:

            if request.params['action'] == 'edit':
                if request.params['rt'].strip() == '':
                    c.edit_vrf.rt = None
                else:
                    c.edit_vrf.rt = request.params['rt'].strip()

                if request.params['name'].strip() == '':
                    c.edit_vrf.name = None
                else:
                    c.edit_vrf.name = request.params['name'].strip()
                c.edit_vrf.description = request.params['description']
                c.edit_vrf.save()

        return render('/vrf_edit.html')



    def add(self):
        """ Add a new VRF.
        """

        c.action = 'add'

        if 'action' in request.params:
            if request.params['action'] == 'add':
                v = VRF()
                if request.params['rt'].strip() != '':
                    v.rt = request.params['rt']
                if request.params['name'].strip() != '':
                    v.name = request.params['name']
                v.description = request.params['description']

                v.save()
                redirect(url(controller='vrf', action='list'))

        return render('/vrf_add.html')



    def remove(self, id):
        """ Removes a VRF.
        """

        v = VRF.get(int(id))
        v.remove()

        redirect(url(controller='vrf', action='list'))
