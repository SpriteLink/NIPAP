import logging
import urllib
try:
    import json
except ImportError:
    import simplejson as json

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from nipapwww.lib.base import BaseController, render
from pynipap import Tag, VRF, Prefix, Pool, NipapError

log = logging.getLogger(__name__)



def validate_string(req, key):

    if isinstance(req[key], basestring) and req[key].strip() != '':
        return req[key].strip()
    else:
        return None


class XhrController(BaseController):
    """ Interface to a few of the NIPAP API functions.
    """

    @classmethod
    def extract_prefix_attr(cls, req):
        """ Extract prefix attributes from arbitary dict.
        """

        # TODO: add more?
        attr = {}
        if 'id' in req:
            attr['id'] = int(req['id'])
        if 'prefix' in req:
            attr['prefix'] = req['prefix']
        if 'pool' in req:
            attr['pool_id'] = int(req['pool'])
        if 'node' in req:
            attr['node'] = req['node']
        if 'type' in req:
            attr['type'] = req['type']
        if 'country' in req:
            attr['country'] = req['country']
        if 'indent' in req:
            attr['indent'] = req['indent']

        return attr



    @classmethod
    def extract_pool_attr(cls, req):
        """ Extract pool attributes from arbitary dict.
        """

        attr = {}
        if 'id' in req:
            attr['id'] = int(req['id'])
        if 'name' in req:
            attr['name'] = req['name']
        if 'description' in req:
            attr['description'] = req['description']
        if 'default_type' in req:
            attr['default_type'] = req['default_type']
        if 'ipv4_default_prefix_length' in req:
            attr['ipv4_default_prefix_length'] = int(req['ipv4_default_prefix_length'])
        if 'ipv6_default_prefix_length' in req:
            attr['ipv6_default_prefix_length'] = int(req['ipv6_default_prefix_length'])

        return attr



    def list_vrf(self):
        """ List VRFs and return JSON encoded result.
        """

        try:
            vrfs = VRF.list()
        except NipapError, e:
            return json.dumps({'error': 1, 'message': e.args, 'type': type(e).__name__})

        return json.dumps(vrfs, cls=NipapJSONEncoder)



    def smart_search_vrf(self):
        """ Perform a smart VRF search.

            The "smart" search function tries extract a query from
            a text string. This query is then passed to the search_vrf
            function, which performs the search.
        """

        search_options = {}
        extra_query = None

        if 'query_id' in request.json:
            search_options['query_id'] = request.json['query_id']

        if 'max_result' in request.json:
            search_options['max_result'] = request.json['max_result']

        if 'offset' in request.json:
            search_options['offset'] = request.json['offset']

        if 'vrf_id' in request.json:
            extra_query = {
                    'val1': 'id',
                    'operator': 'equals',
                    'val2': request.json['vrf_id']
                }

        try:
            result = VRF.smart_search(request.json['query_string'],
                search_options, extra_query
                )
            # Remove error key in result from backend as it interferes with the
            # error handling of the web interface.
            # TODO: Reevaluate how to deal with different types of errors; soft
            # errors like query string parser errors and hard errors like lost
            # database.
            del result['error']
        except NipapError, e:
            return json.dumps({'error': 1, 'message': e.args, 'type': type(e).__name__})

        return json.dumps(result, cls=NipapJSONEncoder)



    def add_vrf(self):
        """ Add a new VRF to NIPAP and return its data.
        """

        v = VRF()
        if 'rt' in request.json:
            v.rt = validate_string(request.json, 'rt')
        if 'name' in request.json:
            v.name = validate_string(request.json, 'name')
        if 'description' in request.json:
            v.description = validate_string(request.json, 'description')
        if 'tags' in request.json:
            v.tags = request.json['tags']
        if 'avps' in request.json:
            v.avps = request.json['avps']

        try:
            v.save()
        except NipapError, e:
            return json.dumps({'error': 1, 'message': e.args, 'type': type(e).__name__})

        return json.dumps(v, cls=NipapJSONEncoder)



    def edit_vrf(self, id):
        """ Edit a VRF.
        """

        try:
            v = VRF.get(int(id))
        except NipapError, e:
            return json.dumps({'error': 1, 'message': e.args, 'type': type(e).__name__})

        if 'rt' in request.json:
            v.rt = validate_string(request.json, 'rt')
        if 'name' in request.json:
            v.name = validate_string(request.json, 'name')
        if 'description' in request.json:
            v.description = validate_string(request.json, 'description')
        if 'tags' in request.json:
            v.tags = request.json['tags']
        if 'avps' in request.json:
            v.avps = request.json['avps']

        try:
            v.save()
        except NipapError, e:
            return json.dumps({'error': 1, 'message': e.args, 'type': type(e).__name__})

        return json.dumps(v, cls=NipapJSONEncoder)



    def remove_vrf(self, id):
        """ Remove a VRF.
        """

        try:
            vrf = VRF.get(int(id))
            vrf.remove()

        except NipapError, e:
            return json.dumps({'error': 1, 'message': e.args, 'type': type(e).__name__})

        return json.dumps(vrf, cls=NipapJSONEncoder)



    def list_pool(self):
        """ List pools and return JSON encoded result.
        """

        # fetch attributes from request.json
        attr = XhrController.extract_pool_attr(request.json)

        try:
            pools = Pool.list(attr)
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

        if 'query_id' in request.json:
            search_options['query_id'] = request.json['query_id']

        if 'max_result' in request.json:
            search_options['max_result'] = request.json['max_result']
        if 'offset' in request.json:
            search_options['offset'] = request.json['offset']

        try:
            result = Pool.smart_search(request.json['query_string'],
                search_options
                )
            # Remove error key in result from backend as it interferes with the
            # error handling of the web interface.
            # TODO: Reevaluate how to deal with different types of errors; soft
            # errors like query string parser errors and hard errors like lost
            # database.
            del result['error']
        except NipapError, e:
            return json.dumps({'error': 1, 'message': e.args, 'type': type(e).__name__})

        return json.dumps(result, cls=NipapJSONEncoder)



    def add_pool(self):
        """ Add a pool.
        """

        # extract attributes
        p = Pool()
        if 'name' in request.json:
            p.name = validate_string(request.json, 'name')
        if 'description' in request.json:
            p.description = validate_string(request.json, 'description')
        if 'default_type' in request.json:
            p.default_type = validate_string(request.json, 'default_type')
        # TODO: handle integers
        if 'ipv4_default_prefix_length' in request.json:
            p.ipv4_default_prefix_length = request.json['ipv4_default_prefix_length']
        if 'ipv6_default_prefix_length' in request.json:
            p.ipv6_default_prefix_length = request.json['ipv6_default_prefix_length']
        if 'tags' in request.json:
            p.tags = request.json['tags']
        if 'avps' in request.json:
            p.avps = request.json['avps']

        try:
           p.save()
        except NipapError, e:
            return json.dumps({'error': 1, 'message': e.args, 'type': type(e).__name__})

        return json.dumps(p, cls=NipapJSONEncoder)



    def edit_pool(self, id):
        """ Edit a pool.
        """

        # extract attributes
        p = Pool.get(int(id))
        if 'name' in request.json:
            p.name = validate_string(request.json, 'name')
        if 'description' in request.json:
            p.description = validate_string(request.json, 'description')
        if 'default_type' in request.json:
            p.default_type = validate_string(request.json, 'default_type')
        # TODO: handle integers
        if 'ipv4_default_prefix_length' in request.json:
            p.ipv4_default_prefix_length = request.json['ipv4_default_prefix_length']
        if 'ipv6_default_prefix_length' in request.json:
            p.ipv6_default_prefix_length = request.json['ipv6_default_prefix_length']
        if 'tags' in request.json:
            p.tags = request.json['tags']
        if 'avps' in request.json:
            p.avps = request.json['avps']

        try:
           p.save()
        except NipapError, e:
            return json.dumps({'error': 1, 'message': e.args, 'type': type(e).__name__})

        return json.dumps(p, cls=NipapJSONEncoder)



    def remove_pool(self, id):
        """ Remove a pool.
        """

        try:
            pool = Pool.get(int(id))
            pool.remove()

        except NipapError, e:
            return json.dumps({'error': 1, 'message': e.args, 'type': type(e).__name__})

        return json.dumps(pool, cls=NipapJSONEncoder)



    def list_prefix(self):
        """ List prefixes and return JSON encoded result.
        """

        # fetch attributes from request.json
        attr = XhrController.extract_prefix_attr(request.json)

        try:
            prefixes = Prefix.list(attr)
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
        if 'operator' in request.json:
            operator = request.json['operator']
        else:
            operator = 'equals'

        # fetch attributes from request.json
        attr = XhrController.extract_prefix_attr(request.json)

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
        if 'children_depth' in request.json:
            search_opts['children_depth'] = request.json['children_depth']
        if 'parents_depth' in request.json:
            search_opts['parents_depth'] = request.json['parents_depth']
        if 'include_neighbors' in request.json:
            search_opts['include_neighbors'] = request.json['include_neighbors']
        if 'max_result' in request.json:
            search_opts['max_result'] = request.json['max_result']
        if 'offset' in request.json:
            search_opts['offset'] = request.json['offset']

        try:
            result = Prefix.search(q, search_opts)
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
        extra_query = None
        vrf_filter = None

        if 'query_id' in request.json:
            search_options['query_id'] = request.json['query_id']

        if 'include_all_parents' in request.json:
            if request.json['include_all_parents'] == 'true':
                search_options['include_all_parents'] = True
            else:
                search_options['include_all_parents'] = False

        if 'include_all_children' in request.json:
            if request.json['include_all_children'] == 'true':
                search_options['include_all_children'] = True
            else:
                search_options['include_all_children'] = False

        if 'parents_depth' in request.json:
            search_options['parents_depth'] = request.json['parents_depth']
        if 'children_depth' in request.json:
            search_options['children_depth'] = request.json['children_depth']
        if 'include_neighbors' in request.json:
            if request.json['include_neighbors'] == 'true':
                search_options['include_neighbors'] = True
            else:
                search_options['include_neighbors'] = False
        if 'max_result' in request.json:
            if request.json['max_result'] == 'false':
                search_options['max_result'] = False
            else:
                search_options['max_result'] = request.json['max_result']
        if 'offset' in request.json:
            search_options['offset'] = request.json['offset']
        if 'parent_prefix' in request.json:
            search_options['parent_prefix'] = request.json['parent_prefix']
        if 'vrf_filter' in request.json:
            vrf_filter_parts = []

            # Fetch VRF IDs from search query and build extra query dict for
            # smart_search_prefix.
            vrfs = request.json['vrf_filter']

            if len(vrfs) > 0:
                vrf = vrfs[0]
                vrf_filter = {
                    'operator': 'equals',
                    'val1': 'vrf_id',
                    'val2': vrf if vrf != 'null' else None
                }

                for vrf in vrfs[1:]:
                    vrf_filter = {
                        'operator': 'or',
                        'val1': vrf_filter,
                        'val2': {
                            'operator': 'equals',
                            'val1': 'vrf_id',
                            'val2': vrf if vrf != 'null' else None
                        }
                    }

        if vrf_filter:
            extra_query = vrf_filter

        if 'indent' in request.json:
            if extra_query:
                extra_query = {
                        'operator': 'and',
                        'val1': extra_query,
                        'val2': {
                            'operator': 'equals',
                            'val1': 'indent',
                            'val2': request.json['indent']
                        }
                    }
            else:
                extra_query = {
                    'operator': 'equals',
                    'val1': 'indent',
                    'val2': request.json['indent']
                    }

        try:
            result = Prefix.smart_search(request.json['query_string'],
                search_options, extra_query)
            # Remove error key in result from backend as it interferes with the
            # error handling of the web interface.
            # TODO: Reevaluate how to deal with different types of errors; soft
            # errors like query string parser errors and hard errors like lost
            # database.
            del result['error']
        except NipapError, e:
            return json.dumps({'error': 1, 'message': e.args, 'type': type(e).__name__})

        return json.dumps(result, cls=NipapJSONEncoder)



    def add_prefix(self):
        """ Add prefix according to the specification.

            The following keys can be used:

            vrf             ID of VRF to place the prefix in
            prefix          the prefix to add if already known
            family          address family (4 or 6)
            description     A short description
            expires         Expiry time of assignment
            comment         Longer comment
            node            Hostname of node
            type            Type of prefix; reservation, assignment, host
            status          Status of prefix; assigned, reserved, quarantine
            pool            ID of pool
            country         Country where the prefix is used
            order_id        Order identifier
            customer_id     Customer identifier
            vlan            VLAN ID
            alarm_priority  Alarm priority of prefix
            monitor         If the prefix should be monitored or not

            from-prefix     A prefix the prefix is to be allocated from
            from-pool       A pool (ID) the prefix is to be allocated from
            prefix_length   Prefix length of allocated prefix
        """

        p = Prefix()

        # Sanitize input parameters
        if 'vrf' in request.json:
            try:
                if request.json['vrf'] is None or len(unicode(request.json['vrf'])) == 0:
                    p.vrf = None
                else:
                    p.vrf = VRF.get(int(request.json['vrf']))
            except ValueError:
                return json.dumps({'error': 1, 'message': "Invalid VRF ID '%s'" % request.json['vrf']})
            except NipapError, e:
                return json.dumps({'error': 1, 'message': e.args, 'type': type(e).__name__})

        if 'description' in request.json:
            p.description = validate_string(request.json, 'description')
        if 'expires' in request.json:
            p.expires = validate_string(request.json, 'expires')
        if 'comment' in request.json:
            p.comment = validate_string(request.json, 'comment')
        if 'node' in request.json:
            p.node = validate_string(request.json, 'node')
        if 'status' in request.json:
            p.status = validate_string(request.json, 'status')
        if 'type' in request.json:
            p.type = validate_string(request.json, 'type')

        if 'pool' in request.json:
            if request.json['pool'] is not None:
                try:
                    p.pool = Pool.get(int(request.json['pool']))
                except NipapError, e:
                    return json.dumps({'error': 1, 'message': e.args, 'type': type(e).__name__})

        if 'country' in request.json:
            p.country = validate_string(request.json, 'country')
        if 'order_id' in request.json:
            p.order_id = validate_string(request.json, 'order_id')
        if 'customer_id' in request.json:
            p.customer_id = validate_string(request.json, 'customer_id')
        if 'alarm_priority' in request.json:
            p.alarm_priority = validate_string(request.json, 'alarm_priority')
        if 'monitor' in request.json:
            if request.json['monitor'] == 'true':
                p.monitor = True
            else:
                p.monitor = False

        if 'vlan' in request.json:
            p.vlan = request.json['vlan']
        if 'tags' in request.json:
            p.tags = request.json['tags']
        if 'avps' in request.json:
            p.avps = request.json['avps']

        # arguments
        args = {}
        if 'from_prefix' in request.json:
            args['from-prefix'] = request.json['from_prefix']
        if 'from_pool' in request.json:
            try:
                args['from-pool'] = Pool.get(int(request.json['from_pool']))
            except NipapError, e:
                return json.dumps({'error': 1, 'message': e.args, 'type': type(e).__name__})
        if 'family' in request.json:
            args['family'] = request.json['family']
        if 'prefix_length' in request.json:
            args['prefix_length'] = request.json['prefix_length']

        # manual allocation?
        if args == {}:
            if 'prefix' in request.json:
                p.prefix = request.json['prefix']

        try:
            p.save(args)
        except NipapError, e:
            return json.dumps({'error': 1, 'message': e.args, 'type': type(e).__name__})

        return json.dumps(p, cls=NipapJSONEncoder)



    def edit_prefix(self, id):
        """ Edit a prefix.
        """

        try:
            p = Prefix.get(int(id))

            # extract attributes
            if 'prefix' in request.json:
                p.prefix = validate_string(request.json, 'prefix')
            if 'type' in request.json:
                p.type = validate_string(request.json, 'type')
            if 'description' in request.json:
                p.description = validate_string(request.json, 'description')
            if 'expires' in request.json:
                p.expires = validate_string(request.json, 'expires')
            if 'comment' in request.json:
                p.comment = validate_string(request.json, 'comment')
            if 'node' in request.json:
                p.node = validate_string(request.json, 'node')
            if 'status' in request.json:
                p.status = validate_string(request.json, 'status')

            if 'pool' in request.json:
                if request.json['pool'] is None:
                    p.pool = None
                else:
                    try:
                        p.pool = Pool.get(int(request.json['pool']))
                    except NipapError, e:
                        return json.dumps({'error': 1, 'message': e.args, 'type': type(e).__name__})

            if 'alarm_priority' in request.json:
                p.alarm_priority = validate_string(request.json, 'alarm_priority')
            if 'monitor' in request.json:
                if request.json['monitor'] == 'true':
                    p.monitor = True
                else:
                    p.monitor = False

            if 'country' in request.json:
                p.country = validate_string(request.json, 'country')
            if 'order_id' in request.json:
                p.order_id = validate_string(request.json, 'order_id')
            if 'customer_id' in request.json:
                p.customer_id = validate_string(request.json, 'customer_id')

            if 'vrf' in request.json:

                try:
                    if request.json['vrf'] is None or len(unicode(request.json['vrf'])) == 0:
                        p.vrf = None
                    else:
                        p.vrf = VRF.get(int(request.json['vrf']))
                except ValueError:
                    return json.dumps({'error': 1, 'message': "Invalid VRF ID '%s'" % request.json['vrf']})
                except NipapError, e:
                    return json.dumps({'error': 1, 'message': e.args, 'type': type(e).__name__})

            if 'vlan' in request.json:
                p.vlan = request.json['vlan']
            if 'tags' in request.json:
                p.tags = request.json['tags']
            if 'avps' in request.json:
                p.avps = request.json['avps']

            p.save()

        except NipapError, e:
            return json.dumps({'error': 1, 'message': e.args, 'type': type(e).__name__})

        return json.dumps(p, cls=NipapJSONEncoder)



    def remove_prefix(self, id):
        """ Remove a prefix.
        """

        try:
            p = Prefix.get(int(id))
            p.remove()

        except NipapError, e:
            return json.dumps({'error': 1, 'message': e.args, 'type': type(e).__name__})

        return json.dumps(p, cls=NipapJSONEncoder)



    def add_current_vrf(self):
        """ Add VRF to filter list session variable
        """

        vrf_id = request.json['vrf_id']

        if vrf_id is not None:

            if vrf_id == 'null':
                vrf = VRF()
            else:
                vrf_id = int(vrf_id)
                vrf = VRF.get(vrf_id)

            session['current_vrfs'][vrf_id] = { 'id': vrf.id, 'rt': vrf.rt,
                    'name': vrf.name, 'description': vrf.description }
            session.save()

        return json.dumps(session.get('current_vrfs', {}))


    def del_current_vrf(self):
        """ Remove VRF to filter list session variable
        """

        vrf_id = int(request.json['vrf_id'])
        if vrf_id in session['current_vrfs']:
            del session['current_vrfs'][vrf_id]

            session.save()

        return json.dumps(session.get('current_vrfs', {}))


    def get_current_vrfs(self):
        """ Return VRF filter list from session variable

            Before returning list, make a search for all VRFs currently in the
            list to verify that they still exist.
        """

        # Verify that all currently selected VRFs still exists
        cur_vrfs = session.get('current_vrfs', {}).items()
        if len(cur_vrfs) > 0:
            q = {
                'operator': 'equals',
                'val1': 'id',
                'val2': cur_vrfs[0][0]
            }

            if len(cur_vrfs) > 1:
                for vrf_id, vrf in cur_vrfs[1:]:
                    q = {
                        'operator': 'or',
                        'val1': q,
                        'val2': {
                            'operator': 'equals',
                            'val1': 'id',
                            'val2': vrf_id
                        }
                    }

            res = VRF.search(q)

            session['current_vrfs'] = {}
            for vrf in res['result']:
                session['current_vrfs'][vrf.id] = { 'id': vrf.id, 'rt': vrf.rt,
                    'name': vrf.name, 'description': vrf.description }

            session.save()

        return json.dumps(session.get('current_vrfs', {}))


    def list_tags(self):
        """ List Tags and return JSON encoded result.
        """

        try:
            tags = Tags.list()
        except NipapError, e:
            return json.dumps({'error': 1, 'message': e.args, 'type': type(e).__name__})

        return json.dumps(tags, cls=NipapJSONEncoder)



class NipapJSONEncoder(json.JSONEncoder):
    """ A class used to encode NIPAP objects to JSON.
    """

    def default(self, obj):

        if isinstance(obj, Tag):
            return {
                'name': obj.name
            }

        elif isinstance(obj, VRF):
            return {
                'id': obj.id,
                'rt': obj.rt,
                'name': obj.name,
                'description': obj.description,
                'tags': obj.tags,
                'num_prefixes_v4': obj.num_prefixes_v4,
                'num_prefixes_v6': obj.num_prefixes_v6,
                'total_addresses_v4': obj.total_addresses_v4,
                'total_addresses_v6': obj.total_addresses_v6,
                'used_addresses_v4': obj.used_addresses_v4,
                'used_addresses_v6': obj.used_addresses_v6,
                'free_addresses_v4': obj.free_addresses_v4,
                'free_addresses_v6': obj.free_addresses_v6,
                'avps': obj.avps
            }

        elif isinstance(obj, Pool):

            if obj.vrf is None:
                vrf_id = None
                vrf_rt = None
            else:
                vrf_id = obj.vrf.id
                vrf_rt = obj.vrf.rt

            return {
                'id': obj.id,
                'name': obj.name,
                'vrf_rt': vrf_rt,
                'vrf_id': vrf_id,
                'description': obj.description,
                'default_type': obj.default_type,
                'ipv4_default_prefix_length': obj.ipv4_default_prefix_length,
                'ipv6_default_prefix_length': obj.ipv6_default_prefix_length,
                'tags': obj.tags,
                'member_prefixes_v4': obj.member_prefixes_v4,
                'member_prefixes_v6': obj.member_prefixes_v6,
                'used_prefixes_v4': obj.used_prefixes_v4,
                'used_prefixes_v6': obj.used_prefixes_v6,
                'free_prefixes_v4': obj.free_prefixes_v4,
                'free_prefixes_v6': obj.free_prefixes_v6,
                'total_prefixes_v4': obj.total_prefixes_v4,
                'total_prefixes_v6': obj.total_prefixes_v6,
                'total_addresses_v4': obj.total_addresses_v4,
                'total_addresses_v6': obj.total_addresses_v6,
                'used_addresses_v4': obj.used_addresses_v4,
                'used_addresses_v6': obj.used_addresses_v6,
                'free_addresses_v4': obj.free_addresses_v4,
                'free_addresses_v6': obj.free_addresses_v6,
                'avps': obj.avps
            }

        elif isinstance(obj, Prefix):

            if obj.pool is None:
                pool = None
            else:
                pool = obj.pool.id

            vrf_id = obj.vrf.id
            vrf_rt = obj.vrf.rt
            expires = None
            if obj.expires is not None:
                expires = str(obj.expires)

            return {
                'id': obj.id,
                'family': obj.family,
                'vrf_rt': vrf_rt,
                'vrf_id': vrf_id,
                'prefix': obj.prefix,
                'display_prefix': obj.display_prefix,
                'status': obj.status,
                'description': obj.description,
                'expires': expires,
                'comment': obj.comment,
                'inherited_tags': obj.inherited_tags,
                'tags': obj.tags,
                'node': obj.node,
                'pool_id': pool,
                'type': obj.type,
                'indent': obj.indent,
                'country': obj.country,
                'order_id': obj.order_id,
                'customer_id': obj.customer_id,
                'authoritative_source': obj.authoritative_source,
                'monitor': obj.monitor,
                'alarm_priority': obj.alarm_priority,
                'display': obj.display,
                'match': obj.match,
                'children': obj.children,
                'vlan': obj.vlan,
                'total_addresses': obj.total_addresses,
                'used_addresses': obj.used_addresses,
                'free_addresses': obj.free_addresses,
                'avps': obj.avps
            }
        else:
            return json.JSONEncoder.default(self, obj)
