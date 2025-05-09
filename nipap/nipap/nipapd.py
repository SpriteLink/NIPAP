#!/usr/bin/env python3
# vim: et sw=4 sts=4 :

import fcntl
import logging.handlers
import logging
import argparse
import os
import sys
import configparser
import ssl

from tornado.netutil import bind_sockets
from tornado.httpserver import HTTPServer
from tornado.wsgi import WSGIContainer
import tornado.process
from tornado.ioloop import IOLoop

from nipap.nipapconfig import NipapConfig, NipapConfigError
from nipap.errors import *
from nipap.backend import NipapError

import psutil
import signal
import atexit

from flask import Flask
try:
    from flask_compress import Compress
except ImportError:
    from flask.ext.compress import Compress

def exit_cleanup():
    """ Cleanup stuff on program exit
    """
    # stop the main tornado loop
    IOLoop.instance().stop()
    # find all our child processes and kill them off
    try:
        p = psutil.Process(os.getpid())
    except psutil.NoSuchProcess:
        return

    children = p.children

    for pid in children(recursive=True):
        os.kill(pid.pid, signal.SIGTERM)


@atexit.register
def at_exit():
    exit_cleanup()


def handle_sigterm(sig, frame):
    """ Handle SIGTERM
    """
    exit_cleanup()
    # and make a clean exit ourselves
    # sys.exit(0)


# register signal handler for SIGTERM
signal.signal(signal.SIGTERM, handle_sigterm)


def drop_privileges(uid_name='nobody', gid_name='nogroup'):
    if os.getuid() != 0:
        raise NipapError("non-root user cannot drop privileges")

    import pwd
    import grp
    # Get the uid/gid from the name
    uid = pwd.getpwnam(uid_name).pw_uid
    gid = grp.getgrnam(gid_name).gr_gid

    # Remove group privileges
    os.setgroups([])

    # Try setting the new uid/gid
    os.setgid(gid)
    os.setuid(uid)

    # Ensure a very conservative umask
    old_umask = os.umask(0o077)


def run():
    parser = argparse.ArgumentParser(description='NIPAP backend server')
    parser.add_argument('--auto-install-db', action='store_true', help='automatically install db schema')
    parser.add_argument('--auto-upgrade-db', action='store_true', help='automatically upgrade db schema')
    parser.add_argument('-d', '--debug', action='store_true', default=None, dest='debug', help='enable debugging')
    parser.add_argument('-f', '--foreground', action='store_true', default=None, dest='foreground',
                        help='run in foreground and log to stdout')
    parser.add_argument('-l', '--listen', type=str, metavar='ADDRESS', help='listen to IPv4/6 ADDRESS')
    parser.add_argument('-p', '--port', dest='port', type=int, help='listen on TCP port PORT')
    parser.add_argument('-s', '--ssl-port', dest='ssl_port', type=int,
                        help='listen with SSL on TCP port PORT')
    parser.add_argument('-c', '--config', dest='config_file', type=str, default='/etc/nipap/nipap.conf',
                        help='read configuration from file CONFIG_FILE')
    parser.add_argument('-P', '--pid-file', type=str, help='write a PID file to PID_FILE')
    parser.add_argument('--no-pid-file', action='store_true', default=False,
                        help='turn off writing PID file (overrides config file)')
    parser.add_argument('--version', action='store_true', help='display version information and exit')
    parser.add_argument("--db-version", dest="dbversion", action="store_true",
                        help="display database schema version information and exit")
    # Arguments overwriting config settings
    cfg_args = ['debug', 'foreground', 'port', 'config_file']

    args = parser.parse_args()

    if args.version:
        import nipap

        print("nipapd version:", nipap.__version__)
        sys.exit(0)

    # set logging format
    LOG_FORMAT = "%(asctime)s: %(module)-10s %(levelname)-8s %(message)s"
    # setup basic logging
    logging.basicConfig(format=LOG_FORMAT)
    logger = logging.getLogger()

    try:
        cfg = NipapConfig(args.config_file)
    except NipapConfigError as exc:
        if args.config_file:
            print("The specified configuration file ('" + args.config_file + "') does not exist", file=sys.stderr)
            sys.exit(1)
        # if no config file is specified, we'll live with our defaults

    # Go through list of argparse args and set the config object to
    # their values.
    args_dict = vars(args)
    for arg_dest in cfg_args:
        if arg_dest in args_dict and args_dict[arg_dest] is not None:
            try:
                cfg.set('nipapd', arg_dest, str(args_dict[arg_dest]))
            except configparser.NoSectionError as exc:
                print("The configuration file contains errors:", exc, file=sys.stderr)
                sys.exit(1)

    # Validate configuration before forking, to be able to print error message to user
    setup_plaintext = cfg.get('nipapd', 'port') != ''
    setup_ssl = cfg.get('nipapd', 'ssl_port') != ''
    if not setup_plaintext and not setup_ssl:
        print >> sys.stderr, "ERROR: Configured to listen to neither plaintext nor SSL"
        sys.exit(1)
    if setup_ssl and cfg.get('nipapd', 'ssl_cert_file') is None:
        print >> sys.stderr, "ERROR: ssl_port configured but ssl_cert_file missing"
        sys.exit(1)

    # drop privileges
    if cfg.get('nipapd', 'user') != '':
        run_user = cfg.get('nipapd', 'user')
        if cfg.get('nipapd', 'group') != '':
            run_group = cfg.get('nipapd', 'group')
        else:
            run_group = cfg.get('nipapd', 'user')
        try:
            drop_privileges(run_user, run_group)
        except NipapError:
            print(("nipapd is configured to drop privileges and run as user '%s' and group '%s', \n"
                   "but was not started as root and can therefore not drop privileges") % (run_user, run_group),
                  file=sys.stderr)
            sys.exit(1)
        except KeyError:
            print("Could not drop privileges to user '%s' and group '%s'" % (run_user, run_group), file=sys.stderr)
            sys.exit(1)

    from nipap.backend import Nipap

    try:
        nip = Nipap(args.auto_install_db, args.auto_upgrade_db)
    except NipapDatabaseSchemaError as exc:
        print("ERROR:", str(exc), file=sys.stderr)
        print("HINT: You can automatically install required extensions and the nipap schema with --auto-install-db",
              file=sys.stderr)
        sys.exit(1)
    except NipapError as exc:
        print("ERROR:", str(exc), file=sys.stderr)
        sys.exit(1)

    if args.dbversion:
        print("nipap db schema:", nip._get_db_version())
        sys.exit(0)

    # check local auth db version
    from nipap import authlib

    a = authlib.SqliteAuth('local', 'a', 'b', 'c')
    try:
        latest = a._latest_db_version()
        if not latest:
            print("It seems your Sqlite database for local auth is out of date", file=sys.stderr)
            print("Please run 'nipap-passwd --upgrade-database' to upgrade your database.", file=sys.stderr)
            sys.exit(2)
    except authlib.AuthSqliteError as e:
        print("Error checking version of Sqlite database for local auth: %s" % e, file=sys.stderr)
        sys.exit(1)
    del a

    if not cfg.getboolean('nipapd', 'foreground'):
        import nipap.daemon

        ret = nipap.daemon.createDaemon()

    # pid file handling
    if cfg.get('nipapd', 'pid_file') and not args.no_pid_file:
        # need a+ to be able to read PID from file
        try:
            lf = open(cfg.get('nipapd', 'pid_file'), 'a+')
            lf.seek(0)
        except IOError as exc:
            logger.error("Unable to open PID file '" + str(exc.filename) + "': " + str(exc.strerror))
            sys.exit(1)
        try:
            fcntl.flock(lf, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            logger.error('NIPAPd already running (pid: ' + lf.read().strip() + ')')
            sys.exit(1)
        logger.debug('Writing PID to file: ' + cfg.get('nipapd', 'pid_file'))
        lf.truncate(0)
        lf.write('%d\n' % os.getpid())
        lf.flush()

    # flask app setups
    app = Flask(__name__)

    # Configure tracing
    if cfg.has_section("tracing"):
        try:
            from nipap.tracing import init_tracing, setup
            from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
            from opentelemetry.instrumentation.flask import FlaskInstrumentor
            from opentelemetry.sdk.trace.sampling import _KNOWN_SAMPLERS

            sampler = None

            if cfg.has_option("tracing", "otel_traces_sampler"):
                trace_sampler = cfg.get("tracing", "otel_traces_sampler")
                if trace_sampler not in _KNOWN_SAMPLERS:
                    raise NipapConfigError(f"Unknown otel_traces_sampler '{trace_sampler}'. Valid samplers are: '{list(_KNOWN_SAMPLERS.keys())}'")
                sampler = _KNOWN_SAMPLERS[trace_sampler]

            if cfg.has_option("tracing", "otlp_grpc_endpoint"):
                init_tracing("nipapd", cfg.get("tracing", "otlp_grpc_endpoint", sampler))
            elif cfg.has_option("tracing", "otlp_http_endpoint"):
                init_tracing("nipapd", cfg.get("tracing", "otlp_http_endpoint"), sampler, False)
            else:
                raise NipapConfigError("Tracing enabled but no OTLP endpoint configured")

            FlaskInstrumentor.instrument_app(app, excluded_urls="/v1/traces")
            Psycopg2Instrumentor().instrument(enable_commenter=True, commenter_options={})

            # Configure proxy of traces from nipap-cli to collector
            try:
                setup(app, cfg.get("tracing", "otlp_http_endpoint"))
            except configparser.NoOptionError:
                logger.info('Found no OTLP HTTP endpoint, OTLP proxy disabled')
                pass
            logger.debug('Tracing is enabled and successfully set up')
        except KeyError:
            logger.error('Error in tracing configuration, tracing not enabled')
            pass
        except ImportError as err:
            logger.error('Failed to import tracing library %s, tracing not enabled', err.name)
            pass
    else:
        logger.debug('Tracing is disabled')

    Compress(app)

    # Set up sockets for handling plaintext and SSL connections
    sockets = []
    ssl_sockets = []
    if cfg.get('nipapd', 'listen') is None or cfg.get('nipapd', 'listen') == '':
        if setup_plaintext:
            sockets = bind_sockets(cfg.get('nipapd', 'port'))
        if setup_ssl:
            ssl_sockets = bind_sockets(cfg.get('nipapd', 'ssl_port'))
    else:
        for entry in cfg.get('nipapd', 'listen').split(','):
            address = entry
            if setup_plaintext:
                port = int(cfg.get('nipapd', 'port'))
                socket = bind_sockets(port, address)
                sockets += socket
            if setup_ssl:
                ssl_port = int(cfg.get('nipapd', 'ssl_port'))
                ssl_socket = bind_sockets(ssl_port, address)
                ssl_sockets += ssl_socket

    num_forks = None
    try:
        if cfg.getint('nipapd', 'forks') == -1:
            num_forks = False
        elif cfg.getint('nipapd', 'forks') == 0:
            num_forks = None
        elif cfg.getint('nipapd', 'forks') > 0:
            num_forks = cfg.getint('nipapd', 'forks')
    except:
        pass

    # pre-fork unless explicitly disabled
    if num_forks is not False:
        # default is to fork as many processes as there are cores
        tornado.process.fork_processes(num_forks)

    import nipap.rest
    rest = nipap.rest.setup(app)

    import nipap.xmlrpc
    nipapxml = nipap.xmlrpc.setup(app)

    if not cfg.getboolean('nipapd', 'foreground'):
        # If we are not running in the foreground, remove current handlers which
        # include a default streamhandler to stdout to prevent messages on
        # stdout when in daemon mode.
        for h in logger.handlers:
            logger.removeHandler(h)

    # logging
    if cfg.getboolean('nipapd', 'debug'):
        logger.setLevel(logging.DEBUG)
        nipapxml.logger.setLevel(logging.DEBUG)
        rest.logger.setLevel(logging.DEBUG)

    if cfg.getboolean('nipapd', 'syslog'):
        log_syslog = logging.handlers.SysLogHandler(address='/dev/log')
        log_syslog.setFormatter(logging.Formatter("%(levelname)-8s %(message)s"))
        logger.addHandler(log_syslog)
        nipapxml.logger.addHandler(log_syslog)
        rest.logger.addHandler(log_syslog)


    if setup_plaintext:
        http_server = HTTPServer(WSGIContainer(app))
        http_server.add_sockets(sockets)

    if setup_ssl:
        ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        try:
            ssl_ctx.load_cert_chain(cfg.get("nipapd", "ssl_cert_file"),
                                    keyfile=cfg.get("nipapd", "ssl_key_file"))
        except ssl.SSLError as err:
            logging.error("SSL Initialization failed: %s", err)
            sys.exit(1)

        https_server = HTTPServer(WSGIContainer(app), ssl_options=ssl_ctx)
        https_server.add_sockets(ssl_sockets)

    # start Tornado
    try:
        IOLoop.instance().start()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as exc:
        logger.error(exc)
        sys.exit(1)


if __name__ == '__main__':
    run()
