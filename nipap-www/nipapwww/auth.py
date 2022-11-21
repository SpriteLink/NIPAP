import functools

from flask import (
    Blueprint, current_app, g, redirect, render_template, request, session,
    url_for
)

from nipap.authlib import AuthError, AuthFactory

from pynipap import AuthOptions


bp = Blueprint('auth', __name__, url_prefix='/auth')


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if session.get("user") is None:
            session['path_before_login'] = request.full_path
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view


@bp.before_app_request
def setup_auth():
    """ Set up the environment
    """

    if current_app.config.get("WELCOME_MESSAGE"):
        g.welcome_message = current_app.config.get("WELCOME_MESSAGE")

    # set authentication options
    o = AuthOptions({
                        'username': session.get('user'),
                        'full_name': session.get('full_name'),
                        'authoritative_source': 'nipap',
                        'readonly': session.get('readonly')
                    })


@bp.route('/login', methods=('GET', 'POST'))
def login():
    """ Show login form.
    """

    if request.method != 'POST':
        return render_template('login.html')

    # Verify username and password.
    try:
        auth_fact = AuthFactory()
        auth = auth_fact.get_auth(request.form['username'],
                                  request.form['password'],
                                  'nipap')
        if not auth.authenticate():
            g.error = 'Invalid username or password'
            return render_template('login.html')
    except AuthError:
        g.error = 'Authentication error'
        return render_template('login.html')

    # Mark user as logged in
    path_before_login = session.get('path_before_login')
    session.clear()
    session['user'] = auth.username
    session['full_name'] = auth.full_name
    session['readonly'] = auth.readonly
    session['current_vrfs'] = {}
    session.permanent = True

    # Send user back to the page he originally wanted to get to
    if path_before_login:
        return redirect(path_before_login)

    else:
        # if previous target is unknown just send the user to a welcome page
        return redirect(url_for('prefix.list'))


@bp.route('/logout', methods=('GET',))
def logout():
    """ Log out the user and display a confirmation message.
    """

    # remove session
    session.clear()

    return render_template('login.html')
