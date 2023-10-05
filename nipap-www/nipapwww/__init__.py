__version__     = "0.31.2"
__author__      = "Kristian Larsson, Lukas Garberg"
__author_email__ = "kll@tele2.net, lukas@spritelink.net"
__license__     = "MIT"
__status__      = "Development"
__url__         = "http://SpriteLink.github.io/NIPAP"


def create_app(test_config=None):

    # Moved imports here to be able to import this module without having the
    # dependencies installed. Relevant during initial package build.
    import os
    from flask import Flask, redirect, url_for
    from nipap.nipapconfig import NipapConfig
    import pynipap

    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        NIPAP_CONFIG_PATH="/etc/nipap/nipap.conf",
        SESSION_REFRESH_EACH_REQUEST=False
    )
    if "NIPAP_CONFIG_PATH" in os.environ:
        app.config["NIPAP_CONFIG_PATH"] = os.environ["NIPAP_CONFIG_PATH"]

    # load NIPAP config file
    nipap_config = NipapConfig(app.config["NIPAP_CONFIG_PATH"])
    for cfg_key, cfg_value in dict(nipap_config.items("www")).items():
        app.config[cfg_key.upper()] = cfg_value

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # configure pynipap
    pynipap.xmlrpc_uri = app.config["XMLRPC_URI"]

    # Set up blueprints
    from . import auth, ng, prefix, static, version, xhr
    app.register_blueprint(auth.bp)
    app.register_blueprint(ng.bp)
    app.register_blueprint(prefix.bp)
    app.register_blueprint(static.bp)
    app.register_blueprint(version.bp)
    app.register_blueprint(xhr.bp)

    @app.route('/')
    def index():
        return redirect(url_for('prefix.list'))

    return app
