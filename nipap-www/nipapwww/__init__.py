__version__     = "0.32.4"
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
    from nipap.nipapconfig import NipapConfig, NipapConfigError
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

    # configure tracing
    if nipap_config.has_section("tracing"):
        try:
            import nipap.tracing
            from opentelemetry.instrumentation.wsgi import OpenTelemetryMiddleware
            from opentelemetry.sdk.trace.sampling import _KNOWN_SAMPLERS

            sampler = None

            if nipap_config.has_option("tracing", "otel_traces_sampler"):
                trace_sampler = nipap_config.get("tracing", "otel_traces_sampler")
                if trace_sampler not in _KNOWN_SAMPLERS:
                    raise NipapConfigError(f"Unknown otel_traces_sampler '{trace_sampler}'. Valid samplers are: {_KNOWN_SAMPLERS}")
                sampler = _KNOWN_SAMPLERS[trace_sampler]

            if nipap_config.has_option("tracing", "otlp_grpc_endpoint"):
                nipap.tracing.init_tracing("nipap-www", nipap_config.get("tracing", "otlp_grpc_endpoint"), sampler)
            elif nipap_config.has_option("tracing", "otlp_http_endpoint"):
                nipap.tracing.init_tracing("nipap-www", nipap_config.get("tracing", "otlp_http_endpoint"), sampler, False)
            else:
                raise NipapConfigError("Tracing enabled but no OTLP endpoint configured")

            app.wsgi_app = OpenTelemetryMiddleware(app.wsgi_app)
        except KeyError:
            pass
        except ImportError:
            pass

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
