import logging
try:
    import json
except ImportError:
    import simplejson as json

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from nipapwww.lib.base import BaseController, render
from pynipap import Schema, Prefix, Pool, NipapError

log = logging.getLogger(__name__)

class XhrController(BaseController):
    """ Interface to a few of the NIPAP API functions.

        TODO: verify that we have a schema id or name specified and
        fail gracefully if not.
    """

    @classmethod
    def extract_prefix_attr(cls, req):
        """ Extract prefix attributes from arbitary dict.
        """

        # TODO: add more?
        attr = {}
        if 'id' in request.params:
            attr['id'] = request.params['id']
        if 'prefix' in request.params:
            attr['prefix'] = request.params['prefix']
        if 'pool' in request.params:
            attr['pool'] = { 'id': request.params['pool'] }
        if 'node' in request.params:
            attr['node'] = request.params['node']
        if 'type' in request.params:
            attr['type'] = request.params['type']
        if 'country' in request.params:
            attr['country'] = request.params['country']

        return attr



    def index(self):
        # TODO: write a function which lists the available XHR functions?
        return 'Hello World'



    def list_schema(self):
        """ List schemas and return JSON encoded result.
        """

        try:
            schemas = Schema.list()
        except NipapError, e:
            return json.dumps({'error': 1, 'message': e.args, 'type': type(e).__name__})

        return json.dumps(schemas, cls=NipapJSONEncoder)



    def add_schema(self):
        """ Add a new schema to NIPAP and returns its data.
        """

        s = Schema()
        if 'name' in request.params:
            s.name = request.params['name']
        if 'description' in request.params:
            s.description = request.params['description']
        if 'vrf' in request.params:
            if request.params['vrf'].strip() == '':
                s.vrf = None
            else:
                s.vrf = request.params['vrf']

        try:
            s.save()
        except NipapError, e:
            return json.dumps({'error': 1, 'message': e.args, 'type': type(e).__name__})

        return json.dumps(s, cls=NipapJSONEncoder)



    def edit_schema(self, id):
        """ Edit a schema.
        """

        try:
            s = Schema.get(int(id))
        except NipapError, e:
            return json.dumps({'error': 1, 'message': e.args, 'type': type(e).__name__})

        if 'name' in request.params:
            s.name = request.params['name']
        if 'description' in request.params:
            s.description = request.params['description']
        if 'vrf' in request.params:
            if request.params['vrf'].strip() == '':
                s.vrf = None
            else:
                s.vrf = request.params['vrf']

        try:
            s.save()
        except NipapError, e:
            return json.dumps({'error': 1, 'message': e.args, 'type': type(e).__name__})

        return json.dumps(s, cls=NipapJSONEncoder)



    def list_pool(self):
        """ List pools and return JSON encoded result.
        """

        try:
            schema = Schema.get(int(request.params['schema']))
            pools = Pool.list(schema)
        except NipapError, e:
            return json.dumps({'error': 1, 'message': e.args, 'type': type(e).__name__})

        return json.dumps(pools, cls=NipapJSONEncoder)



    def smart_search_pool(self):
        """ Perform a smart pool search.

            The "smart" search function tries extract a query from
            a text string. This query is then passed to the search_pool
            function, which performs the search.
        """

        search_options = {}

        if 'query_id' in request.params:
            search_options['query_id'] = request.params['query_id']

        if 'max_result' in request.params:
            search_options['max_result'] = request.params['max_result']
        if 'offset' in request.params:
            search_options['offset'] = request.params['offset']

        try:
            schema = Schema.get(int(request.params['schema']))
            result = Pool.smart_search(schema,
                request.params['query_string'],
                search_options
                )
        except NipapError, e:
            return json.dumps({'error': 1, 'message': e.args, 'type': type(e).__name__})

        return json.dumps(result, cls=NipapJSONEncoder)



    def add_pool(self):
        """ Add a pool.
        """

        try:
            c.schema = Schema.get(int(request.params.get('schema')))
        except NipapError, e:
            return json.dumps({'error': 1, 'message': e.args, 'type': type(e).__name__})

        # extract attributes
        p = Pool()
        p.schema = c.schema
        p.name = request.params.get('name')
        p.description = request.params.get('description')
        p.default_type = request.params.get('default_type')
        if 'ipv4_default_prefix_length' in request.params:
            if request.params['ipv4_default_prefix_length'].strip() != '':
                p.ipv4_default_prefix_length = request.params['ipv4_default_prefix_length']
        if 'ipv6_default_prefix_length' in request.params:
            if request.params['ipv6_default_prefix_length'].strip() != '':
                p.ipv6_default_prefix_length = request.params['ipv6_default_prefix_length']

        try:
           p.save()
        except NipapError, e:
            return json.dumps({'error': 1, 'message': e.args, 'type': type(e).__name__})

        return json.dumps(p, cls=NipapJSONEncoder)



    def edit_pool(self, id):
        """ Edit a pool.
        """

        try:
            c.schema = Schema.get(int(request.params.get('schema')))
        except NipapError, e:
            return json.dumps({'error': 1, 'message': e.args, 'type': type(e).__name__})

        # extract attributes
        p = Pool.get(c.schema, int(id))
        if 'name' in request.params:
            p.name = request.params.get('name')
        if 'description' in request.params:
            p.description = request.params.get('description')
        if 'default_type' in request.params:
            p.default_type = request.params.get('default_type')
        if 'ipv4_default_prefix_length' in request.params:
            if request.params['ipv4_default_prefix_length'].strip() != '':
                p.ipv4_default_prefix_length = request.params['ipv4_default_prefix_length']
            else:
                p.ipv4_default_prefix_length = None
        if 'ipv6_default_prefix_length' in request.params:
            if request.params['ipv6_default_prefix_length'].strip() != '':
                p.ipv6_default_prefix_length = request.params['ipv6_default_prefix_length']
            else:
                p.ipv6_default_prefix_length = None

        try:
           p.save()
        except NipapError, e:
            return json.dumps({'error': 1, 'message': e.args, 'type': type(e).__name__})

        return json.dumps(p, cls=NipapJSONEncoder)



    def list_prefix(self):
        """ List prefixes and return JSON encoded result.
        """

        # fetch attributes from request.params
        attr = XhrController.extract_prefix_attr(request.params)

        try:
            schema = Schema.get(int(request.params['schema']))
            prefixes = Prefix.list(schema, attr)
        except NipapError, e:
            return json.dumps({'error': 1, 'message': e.args, 'type': type(e).__name__})

        return json.dumps(prefixes, cls=NipapJSONEncoder)



    def search_prefix(self):
        """ Search prefixes. Does not yet incorporate all the functions of the
            search_prefix API function due to difficulties with transferring
            a complete 'dict-to-sql' encoded data structure.

            Instead, a list of prefix attributes can be given which will be
            matched with the 'equals' operator if notheing else is specified. If
            multiple attributes are given, they will be combined with the 'and'
            operator. Currently, it is not possible to specify different
            operators for different attributes.
        """

        # extract operator
        if 'operator' in request.params:
            operator = request.params['operator']
        else:
            operator = 'equals'

        # fetch attributes from request.params
        attr = XhrController.extract_prefix_attr(request.params)

        # build query dict
        n = 0
        q = {}
        for key, val in attr.items():
            if n == 0:
                q = {
                    'operator': operator,
                    'val1': key,
                    'val2': val
                }
            else:
                q = {
                    'operator': 'and',
                    'val1': {
                        'operator': operator,
                        'val1': key,
                        'val2': val
                    },
                    'val2': q
                }
            n += 1

        # extract search options
        search_opts = {}
        if 'children_depth' in request.params:
            search_opts['children_depth'] = request.params['children_depth']
        if 'parents_depth' in request.params:
            search_opts['parents_depth'] = request.params['parents_depth']
        if 'max_result' in request.params:
            search_opts['max_result'] = request.params['max_result']
        if 'offset' in request.params:
            search_opts['offset'] = request.params['offset']

        try:
            schema = Schema.get(int(request.params['schema']))
            result = Prefix.search(schema, q, search_opts)
        except NipapError, e:
            return json.dumps({'error': 1, 'message': e.args, 'type': type(e).__name__})

        return json.dumps(result, cls=NipapJSONEncoder)



    def smart_search_prefix(self):
        """ Perform a smart search.

            The smart search function tries extract a query from
            a text string. This query is then passed to the search_prefix
            function, which performs the search.
        """

        search_options = {}

        if 'query_id' in request.params:
            search_options['query_id'] = request.params['query_id']

        if 'include_all_parents' in request.params:
            if request.params['include_all_parents'] == 'true':
                search_options['include_all_parents'] = True
            else:
                search_options['include_all_parents'] = False
                
        if 'include_all_children' in request.params:
            if request.params['include_all_children'] == 'true':
                search_options['include_all_children'] = True
            else:
                search_options['include_all_children'] = False

        if 'parents_depth' in request.params:
            search_options['parents_depth'] = request.params['parents_depth']
        if 'children_depth' in request.params:
            search_options['children_depth'] = request.params['children_depth']
        if 'max_result' in request.params:
            search_options['max_result'] = request.params['max_result']
        if 'offset' in request.params:
            search_options['offset'] = request.params['offset']

        try:
            schema = Schema.get(int(request.params['schema']))
            result = Prefix.smart_search(schema,
                request.params['query_string'],
                search_options
                )
        except NipapError, e:
            return json.dumps({'error': 1, 'message': e.args, 'type': type(e).__name__})

        return json.dumps(result, cls=NipapJSONEncoder)



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
            order_id        Order identifier
            vrf             VRF
            alarm_priority  Alarm priority of prefix
            monitor         If the prefix should be monitored or not

            from-prefix     A prefix the prefix is to be allocated from
            from-pool       A pool (ID) the prefix is to be allocated from
            prefix_length   Prefix length of allocated prefix
        """

        p = Prefix()

        # parameters which are "special cases"
        try:
            p.schema = Schema.get(int(request.params['schema']))
        except NipapError, e:
            return json.dumps({'error': 1, 'message': e.args, 'type': type(e).__name__})

        # standard parameters
        if 'description' in request.params:
            if request.params['description'].strip() == '':
                p.description = None
            else:
                p.description = request.params['description']

        if 'comment' in request.params:
            if request.params['comment'].strip() == '':
                p.comment = None
            else:
                p.comment = request.params['comment']

        if 'node' in request.params:
            if request.params['node'].strip() == '':
                p.node = None
            else:
                p.node = request.params['node']

        if 'type' in request.params:
            p.type = request.params['type']

        if 'pool' in request.params:
            if request.params['pool'].strip() == '':
                p.pool = None
            else:
                p.pool = Pool.get(p.schema, int(request.params['pool']))

        if 'country' in request.params:
            if request.params['country'].strip() == '':
                p.country = None
            else:
                p.country = request.params['country']

        if 'order_id' in request.params:
            if request.params['order_id'].strip() == '':
                p.order_id = None
            else:
                p.order_id = request.params['order_id']

        if 'vrf' in request.params:
            if request.params['vrf'].strip() == '':
                p.vrf = None
            else:
                p.vrf = request.params['vrf']

        if 'alarm_priority' in request.params:
            p.alarm_priority = request.params['alarm_priority']
        if 'monitor' in request.params:
            if request.params['monitor'] == 'true':
                p.monitor = True
            else:
                p.monitor = False

        # arguments
        args = {}
        if 'from_prefix[]' in request.params:
            args['from-prefix'] = request.params.getall('from_prefix[]')
        if 'from_pool' in request.params:
            try:
                args['from-pool'] = Pool.get(p.schema, int(request.params['from_pool']))
            except NipapError, e:
                return json.dumps({'error': 1, 'message': e.args, 'type': type(e).__name__})
        if 'family' in request.params:
            args['family'] = int(request.params['family'])
        if 'prefix_length' in request.params:
            args['prefix_length'] = int(request.params['prefix_length'])

        # manual allocation?
        if args == {}:
            if 'prefix' in request.params:
                p.prefix = request.params['prefix']

        try:
            p.save(args)
        except NipapError, e:
            return json.dumps({'error': 1, 'message': e.args, 'type': type(e).__name__})

        return json.dumps(p, cls=NipapJSONEncoder)



    def edit_prefix(self, id):
        """ Edit a prefix.
        """

        try:
            schema = Schema.get(int(request.params['schema']))

            p = Prefix.get(schema, int(id))

            # extract attributes
            if 'prefix' in request.params:
                p.prefix = request.params['prefix']

            if 'type' in request.params:
                p.type = request.params['type']

            if 'description' in request.params:
                p.description = request.params['description']

            if 'comment' in request.params:
                if request.params['comment'].strip() == '':
                    p.comment = None
                else:
                    p.comment = request.params['comment']

            if 'node' in request.params:
                if request.params['node'].strip() == '':
                    p.node = None
                else:
                    p.node = request.params['node']

            if 'pool' in request.params:
                if request.params['pool'].strip() == '':
                    p.pool = None
                else:
                    p.pool = Pool.get(schema, int(request.params['pool']))

            if 'alarm_priority' in request.params:
                p.alarm_priority = request.params['alarm_priority']

            if 'monitor' in request.params:
                if request.params['monitor'] == 'true':
                    p.monitor = True
                else:
                    p.monitor = False

            if 'country' in request.params:
                if request.params['country'].strip() == '':
                    p.country = None
                else:
                    p.country = request.params['country']

            if 'order_id' in request.params:
                if request.params['order_id'].strip() == '':
                    p.order_id = None
                else:
                    p.order_id = request.params['order_id']

            if 'vrf' in request.params:
                if request.params['vrf'].strip() == '':
                    p.vrf = None
                else:
                    p.vrf = request.params['vrf']

            p.save()

        except NipapError, e:
            return json.dumps({'error': 1, 'message': e.args, 'type': type(e).__name__})

        return json.dumps(p, cls=NipapJSONEncoder)



    def remove_prefix(self):
        """ Remove a prefix.
        """

        try:
            schema = Schema.get(int(request.params['schema']))
            p = Prefix.get(schema, int(request.params['id']))
            p.remove()

        except NipapError, e:
            return json.dumps({'error': 1, 'message': e.args, 'type': type(e).__name__})

        return json.dumps(p, cls=NipapJSONEncoder)



    def remove_schema(self):
        """ Remove a schema.
        """

        try:
            schema = Schema.get(int(request.params['id']))
            schema.remove()

        except NipapError, e:
            return json.dumps({'error': 1, 'message': e.args, 'type': type(e).__name__})

        return json.dumps(schema, cls=NipapJSONEncoder)




class NipapJSONEncoder(json.JSONEncoder):
    """ A class used to encode NIPAP objects to JSON.
    """

    def default(self, obj):

        if isinstance(obj, Schema):
            return {
                'id': obj.id,
                'name': obj.name,
                'description': obj.description,
                'vrf': obj.vrf
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
                'order_id': obj.order_id,
                'vrf': obj.vrf,
                'authoritative_source': obj.authoritative_source,
                'monitor': obj.monitor,
                'alarm_priority': obj.alarm_priority,
                'display': obj.display,
                'match': obj.match,
				'children': obj.children
            }
        else:
            return json.JSONEncoder.default(self, obj)
