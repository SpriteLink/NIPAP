import logging
import json

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from napwww.lib.base import BaseController, render
from napwww.model.napmodel import Schema, Prefix

log = logging.getLogger(__name__)

class XhrController(BaseController):

    def index(self):
        # Return a rendered template
        #return render('/xhr.mako')
        # or, return a string
        return 'Hello World'



    def list_schema(self):
        """ List schemas and return JSON encoded result.
        """

        schemas = Schema.list()
        return json.dumps(schemas, cls=NapJSONEncoder)



    def list_prefix(self):
        """ List prefixes and return JSON encoded result.
        """

        prefixes = Prefix.list({'schema_id': 367, 'prefix': '1.3.0.0/16'})
        return json.dumps(prefixes, cls=NapJSONEncoder)



    def smart_search_prefix(self):
        """ Perform a smart search.     

            The smart search function tries extract a query from
            a text string. This query is then passed to the search_prefix
            function, which performs the search.
        """

        result = Prefix.smart_search(request.params['query_string'], {'id': int(request.params['schema'])})
        return json.dumps(result, cls=NapJSONEncoder)



class NapJSONEncoder(json.JSONEncoder):
    """ A class used to encode Nap objects to JSON.
    """

    def default(self, obj):

        if isinstance(obj, Schema):
            return {
                'id': obj.id,
                'name': obj.name,
                'description': obj.description
            }
        elif isinstance(obj, Prefix):
            return {
                'id': obj.id,
                'family': obj.family,
                'schema': obj.schema.id,
                'prefix': obj.prefix,
                'display_prefix': obj.display_prefix,
                'description': obj.description,
                'comment': obj.comment,
                'node': obj.node,
                'pool': obj.pool.id,
                'type': obj.type,
                'indent': obj.indent,
                'country': obj.country,
                'span_order': obj.span_order,
                'authoritative_source': obj.authoritative_source,
                'alarm_priority': obj.alarm_priority
            }
        else:
            return json.JSONEncoder.default(self, obj)
