import functools

from flask import session

try:
    from opentelemetry import trace
    from opentelemetry.trace import INVALID_SPAN

    def create_span(view):
        @functools.wraps(view)
        def wrapped_view(**kwargs):
            current_span = trace.get_current_span()
            if current_span != INVALID_SPAN:
                if session.get("user") is None:
                    current_span.set_attribute("username", "unknown")
                else:
                    current_span.set_attribute("username", session.get("user"))
            return view(**kwargs)

        return wrapped_view
except ImportError:
   def create_span(view):
        @functools.wraps(view)
        def wrapped_view(**kwargs):
            return view(**kwargs)

        return wrapped_view
