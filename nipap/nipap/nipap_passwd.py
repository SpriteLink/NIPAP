#!/usr/bin/env python3
#
# Manages NIPAP LocalAuth authentication database
#

import sys
import os
import argparse
import logging

import nipap.authlib
from nipap.nipapconfig import NipapConfig, NipapConfigError


def run():
    # parse arguments
    parser = argparse.ArgumentParser(description='NIPAP User configuration')
    parser.add_argument('action',
                        metavar='{list, add, delete, modify, test-user, latest-version, create-database, upgrade-database}',
                        nargs='?', type=str,
                        choices=['list', 'add', 'delete', 'modify', 'test-user', 'latest-version', 'create-database',
                                 'upgrade-database'],
                        help='define an action to execute')
    parser.add_argument('-u', '--username', dest='user', type=str,
                        help='username')
    parser.add_argument('-p', '--password', dest='password', type=str,
                        help='set user\'s password to PASSWORD')
    parser.add_argument('-n', '--name', dest='name', type=str,
                        help='set user\'s name to NAME')
    parser.add_argument('-t', '--trusted', action='store_true', dest='trusted',
                        default=None, help='mark user as trusted')
    parser.add_argument('--no-trusted', action='store_false', dest='trusted',
                        default=None, help='mark user as not trusted')
    parser.add_argument('-r', '--readonly', action='store_true', dest='readonly',
                        default=None, help='set user to read only')
    parser.add_argument('--no-readonly', action='store_false', dest='readonly',
                        default=None, help='set user to read write')
    parser.add_argument('-f', '--file', dest='db_file', type=str,
                        help="database file [default: read from config]")
    parser.add_argument('-c', '--config', dest='config',
                        default='/etc/nipap/nipap.conf', type=str, help=
                        'read configuration from CONFIG [default:/etc/nipap/nipap.conf]')
    parser.add_argument('--version', action='version',
                        version='nipap-passwd version %s' % nipap.__version__)
    args = parser.parse_args()

    logger = logging.getLogger()
    log_format = "%(levelname)-8s %(message)s"
    log_stream = logging.StreamHandler()
    log_stream.setFormatter(logging.Formatter("%(asctime)s: " + log_format))
    logger.setLevel(logging.WARNING)
    logger.addHandler(log_stream)

    try:
        cfg = NipapConfig(args.config)
    except NipapConfigError as exc:
        print("The specified configuration file ('" + args.config + "') does not exist", file=sys.stderr)
        sys.exit(1)

    if args.db_file:
        cfg.set('auth.backends.local', 'db_path', args.db_file)

    a = nipap.authlib.SqliteAuth('local', 'a', 'b', 'c')

    if args.action == 'list':
        # print a nicely formatted list of users
        header = "{:<20} {:<25} {:<7} {:<7}".format('username', 'real name', 'trusted', 'read only')
        print("{}\n{}".format(header, ''.join('-' for x in range(len(header)))))
        for u in a.list_users():
            if not args.user or args.user == u['username']:
                print("%-20s %-25s %-7d %-7d" % (u['username'], u['full_name'], int(u['trusted']), int(u['readonly'])))

    elif args.action == 'test-user':
        if not args.user:
            print("Please specify user with --user")
            sys.exit(1)
        if not args.password:
            print("Please specify password with --password")
            sys.exit(1)
        af = nipap.authlib.AuthFactory()
        auth = af.get_auth(args.user, args.password, "nipap", {})
        if not auth.authenticate():
            print("The username or password seems to be wrong")
            sys.exit(2)

        print("Username and password seem to be correct")
        sys.exit(0)

    elif args.action == 'add':
        if not args.user:
            print("Please specify user with --user")
            sys.exit(1)
        if not args.password:
            print("Please specify password with --password")
            sys.exit(1)
        if not args.name:
            print("Please specify name with --name")
            sys.exit(1)
        try:
            a.add_user(args.user, args.password, args.name, args.trusted, args.readonly)
            print("Added user {} to database {}".format(args.user, cfg.get('auth.backends.local', 'db_path')))
        except nipap.authlib.AuthError as exc:
            if str(exc) == 'attempt to write a readonly database':
                print("You do not have sufficient rights to write to database: %s" % (
                    cfg.get('auth.backends.local', 'db_path')))
            elif str(exc) == 'column username is not unique':
                print("Username '{}' already exists in the database: {} ".format(args.user,
                                                                                 cfg.get('auth.backends.local',
                                                                                         'db_path')))
            else:
                print(exc)

    elif args.action == 'delete':
        try:
            if not args.user:
                print("Please specify user with --user")
                sys.exit(1)
            a.remove_user(args.user)
            print("User {} deleted from database {}".format(args.user, cfg.get('auth.backends.local', 'db_path')))
        except nipap.authlib.AuthError as exc:
            if str(exc) == 'attempt to write a readonly database':
                print("You do not have sufficient rights to write to database: %s" % (
                    cfg.get('auth.backends.local', 'db_path')))
            else:
                print(exc)

    elif args.action == 'modify':
        if not args.user:
            print("Please specify user with --user")
            sys.exit(1)

        data = {}
        if args.password is not None:
            data['password'] = args.password
        if args.name is not None:
            data['full_name'] = args.name
        if args.trusted is not None:
            data['trusted'] = args.trusted
        if args.readonly is not None:
            data['readonly'] = args.readonly

        if len(data) == 0:
            print("Please specify value to change")
            sys.exit(1)

        try:
            a.modify_user(args.user, data)
        except nipap.authlib.AuthError as exc:
            if str(exc) == 'attempt to write a readonly database':
                print("You do not have sufficient rights to write to database: %s" % (
                    cfg.get('auth.backends.local', 'db_path')))
            else:
                print(exc)

    elif args.action == 'upgrade-database':
        a._upgrade_database()
        sys.exit(0)

    elif args.action == 'create-database':
        a._create_database()
        sys.exit(0)

    elif args.action == 'latest-version':
        try:
            latest = a._latest_db_version()
            if not latest:
                print("It seems your Sqlite database for local auth is out of date", file=sys.stderr)
                print("Please run 'nipap-passwd upgrade-database' to upgrade your database.", file=sys.stderr)
                sys.exit(2)
        except nipap.authlib.AuthSqliteError as e:
            print("Error checking version of Sqlite database for local auth: %s" % e, file=sys.stderr)
            sys.exit(1)
        print("Sqlite database for local auth is of the latest version.")
        sys.exit(0)

    else:
        parser.print_help()


if __name__ == '__main__':
    run()
