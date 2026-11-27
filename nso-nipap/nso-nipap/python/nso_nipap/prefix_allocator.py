import logging

import ncs
import ncs.maapi as maapi
import ncs.maagic as maagic

log = logging.getLogger()


def prefix_request(service, svc_xpath, pool_name, allocation_name,
        prefix_length, family=4, prefix_attributes=None):
    """ Create a prefix allocation request

        Arguments:
        service -- the requesting service node
        svc_xpath -- xpath to the requesting service
        pool_name -- name of pool to request from
        allocation_name -- unique allocation name
        prefix_length -- the prefix length of the allocated network
        family -- address family of the network, 4 (IPv4) or 6 (IPv6)
        prefix_attributes -- dict with prefix attributes
    """

    if prefix_attributes is None:
        prefix_attributes = {}

    template = ncs.template.Template(service)
    vars = ncs.template.Variables()

    # required variables
    vars.add("POOL_NAME", pool_name)
    vars.add("ALLOCATION_NAME", allocation_name)
    vars.add("SERVICE", svc_xpath)
    vars.add("PREFIX_LENGTH", prefix_length)
    vars.add("FAMILY", family)

    # optional prefix attributes
    _set_prefix_attributes(prefix_attributes, vars)

    log.debug("Placing prefix request with data %s" % vars)

    template.apply('nso-nipap-prefix-request', vars)


def from_prefix_request(service, pool_name, main_allocation_name,
        from_pref_allocation_name, prefix_attributes=None):
    """ Create a from-prefix allocation request

        Arguments:
        service -- the requesting service node
        pool_name -- name of pool to request from
        main_allocation_name -- name of main allocation which the from-prefix is appended to
        from_pref_allocation_name -- name of from-prefix allocation
        prefix_attributes -- dict with prefix attributes
    """

    if prefix_attributes is None:
        prefix_attributes = {}

    template = ncs.template.Template(service)
    vars = ncs.template.Variables()

    # required variables
    vars.add('POOL_NAME', pool_name)
    vars.add('ALLOCATION_NAME', main_allocation_name)
    vars.add('FROM_PREFIX_ALLOCATION_NAME', from_pref_allocation_name)

    # optional prefix attributes
    _set_prefix_attributes(prefix_attributes, vars)

    log.debug("Placing from-prefix request with data %s" % vars)

    template.apply('nso-nipap-from-prefix-request', vars)


def prefix_read(root, pool_name, allocation_name):
    """Returns the allocated network or None

        Arguments:
        root -- a maagic root for the current transaction
        pool_name -- name of pool to request from
        allocation_name -- unique allocation name
    """
    # Look in the current transaction
    _verify_allocation(root, pool_name, allocation_name)

    # Now we switch from the current trans to actually see if
    # we have received the alloc
    with maapi.single_read_trans("admin", "system",
                                 db=ncs.OPERATIONAL) as th:

        oper_root = maagic.get_root(th)
        alloc = _get_allocation(oper_root, pool_name, allocation_name)
        if alloc is None:
            return None

        if alloc.response.prefix:
            return alloc.response.prefix
        else:
            return None


def from_prefix_read(root, pool_name, main_allocation_name, from_prefix_allocation_name):
    """Returns the allocated network or None

        Arguments:
        root -- a maagic root for the current transaction
        pool_name -- name of pool to request from
        main_allocation_name -- name of allocation which the from-prefix allocation belongs to
        from_prefix_allocation_name -- name of from-prefix allocation
    """
    # Look in the current transaction
    alloc = _verify_allocation(root, pool_name, main_allocation_name)
    if from_prefix_allocation_name not in alloc.from_prefix_request:
        raise LookupError("from-prefix allocation %s does not exist in main allocation %s from pool %s" %
                          (from_prefix_allocation_name, main_allocation_name, pool_name))

    # Now we switch from the current trans to actually see if
    # we have received the alloc
    with maapi.single_read_trans("admin", "system",
                                 db=ncs.OPERATIONAL) as th:
        oper_root = maagic.get_root(th)
        alloc = _get_allocation(oper_root, pool_name, main_allocation_name)
        if alloc is None:
            return None

        if from_prefix_allocation_name not in alloc.from_prefix_request:
            return None

        from_pref_alloc = alloc.from_prefix_request[from_prefix_allocation_name]

        if from_pref_alloc.response.prefix:
            return from_pref_alloc.response.prefix
        else:
            return None


def _set_prefix_attributes(attributes, template_vars):
    """ Fetch prefix attributes from CDB and write to template vars
    """

    template_vars.add('CUSTOMER_ID',
        attributes['customer_id'] if 'customer_id' in attributes else '-1')

    template_vars.add('DESCRIPTION',
        attributes['description'] if 'description' in attributes else '-1')

    template_vars.add('NODE',
        attributes['node'] if 'node' in attributes else '-1')

    template_vars.add('ORDER_ID',
        attributes['order_id'] if 'order_id' in attributes else '-1')


def _verify_allocation(root, pool_name, allocation_name):
    """ Verify that the allocation exists and return it

        Throws LookupError if allocation is missing.
    """
    pool_l = root.ncs__services.nipap__nipap.from_pool

    if pool_name not in pool_l:
        raise LookupError("Pool %s does not exist" % (pool_name))

    pool = pool_l[pool_name]

    if allocation_name not in pool.request:
        raise LookupError("allocation %s does not exist in pool %s" %
                          (allocation_name, pool_name))

    return pool.request[allocation_name]


def _get_allocation(root, pool_name, allocation_name):
    """ Return allocation.

        Returns None if allocation does not exist, raises exception if
        allocation status == 'error'.
    """
    alloc = None
    try:
        alloc = _verify_allocation(root, pool_name, allocation_name)
    except LookupError as e:
        return None

    if alloc.response.status == 'ok':
        return alloc
    elif alloc.response.status == 'error':
        raise AllocationError(alloc.response.status_message)


class AllocationError(Exception):
    """ Exception thrown when allocation has failed.
    """
    pass
