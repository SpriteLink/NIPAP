""" Controller for handling pure AngularJS pages

    Used during the transition phase when the NIPAP web UI is built up
    partly by legacy Jinja2/jQuery and AngularJS components. At this stage
    each section of the NIPAP page (VRF, Prefix, Pool) gets its own action,
    basically just to avoid handling the hilighting of the active section
    in the top menu in AngularJS.
"""

from flask import Blueprint, redirect, render_template, url_for

from auth import login_required

bp = Blueprint('ng', __name__, url_prefix='/ng')


@bp.route('/')
def index():
    return redirect(url_for('ng.prefix'))


@bp.route('/pool')
@login_required
def pool():
    """ Action for handling the pool-section
    """
    return render_template('/ng-pool.html')


@bp.route('/prefix')
@login_required
def prefix():
    """ Action for handling the prefix-section
    """
    return render_template('/ng-prefix.html')


@bp.route('/vrf')
@login_required
def vrf():
    """ Action for handling the vrf-section
    """
    return render_template('/ng-vrf.html')
