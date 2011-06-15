import logging
import json

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from napwww.lib.base import BaseController, render
from napwww.model.napmodel import Schema, Prefix, Pool

log = logging.getLogger(__name__)

class XhrController(BaseController):
    """ Interface to a few of the Nap API functions.

        TODO: verify that we have a schema id or name specified and
        fail gracefully if not.
    """

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



    def list_pool(self):
        """ List pools and return JSON encoded result.
        """

        schema = Schema.get(int(request.params['schema_id']))
        pools = Pool.list(schema)
        return json.dumps(pools, cls=NapJSONEncoder)



    def list_prefix(self):
        """ List prefixes and return JSON encoded result.
        """

        schema = Schema.get(int(request.params['schema_id']))
        prefixes = Prefix.list(schema, { 'prefix': '1.3.0.0/16'})
        return json.dumps(prefixes, cls=NapJSONEncoder)



    def smart_search_prefix(self):
        """ Perform a smart search.

            The smart search function tries extract a query from
            a text string. This query is then passed to the search_prefix
            function, which performs the search.
        """

        log.debug("Smart search query: schema=%d q=%s search_opt_parent=%s search_opt_child=%s" %
            (int(request.params['schema']),
            request.params['query_string'],
            request.params['search_opt_parent'],
            request.params['search_opt_child'])
        )

        schema = Schema.get(int(request.params['schema']))

        result = Prefix.smart_search(schema,
            request.params['query_string'],
            request.params['search_opt_parent'],
            request.params['search_opt_child']
            )
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

        elif isinstance(obj, Pool):
            return {
                'id': obj.id,
                'name': obj.name,
                'schema': obj.schema.id,
                'description': obj.description,
                'default_type': obj.default_type,
                'ipv4_default_prefix_length': obj.ipv4_default_prefix_length,
                'ipv6_default_prefix_length': obj.ipv4_default_prefix_length
            }

        elif isinstance(obj, Prefix):

            if obj.pool is None:
                pool = None
            else:
                pool = obj.pool.id

            return {
                'id': obj.id,
                'family': obj.family,
                'schema': obj.schema.id,
                'prefix': obj.prefix,
                'display_prefix': obj.display_prefix,
                'description': obj.description,
                'comment': obj.comment,
                'node': obj.node,
                'pool': pool,
                'type': obj.type,
                'indent': obj.indent,
                'country': obj.country,
                'span_order': obj.span_order,
                'authoritative_source': obj.authoritative_source,
                'alarm_priority': obj.alarm_priority
            }
        else:
            return json.JSONEncoder.default(self, obj)
