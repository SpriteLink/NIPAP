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



    def add_prefix(self):
        """ Add prefix according to the specification.

            The following keys can be used:

            schema          Schema to which the prefix is to be added (mandatory)
            prefix          the prefix to add if already known
            family          address family (4 or 6)
            description     A short description
            comment         Longer comment
            node            Hostname of node 
            type            Type of prefix; reservation, assignment, host
            pool            ID of pool
            country         Country where the prefix is used
            span_order      SPAN order number
            alarm_priority  Alarm priority of prefix

            from-prefix     A prefix the prefix is to be allocated from
            from-pool       A pool (ID) the prefix is to be allocated from
            prefix_length   Prefix length of allocated prefix
        """

        p = Prefix()

        # parameters which are "special cases"
        p.schema = Schema.get(request.params['schema'])
        if 'pool' in request.params:
            p.pool = Pool.get(request.params['pool'])
        else:
            p.pool = None

        # standard parameters
        if 'family' in request.params:
            p.family = request.params['family']
        if 'description' in request.params:
            p.description = request.params['description']
        if 'comment' in request.params:
            p.comment = request.params['comment']
        if 'node' in request.params:
            p.node = request.params['node']
        if 'type' in request.params:
            p.type = request.params['type']
        if 'country' in request.params:
            p.country = request.params['country']
        if 'span_order' in request.params:
            p.span_order = request.params['span_order']
        if 'alarm_priority' in request.params:
            p.alarm_priority = request.params['alarm_priority']

        # arguments
        args = {}
        if 'from-prefix' in request.params:
            args['from-prefix'] = request.params['from-prefix']
        if 'from-pool' in request.params:
            args['from-pool'] = Pool.get(request.params['from-pool'])
        if 'prefix_length' in request.params:
            args['prefix_length'] = request.params['prefix_length']

        p.save(args)

        return json.dumps(p, cls=NapJSONEncoder)



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
                'ipv6_default_prefix_length': obj.ipv6_default_prefix_length
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
