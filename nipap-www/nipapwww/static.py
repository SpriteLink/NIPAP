""" Controller for serving static content
"""

from flask import Blueprint, send_from_directory

bp = Blueprint('static', __name__, url_prefix='/')
