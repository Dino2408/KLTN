# Universal Log Pipeline implementation roadmap

## Completed foundation
- deterministic fingerprint/template extraction
- parser registry and runtime
- unknown-format path
- isolated AI parser generator
- deterministic parser validator
- ECS-oriented normalization with raw-event preservation
- HTTP ingestion envelope
- Wazuh and Suricata adapters
- multiline event assembler
- template clustering
- enrichment service boundary
- correlation service boundary
- deterministic detection service
- policy gate
- append-only audit service
- end-to-end pipeline API

## Next production milestones
1. Persistent event bus and durable queue.
2. Syslog TCP/UDP listeners and file tailer with backpressure.
3. Real template clustering over batches rather than single-event fingerprints.
4. AI semantic mapper with explicit evidence for every mapping.
5. Parser repair loop using failed validation samples.
6. Full ECS mapping plus optional OCSF projection.
7. Asset/identity, GeoIP and threat-intelligence enrichment adapters.
8. Stateful correlation windows and rule registry.
9. AI security analysis over correlated signals.
10. Policy versioning, approval workflow, idempotency and rate limits.
11. Shuffle playbook adapter and response executor.
12. Replay engine for reprocessing historical raw events.
13. Benchmark datasets and reproducible evaluation.

## Evaluation
Measure:
- parser coverage
- field extraction precision/recall
- normalization accuracy
- unknown-format recovery
- false extraction rate
- LLM calls avoided by deterministic parsing
- throughput and P50/P95/P99 latency
- correlation precision/recall
- detection TP/FP/FN/TN
- response policy violations (target: zero)

The word "universal" means adaptive coverage across heterogeneous and previously unseen templates within the supported transport/serialization envelope. It does not claim support for every possible proprietary format.
