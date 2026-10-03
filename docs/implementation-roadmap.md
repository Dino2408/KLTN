# Universal Log Pipeline implementation roadmap

## Phase 1 — Foundation
- deterministic fingerprint/template extraction
- parser registry
- parser runtime
- unknown-format path
- isolated AI parser generator
- deterministic parser validator
- ECS-oriented normalization
- raw-event preservation

## Phase 2 — Production ingestion
- syslog TCP/UDP
- file tailing
- HTTP ingestion
- Wazuh adapter
- Suricata EVE adapter
- multiline event assembler
- backpressure and dead-letter queue

## Phase 3 — Detection
- enrichment
- asset identity
- threat intelligence
- event correlation
- rule engine
- AI security analysis

## Phase 4 — Response
- deterministic policy engine
- approval gates
- Shuffle integration
- playbook registry
- idempotency and audit trail

## Phase 5 — Evaluation
Measure parser coverage, extraction accuracy, normalization accuracy, unknown-format recovery, LLM call reduction, throughput, latency and security-detection metrics.
