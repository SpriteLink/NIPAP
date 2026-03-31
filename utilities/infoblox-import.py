from pyinfoblox import InfobloxWAPI
import pynipap
from pynipap import Prefix, VRF
from pynipap import AuthOptions
import ipaddr

# the v1.4 is the minimum requirement
infoblox = InfobloxWAPI(username='dev',
                        password='passwd',
                        wapi='https://infoblox.example.com/wapi/v1.4/')

pynipap.xmlrpc_uri = 'http://dev:testing@localhost:1337'
o = AuthOptions({
    'authoritative_source': 'nipap'
})

# set to a string if you want the customerid populated
DEFAULT_CUSTOMER = None

# set this to true if any of the network blocks
# are unclean and are really assignments or hosts.
# use with caution.
detect_hosts = False

# this is for network blocks that are misrepresented
# it might not be needed for your network
hosts = []

for vrf in VRF.list():
    if vrf.id == 0:
        DEFAULT_VRF = vrf
        break
else:
    raise ValueError("No default VRF")


def export_tags(obj):
    def f():
        for name, attr in obj['extattrs'].items():
            # skip inherited attributes
            if attr.get('inheritance_source'):
                continue
            yield name, attr['value']
    return dict(f())


def new_prefix():
    p = Prefix()
    p.monitor = True
    p.alarm_priority = 'high'
    p.vrf = DEFAULT_VRF
    p.node = None
    p.tags['infoblox-import'] = 1
    p.customer_id = DEFAULT_CUSTOMER
    p.authoritative_source = 'import'

    # https://github.com/SpriteLink/NIPAP/issues/721
    p.expires = '2100-01-30 00:00:00'
    return p


def save_hosts():
    for host in hosts:
        try:
            host.save()
            continue
        except:
            pass

        r = Prefix().search({
            'operator': 'contains',
            'val1': 'prefix',
            'val2': host.prefix
        })
        for p in r['result']:
            try:
                p.type = 'assignment'
                p.tags['guessed'] = 1
                p.save()
            except:
                pass

        try:
            host.save()
            continue
        except:
            pass

        # this is a last and probably wrong attempt
        # to fix the bad data in infoblox.
        p = Prefix()
        p.type = 'assignment'
        p.description = 'AUTO: host container (import)'
        p.tags['auto'] = 1
        ip = ipaddr.IPNetwork(host.prefix)
        p.prefix = str(ip.supernet(prefixlen_diff=1).network) + '/127'
        p.save()
        host.save()


def save_block(block):
    tags = export_tags(block)
    ipnet = ipaddr.IPNetwork(block['network'])
    p = new_prefix()
    p.prefix = block['network']
    p.type = 'assignment'
    p.comment = str(tags)
    p.description = block.get('comment')

    if ipnet.version == 6:
        if ipnet.prefixlen == 128:
            p.type = 'host'
            p.tags['networkashost'] = 1
            hosts.append(p)
            return

    try:
        p.save()
    except Exception as exc:
        print '---==== ERROR ====---'
        print '!!! ', exc
        print '~~~ ', block


def save_root_network(block):
    tags = export_tags(block)
    ipnet = ipaddr.IPNetwork(block['network'])

    p = new_prefix()
    p.prefix = block['network']
    p.type = 'reservation'
    p.comment = str(tags)
    p.description = block.get('comment')

    if ipnet.version == 6:
        if ipnet.prefixlen >= 126:
            p.type = 'assignment'
            p.tags['prefixlenmax'] = 1
        elif 'oopback' in p.description:
            p.type = 'assignment'
            p.tags['loopback'] = 1

    try:
        p.save()
    except Exception as exc:
        print '---==== ERROR ====---'
        print '!!! ', exc
        print '??? ', p.type
        print '~~~ ', block


def assignedblocks():
    for d in ['network', 'ipv6network']:
        for netblock in getattr(infoblox, d).get(
                network_view='default',
                _max_results=10000,
                _return_fields=','.join(['extattrs', 'comment', 'network', ])):
            yield netblock


def superblocks():
    for d in ['networkcontainer', 'ipv6networkcontainer']:
        for netblock in getattr(infoblox, d).get(
                network_view='default',
                _max_results=10000,
                _return_fields=','.join(['extattrs', 'comment', 'network', ])):
            yield netblock


if __name__ == '__main__':
    for net in superblocks():
        save_root_network(net)

    for net in assignedblocks():
        save_block(net)

    if detect_hosts:
        save_hosts()
    else:
        for host in hosts:
            print "Failed to save ", host
