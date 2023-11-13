try:
    import inspect
    from functools import wraps

    from flask import request

    from opentelemetry import trace, context
    from opentelemetry.trace import SpanKind, StatusCode
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from requests import post

    tracer = trace.get_tracer("nipap")

    def init_tracing(service_name, endpoint):
        resource = Resource(attributes={
            SERVICE_NAME: service_name
        })

        provider = TracerProvider(resource=resource)
        processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint))
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)


    def setup(app, endpoint):
        @app.route('/v1/traces/', defaults={'path': ''}, methods=["POST"])
        def proxy(path):
            return post(f'{endpoint}{path}', data=request.data, headers=request.headers).content


    def create_span(f):
        """ Class decorator creating a opentelemetry span
        """

        @wraps(f)
        def decorated(*args, **kwargs):
            """
            """

            auth = args[1]
            signature = inspect.signature(f)
            with tracer.start_as_current_span(args[0].__class__.__name__ + " " + f.__name__, context.get_current(),
                                              SpanKind.CLIENT):
                index = 0
                span = trace.get_current_span()
                for parameter in signature.parameters:
                    if index > 1:
                        try:
                            span.set_attribute("argument." + parameter, str(args[index]))
                        except IndexError:
                            break
                    index += 1
                try:
                    span.set_attribute("username", auth.username)
                    if auth.full_name is not None:
                        span.set_attribute("full_name", auth.full_name)
                    span.set_attribute("authoritative_source", auth.authoritative_source)
                    span.set_attribute("authenticated_as", auth.authenticated_as)
                except:
                    pass
                return f(*args, **kwargs)

        return decorated

    def create_span_rest(f):
        """ Class decorator creating a opentelemetry span
        """

        @wraps(f)
        def decorated(*args, **kwargs):
            """
            """

            with tracer.start_as_current_span(args[0].__class__.__name__ + " " + f.__name__, context.get_current(),
                                              SpanKind.CLIENT):
                span = trace.get_current_span()
                try:
                    auth = args[1]["auth"]
                    span.set_attribute("username", auth.username)
                    span.set_attribute("full_name", auth.full_name)
                    span.set_attribute("authoritative_source", auth.authoritative_source)
                    span.set_attribute("authenticated_as", auth.authenticated_as)
                except KeyError:
                    pass

                try:
                    prefix = args[1]["prefix"]
                    span.set_attribute("prefix", str(prefix))
                except KeyError:
                    pass

                try:
                    attr = args[1]["attr"]
                    span.set_attribute("attr", str(attr))
                except KeyError:
                    pass

                return f(*args, **kwargs)
        return decorated

    def create_span_authenticate(f):
        """ Class decorator creating a opentelemetry span
        """

        @wraps(f)
        def decorated(*args, **kwargs):
            """
            """

            result = f(*args, **kwargs)

            span = trace.get_current_span()

            span.set_attribute("auth_backend", args[0].auth_backend)
            if args[0].username is not None:
                span.set_attribute("username", args[0].username)
            if args[0].authenticated_as is not None:
                span.set_attribute("authenticated_as", args[0].authenticated_as)
            if args[0].full_name is not None:
                span.set_attribute("full_name", args[0].full_name)
            if args[0].authoritative_source is not None:
                span.set_attribute("authoritative_source", args[0].authoritative_source)

            if result:
                span.set_status(StatusCode.OK)
            else:
                span.set_status(StatusCode.ERROR)

            return result

        return decorated


except ImportError:
    def create_span(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            return f(*args, **kwargs)
        return decorated

    def create_span_rest(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            return f(*args, **kwargs)
        return decorated

    def create_span_authenticate(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            return f(*args, **kwargs)
        return decorated