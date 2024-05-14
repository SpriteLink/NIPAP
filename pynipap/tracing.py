import inspect
import sys
from functools import wraps

if sys.version_info[0] < 3:
    import xmlrpclib

    int = long
else:
    import xmlrpc.client as xmlrpclib

try:
    from opentelemetry import trace, context
    from opentelemetry.trace import SpanKind, INVALID_SPAN
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.trace.sampling import DEFAULT_ON
    import opentelemetry.exporter.otlp.proto.http.trace_exporter

    tracer = trace.get_tracer("pynipap")


    def init_tracing(service_name, endpoint, sampler, use_grpc=True):
        resource = Resource(attributes={
            SERVICE_NAME: service_name
        })

        if sampler is None:
            sampler = DEFAULT_ON

        provider = TracerProvider(sampler=sampler, resource=resource)
        if use_grpc:
            processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint))
        else:
            processor = BatchSpanProcessor(
                opentelemetry.exporter.otlp.proto.http.trace_exporter.OTLPSpanExporter(endpoint=endpoint))
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)


    def create_span(f):
        """ Class decorator creating a opentelemetry span
        """

        @wraps(f)
        def decorated(*args, **kwargs):
            """
            """

            from pynipap import AuthOptions
            signature = inspect.signature(f)

            if args[0].__class__ == type:
                span_name = args[0].__name__ + " " + f.__name__
            else:
                span_name = str(args[0].__class__.__name__) + " " + f.__name__

            with tracer.start_as_current_span(span_name,
                                              context.get_current(),
                                              SpanKind.CLIENT):
                index = 0
                span = trace.get_current_span()
                for parameter in signature.parameters:
                    if index > 0:
                        try:
                            span.set_attribute("argument." + parameter, str(args[index]))
                        except IndexError:
                            break
                    index += 1
                try:
                    span.set_attribute("username", AuthOptions().options['username'])
                    span.set_attribute("authoritative_source", AuthOptions().options['authoritative_source'])
                except BaseException:
                    pass
                return f(*args, **kwargs)

        return decorated


    class TracingXMLTransport(xmlrpclib.Transport):

        def __init__(self, use_datetime=False, use_builtin_types=False,
                     *, headers=()):
            super().__init__(use_datetime=use_datetime,
                             use_builtin_types=use_builtin_types,
                             headers=headers)

        def request(self, host, handler, request_body, verbose=False):
            with tracer.start_as_current_span("POST XML request", context.get_current(), SpanKind.CLIENT):
                current_span = trace.get_current_span()
                try:
                    result = super().request(host, handler, request_body, verbose)
                    current_span.set_attribute("http.status_code", 200)
                except xmlrpclib.ProtocolError as protocolError:
                    current_span.set_attribute("http.status_code", protocolError.errcode)
                    current_span.record_exception(protocolError)
                    raise protocolError
            return result

        def send_content(self, connection, request_body):
            current_span = trace.get_current_span()
            if current_span != INVALID_SPAN:
                current_span.set_attribute("net.peer.ip", connection.host)
                current_span.set_attribute("net.peer.port", connection.port)
                current_span.set_attribute("net.peer.transport", "ip_tcp")
                connection.putheader("traceparent",
                                     "00-" + hex(current_span.get_span_context().trace_id)[2:].zfill(32) + "-" + hex(
                                         current_span.get_span_context().span_id)[2:].zfill(16) + "-0" + ("1" if current_span.is_recording() else "0"))

            super().send_content(connection, request_body)


    class TracingXMLSafeTransport(xmlrpclib.SafeTransport):

        def __init__(self, use_datetime=False, use_builtin_types=False,
                     *, headers=(), context=None):
            super().__init__(use_datetime=use_datetime,
                             use_builtin_types=use_builtin_types,
                             headers=headers, context=context)

        def request(self, host, handler, request_body, verbose=False):
            with tracer.start_as_current_span("POST XML request", context.get_current(), SpanKind.CLIENT):
                current_span = trace.get_current_span()
                try:
                    result = super().request(host, handler, request_body, verbose)
                    current_span.set_attribute("http.status_code", 200)
                except xmlrpclib.ProtocolError as protocolError:
                    current_span.set_attribute("http.status_code", protocolError.errcode)
                    current_span.record_exception(protocolError)
                    raise protocolError
            return result

        def send_content(self, connection, request_body):
            current_span = trace.get_current_span()
            if current_span != INVALID_SPAN:
                current_span.set_attribute("net.peer.ip", connection.host)
                current_span.set_attribute("net.peer.port", connection.port)
                current_span.set_attribute("net.peer.transport", "ip_tcp")
                connection.putheader("traceparent",
                                     "00-" + hex(current_span.get_span_context().trace_id)[2:].zfill(32) + "-" + hex(
                                         current_span.get_span_context().span_id)[2:].zfill(16) + "-0" + ("1" if current_span.is_recording() else "0"))

            super().send_content(connection, request_body)

except ImportError:
    def create_span(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            return f(*args, **kwargs)

        return decorated
