import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from napwww.lib.base import BaseController, render

log = logging.getLogger(__name__)

class AuthController(BaseController):
    """ Deals with authentication.
    """

    requires_auth = False


    def login(self):
        """ Show login form.
        """

        if request.method != 'POST':
            return render('login.html')

        # Verify username and password.
        if not (request.params.get('username') == 'test' and request.params.get('password') == 'test'):
            c.error = 'Invalid username or password'
            return render('login.html')

        # Mark user as logged in
        session['user'] = request.params.get('username')
        session.save()

        # Send user back to the page he originally wanted to get to
        if session.get('path_before_login'):
            log.error(session.get('path_before_login'))
            redirect(session['path_before_login'])

        else:
            # if previous target is unknown just send the user to a welcome page
            redirect(url(controller='schema', action='list'))



    def logout(self):
        """ Log out the user and display a confirmation message.
        """

        if 'user' in session:
            del session['user']
            session.save()

        return render('login.html')
