from flask import Blueprint, g, render_template

import nipapwww

import pynipap

bp = Blueprint('version', __name__, url_prefix='/version')


@bp.before_app_request
def set_version():
    """ Add version
    """
    g.www_version = nipapwww.__version__


@bp.route('/')
def show_version():
    """ Display NIPAP version info
    """
    g.pynipap_version = pynipap.__version__
    try:
        g.nipapd_version = pynipap.nipapd_version()
    except pynipap.NipapError:
        g.nipapd_version = 'unknown'

    g.nipap_db_version = pynipap.nipap_db_version()

    return render_template('/version.html')
