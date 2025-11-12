#!/usr/bin/env python3
# Simple Kafka producer process for NIPAP
# This process polls the kafka_produce_event table and forwards events to Kafka.
# It is intended to be forked by nipapd.

import json
import logging
import time
from typing import Any

try:
    from kafka import KafkaProducer
except Exception:
    KafkaProducer = None

import psycopg2
import psycopg2.extras

from nipap.nipapconfig import NipapConfig

LOG = logging.getLogger("nipap.kafka_producer")
LOG.addHandler(logging.NullHandler())


def _build_db_args(cfg):
    db_args = {}
    db_args['host'] = cfg.get('nipapd', 'db_host')
    db_args['database'] = cfg.get('nipapd', 'db_name')
    db_args['user'] = cfg.get('nipapd', 'db_user')
    db_args['password'] = cfg.get('nipapd', 'db_pass')
    db_args['sslmode'] = cfg.get('nipapd', 'db_sslmode')
    db_args['port'] = cfg.get('nipapd', 'db_port')

    if db_args['host'] is not None and db_args['host'] in ('', '""'):
        db_args['host'] = None
    for key in list(db_args.keys()):
        if db_args[key] is None:
            del db_args[key]

    return db_args


def _connect_db(cfg):
    db_args = _build_db_args(cfg)
    conn = None
    while True:
        try:
            conn = psycopg2.connect(**db_args, cursor_factory=psycopg2.extras.RealDictCursor)
            conn.autocommit = False
            psycopg2.extras.register_hstore(conn, globally=True)
            break
        except Exception as e:
            LOG.error("Unable to connect to DB for kafka_producer: %s. Retrying in 5s", e)
            time.sleep(5)
    return conn


def _create_kafka_producer(cfg):
    if KafkaProducer is None:
        LOG.error("kafka-python not installed, kafka producer disabled")
        return None

    brokers = None
    try:
        if cfg.has_option('kafka', 'brokers'):
            brokers = cfg.get('kafka', 'brokers')
    except Exception:
        brokers = None

    if not brokers:
        LOG.error("No 'kafka.brokers' configured, kafka producer disabled")
        return None

    # brokers could be comma separated list
    brokers_list = [b.strip() for b in brokers.split(',') if b.strip()]

    # allow optional producer configs
    producer_cfg: dict[str, Any] = {'bootstrap_servers': brokers_list,
                    'value_serializer': lambda v: json.dumps(v).encode('utf-8'),
                    'key_serializer': lambda k: str(k).encode('utf-8')}
    
    # Add SASL_SSL security protocol support
    try:
        if cfg.has_option('kafka', 'security_protocol'):
            security_protocol = cfg.get('kafka', 'security_protocol')
            
            # Currently only SASL_SSL is supported
            if security_protocol != 'SASL_SSL':
                LOG.error("Security protocol '%s' is not supported. Only SASL_SSL is currently supported.", security_protocol)
                return None
            
            producer_cfg['security_protocol'] = security_protocol
            
            # If using SASL_SSL, require SASL credentials
            if security_protocol == 'SASL_SSL':
                # Get SASL mechanism (default to PLAIN)
                sasl_mechanism = 'PLAIN'
                if cfg.has_option('kafka', 'sasl_mechanism'):
                    sasl_mechanism = cfg.get('kafka', 'sasl_mechanism')
                producer_cfg['sasl_mechanism'] = sasl_mechanism
                
                # Get SASL username and password
                if cfg.has_option('kafka', 'sasl_username'):
                    sasl_username = cfg.get('kafka', 'sasl_username')
                    producer_cfg['sasl_plain_username'] = sasl_username
                else:
                    LOG.warning("SASL_SSL configured but sasl_username not provided")
                
                if cfg.has_option('kafka', 'sasl_password'):
                    sasl_password = cfg.get('kafka', 'sasl_password')
                    producer_cfg['sasl_plain_password'] = sasl_password
                else:
                    LOG.warning("SASL_SSL configured but sasl_password not provided")
                
                # Optional: SSL CA certificate verification
                if cfg.has_option('kafka', 'ssl_cafile'):
                    ssl_cafile = cfg.get('kafka', 'ssl_cafile')
                    producer_cfg['ssl_cafile'] = ssl_cafile
                
                # Optional: SSL hostname verification
                if cfg.has_option('kafka', 'ssl_check_hostname'):
                    try:
                        ssl_check_hostname = cfg.getboolean('kafka', 'ssl_check_hostname')
                        producer_cfg['ssl_check_hostname'] = ssl_check_hostname
                    except Exception:
                        LOG.warning("Invalid value for ssl_check_hostname, using default")
    except Exception as e:
        LOG.warning("Failed to configure security settings: %s", e)
    
    try:
        # additional options could be added in config later
        producer = KafkaProducer(**producer_cfg)
        return producer
    except Exception as e:
        LOG.exception("Failed to create KafkaProducer: %s", e)
        return None


def _ensure_producer(cfg, base_delay=1, max_delay=60):
    """
    Ensure a KafkaProducer is available. If broker(s) are unavailable, keep retrying
    with exponential backoff until a producer can be created. If kafka-python is not
    installed, return None immediately.
    """
    if KafkaProducer is None:
        LOG.error("kafka-python not installed; cannot create KafkaProducer")
        return None

    attempt = 0
    delay = base_delay
    while True:
        attempt += 1
        producer = _create_kafka_producer(cfg)
        if producer is not None:
            LOG.info("Successfully created KafkaProducer (attempt %d)", attempt)
            return producer
        LOG.error("Kafka producer not available, retrying in %ds (attempt %d)", min(delay, max_delay), attempt)
        time.sleep(min(delay, max_delay))
        delay = min(delay * 2, max_delay)


def _send_with_backoff(producer, topic, value, key=None, max_retries=10, base_delay=1, max_delay=60):
    """
    Attempt to send a message via KafkaProducer, retrying with exponential backoff on failure.
    Returns True if the send was initiated successfully, False otherwise.
    If producer is None, returns False immediately.
    """
    if producer is None:
        LOG.warning("Kafka producer is not available; cannot send message to %s", topic)
        return False

    attempt = 0
    delay = base_delay
    while True:
        try:
            # producer.send is async; it may still raise on client-side errors
            producer.send(topic, value, key)
            return True
        except Exception as e:
            attempt += 1
            LOG.warning("Kafka producer send failed for topic %s (attempt %d/%d): %s", topic, attempt, max_retries, e)
            if attempt >= max_retries:
                LOG.exception("Exceeded max retries (%d) for sending to topic %s. Giving up.", max_retries, topic)
                return False
            # sleep before next retry with growing delay
            time.sleep(min(delay, max_delay))
            delay *= 2.0


def run(config_path=None):
    """
    Entry point for the kafka producer process.
    :param config_path: path to configuration file (will be read via NipapConfig)
    """
    # configure basic logging to stderr so daemonized process has something
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)-20s %(levelname)-8s %(message)s")

    try:
        cfg = NipapConfig(config_path)
    except Exception as e:
        LOG.error("Unable to read config %s: %s", config_path, e)
        return

    LOG.info("Starting kafka producer (config: %s)", config_path)

    # poll interval seconds
    poll_interval = 2
    try:
        if cfg.has_option('kafka', 'poll_interval'):
            poll_interval = int(cfg.get('kafka', 'poll_interval'))
    except Exception:
        poll_interval = 2

    # topic prefix default
    topic_prefix = "nipap."
    try:
        if cfg.has_option('kafka', 'topic_prefix'):
            topic_prefix = cfg.get('kafka', 'topic_prefix')
    except Exception:
        topic_prefix = "nipap."

    conn = _connect_db(cfg)
    cur = conn.cursor()

    # ensure a producer is available before entering the main loop. This will retry
    # indefinitely if brokers are unavailable, ensuring the process keeps trying to connect.
    producer = _ensure_producer(cfg)
    if producer is None:
        # _ensure_producer returns None if kafka-python isn't installed or config invalid
        LOG.error("Kafka producer not available (missing dependency or bad config), exiting kafka_producer process")
        return

    LOG.info("Kafka producer connected, starting event loop")

    # main loop
    while True:
        try:
            # begin transaction
            cur.execute("BEGIN;")

            # fetch a batch of unlocked events
            cur.execute("""
                SELECT id, table_name, event_type, payload
                FROM kafka_produce_event
                WHERE processed = FALSE
                ORDER BY id
                FOR UPDATE SKIP LOCKED
                LIMIT 100
            """)
            rows = cur.fetchall()

            if not rows:
                # nothing to do
                conn.rollback()
                time.sleep(poll_interval)
                continue

            # send events to kafka
            ids = []
            send_failed = False
            for row in rows:
                try:
                    event_id = row['id']
                    table = row['table_name']
                    etype = row['event_type']
                    payload = row['payload']

                    topic = f"{topic_prefix}{table}"
                    message = {'event_type': etype, 'payload': payload}
                    # send with retries and exponential backoff
                    sent = _send_with_backoff(producer, topic, message, payload.get('id'))
                    if sent:
                        ids.append(event_id)
                    else:
                        # sending failed (producer might be disconnected); mark to recreate producer
                        LOG.error("Failed to send event id %s to topic %s; will attempt to recreate producer", event_id, topic)
                        send_failed = True
                        break
                except Exception as e:
                    # if a single event fails to prepare, log and skip it for now
                    LOG.exception("Failed to send event id %s: %s", row.get('id'), e)

            if send_failed:
                # rollback processing of this batch, attempt to recreate producer and retry later
                try:
                    conn.rollback()
                except Exception:
                    pass
                # try to recreate producer (this will block until a producer is available)
                LOG.info("Attempting to recreate Kafka producer after send failures")
                producer = _ensure_producer(cfg)
                if producer is None:
                    LOG.error("Unable to recreate Kafka producer; exiting kafka_producer process")
                    return
                # back off a bit before next attempt to avoid tight loop
                time.sleep(max(1, poll_interval))
                continue

            # flush to ensure delivery or at least attempt
            try:
                producer.flush(timeout=10)
            except Exception:
                LOG.exception("Kafka producer flush failed")
                # try to recreate producer on flush failure
                try:
                    conn.rollback()
                except Exception:
                    pass
                LOG.info("Attempting to recreate Kafka producer after flush failure")
                producer = _ensure_producer(cfg)
                if producer is None:
                    LOG.error("Unable to recreate Kafka producer; exiting kafka_producer process")
                    return
                time.sleep(max(1, poll_interval))
                continue

            # mark processed for ids that were attempted
            if ids:
                cur.execute("UPDATE kafka_produce_event SET processed = TRUE WHERE id = ANY(%s);", (ids,))
                conn.commit()
            else:
                conn.rollback()

        except Exception as e:
            LOG.exception("Unexpected error in kafka_producer loop: %s", e)
            try:
                conn.rollback()
            except Exception:
                pass
            # backoff on error
            time.sleep(max(1, poll_interval))
