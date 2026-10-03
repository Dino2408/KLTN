# Durable ingestion and replay

The ingestion layer now uses Redis Streams as a durable handoff between collectors and the processing pipeline.

## Inputs

- HTTP: `POST /v1/events` on port 8000.
- Syslog TCP: port 5514.
- Syslog UDP: port 5514.
- File tailing: `data/ingest/*.log`.

Every accepted record becomes an envelope containing raw data, source, transport, receive time and metadata.

## Processing

The `pipeline-api` service consumes stream `siem:events` through Redis consumer group `pipeline`. A successful event is acknowledged only after processing. Unknown parser results and processing exceptions are copied to `siem:dlq` for controlled review/replay.

## Replay

`POST /v1/replay?limit=100` moves records from the DLQ back to the main event stream.

This is intentionally at-least-once processing. Consumers must therefore keep downstream actions idempotent before automated response is enabled.

## Deployment

Redis persistence uses AOF plus periodic snapshots and a Docker named volume. Docker Compose waits for the Redis healthcheck before starting ingestion and pipeline services. Compose supports `service_healthy` dependencies when a healthcheck is defined. citeturn0search2turn0search3

## Wazuh integration

Wazuh can receive syslog from firewalls, switches and routers, and its current documentation supports TCP or UDP syslog listeners. This project can alternatively receive the same upstream syslog stream directly when the deployment requires the adaptive parser pipeline to own ingestion. citeturn0search7

JSON events can also be forwarded without requiring a vendor-specific Wazuh decoder because Wazuh provides a JSON decoder for dynamic fields. citeturn0search0
