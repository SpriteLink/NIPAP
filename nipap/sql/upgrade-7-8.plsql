--
-- Upgrade from NIPAP database schema version 7 to 8
--

--
-- Kafka event table and triggers
--
-- This table is used as a queue for the external kafka_producer process.
-- Triggers on the core tables insert events here. The daemon will enable or
-- disable these triggers at startup depending on configuration.
--
CREATE TABLE IF NOT EXISTS kafka_produce_event (
	id SERIAL PRIMARY KEY,
	table_name TEXT NOT NULL,
	event_type TEXT NOT NULL,
	payload JSONB,
	processed BOOLEAN DEFAULT FALSE,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE OR REPLACE FUNCTION tf_kafka_produce_event() RETURNS trigger AS $$
BEGIN
	IF TG_OP = 'DELETE' THEN
		INSERT INTO kafka_produce_event (table_name, event_type, payload) VALUES (TG_TABLE_NAME, TG_OP, row_to_json(OLD)::jsonb);
	ELSIF OLD IS DISTINCT FROM NEW THEN
		INSERT INTO kafka_produce_event (table_name, event_type, payload) VALUES (TG_TABLE_NAME, TG_OP, row_to_json(NEW)::jsonb);
	END IF;
	RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers that write to kafka_produce_event
CREATE TRIGGER trigger_kafka_ip_net_plan
	AFTER INSERT OR UPDATE OR DELETE
	ON ip_net_plan
	FOR EACH ROW
	EXECUTE PROCEDURE tf_kafka_produce_event();

CREATE TRIGGER trigger_kafka_ip_net_vrf
	AFTER INSERT OR UPDATE OR DELETE
	ON ip_net_vrf
	FOR EACH ROW
	EXECUTE PROCEDURE tf_kafka_produce_event();

CREATE TRIGGER trigger_kafka_ip_net_pool
	AFTER INSERT OR UPDATE OR DELETE
	ON ip_net_pool
	FOR EACH ROW
	EXECUTE PROCEDURE tf_kafka_produce_event();


-- update database schema version
COMMENT ON DATABASE %s IS 'NIPAP database - schema version: 8';
