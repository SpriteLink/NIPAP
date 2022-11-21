""" Controller for serving static content
"""

from flask import Blueprint, send_from_directory

bp = Blueprint('static', __name__, url_prefix='/')


@bp.route('/images/<path:path>')
def images(path):
    """ foo
    """
    return send_from_directory('static/images', path)


@bp.route('/fonts/<path:path>')
def fonts(path):
    """ bar
    """
    return send_from_directory('static/fonts', path)
