from flask import Blueprint, g, render_template

from .auth import login_required

bp = Blueprint('prefix', __name__, url_prefix='/prefix')


@bp.route('/list')
@login_required
def list():
    """ Prefix list.
    """

    g.search_opt_parent = "all"
    g.search_opt_child = "none"

    return render_template('/prefix_list.html')
