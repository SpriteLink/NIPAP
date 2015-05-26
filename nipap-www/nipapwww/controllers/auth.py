import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from nipapwww.lib.base import BaseController, render

from nipap.authlib import AuthFactory, AuthError
from nipap.nipapconfig import NipapConfig

from ConfigParser import NoOptionError

log = logging.getLogger(__name__)

class AuthController(BaseController):
    """ Deals with authentication.
    """

    requires_auth = False


    def login(self):
        """ Show login form.
        """

        if request.method != 'POST':
            cfg = NipapConfig()
            try:
                c.welcome_message = cfg.get('www', 'welcome_message')
            except NoOptionError:
                pass

            return render('login.html')

        # Verify username and password.
        try:
            auth_fact = AuthFactory()
            auth = auth_fact.get_auth(request.params.get('username'), request.params.get('password'), 'nipap')
            if not auth.authenticate():
                c.error = 'Invalid username or password'
                return render('login.html')
        except AuthError as exc:
            c.error = 'Authentication error'
            return render('login.html')

        # Mark user as logged in
        session['user'] = auth.username
        session['full_name'] = auth.full_name
        session['readonly'] = auth.readonly
        session['current_vrfs'] = {}
        session.save()

        # Send user back to the page he originally wanted to get to
        if session.get('path_before_login'):
            redirect(session['path_before_login'])

        else:
            # if previous target is unknown just send the user to a welcome page
            redirect(url(controller='prefix', action='list'))



    def logout(self):
        """ Log out the user and display a confirmation message.
        """

        # remove session
        session.delete()

        return render('login.html')
