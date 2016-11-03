#!/usr/bin/env python3
""" NIPAP import script for ipplan data.

This script uses the standard export files base.txt and ipaddr.txt from ipplan.

base.txt format:
ip\t description\t netmask\t comment

ipaddr.txt format:
ip\t user\t location\t description\t hostname\t phone\t comment
"""
import configparser
import os
# use local pynipap, useful if we are developing
import sys
sys.path.append('../pynipap')
import pynipap
import csv
import ipaddress


def add_ip_to_net(networks, host):
    """ Add hosts from ipplan to networks object. """
    for network in networks:
        if host['ipaddr'] in network['network']:
            network['hosts'].append(host)
            return


def get_networks(base_file, ipaddr_file):
    """ Gather network and host information from ipplan export files. """
    networks = []

    base = open(base_file, 'r')

    csv_reader = csv.reader(base, delimiter='\t')

    buffer = ""
    for row in csv_reader:

        # Fixes quotation bug in ipplan exporter for networks
        if len(networks) > 0 and len(buffer) > 0:
            networks[-1]['comment'] += " ".join(buffer)
            buffer = ""
        if len(row) < 3:
            buffer = row
        else:

            network = {
                'network': ipaddress.ip_network("{}/{}".format(row[0], row[2])),
                'description': row[1],
                'hosts': [],
                'comment': ""
            }

            if len(row) > 3:
                network['additional'] = " ".join(row[3:])

            networks.append(network)

    base.close()

    ipaddr = open(ipaddr_file, 'r')

    csv_reader = csv.reader(ipaddr, delimiter='\t')
    for row in csv_reader:

        host = {
            'ipaddr': ipaddress.ip_address(row[0]),
            'user': row[1],
            'location': row[2],
            'description': row[3],
            'fqdn': row[4],
            'phone': row[5],
            'mac': row[6]
        }

        if len(row) > 7:
            host['additional'] = " ".join(row[7:])

        add_ip_to_net(networks, host)

    ipaddr.close()

    return networks


def new_prefix():
    """ Create new prefix object with general settings. """
    p = pynipap.Prefix()
    p.authorative_source = "nipap"
    return p


def add_prefix(network):
    """ Put your network information in the prefix object. """
    p = new_prefix()
    p.prefix = str(network['network'])
    p.type = "assignment"
    p.description = network['description']
    p.tags = ['ipplan-import']
    p.comment = ""

    if 'additional' in network:
        p.comment += network['additional']
    if len(network['comment']) > 0:
        p.comment += network['comment']
    return p


def add_host(host):
    """ Put your host information in the prefix object. """
    p = new_prefix()
    p.prefix = str(host['ipaddr'])
    p.type = "host"
    p.description = host['description']
    p.node = host['fqdn']
    p.avps = {}

    # Use remaining data from ipplan to populate comment field.
    if 'additional' in host:
        p.comment = host['additional']

    # Use specific info to create extra attributes.
    if len(host['location']) > 0:
        p.avps['location'] = host['location']

    if len(host['mac']) > 0:
        p.avps['mac'] = host['mac']

    if len(host['phone']) > 0:
        p.avps['phone'] = host['phone']

    if len(host['user']) > 0:
        p.avps['user'] = host['user']

    return p


if __name__ == '__main__':
    # read configuration
    cfg = configparser.ConfigParser()
    cfg.read(os.path.expanduser('~/.nipaprc'))

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', help="NIPAP backend username")
    parser.add_argument('--password', help="NIPAP backend password")
    parser.add_argument('--host', help="NIPAP backend host")
    parser.add_argument('--port', help="NIPAP backend port")
    ipplan = parser.add_argument_group()
    ipplan.add_argument('--base-file', help="Path to ipplan base csv file",
                        required=True)
    ipplan.add_argument('--ipaddr-file', help="Path to ipplan ipaddr csv file",
                        required=True)
    ipplan.add_argument('--logfile', help="Path to import error log",
                        default="/tmp/ipplan-import-errors.log")
    args = parser.parse_args()

    auth_uri = "%s:%s@" % (args.username or cfg.get('global', 'username'),
                           args.password or cfg.get('global', 'password'))

    xmlrpc_uri = "http://%(auth_uri)s%(host)s:%(port)s" % {
        'auth_uri': auth_uri,
        'host': args.host or cfg.get('global', 'hostname'),
        'port': args.port or cfg.get('global', 'port')
        }
    pynipap.AuthOptions({'authoritative_source': 'nipap'})
    pynipap.xmlrpc_uri = xmlrpc_uri

    networks = get_networks(args.base_file, args.ipaddr_file)

    # Collect all prefixes and hosts that couldn't be saved to NIPAP.
    log = open(args.logfile, 'a')

    for network in networks:
        p = add_prefix(network)
        try:
            p.save()
        except Exception as exc:
            log.write("ERROR: {}\n".format(exc))
            log.write("INFO: prefix: {}, type: {}, comment: {}\n".format(p.prefix, p.type, p.description))

        for host in network['hosts']:
            p = add_host(host)
            try:
                p.save()
            except Exception as exc:
                log.write("ERROR: {}\n".format(exc))
                log.write("INFO: host: {}, type: {}, node: {}, desc: {}, comment: {}\n".format(p.prefix, p.type, p.node, p.description, p.comment))

    if os.path.getsize(args.logfile) > 0:
        print("Done with errors, have a look in {}...".format(args.logfile))
    else:
        print("All done!")

    log.close()
