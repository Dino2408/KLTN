# Lecturer demo

This branch includes a small end-to-end demonstration path. It is intentionally safe: the SOAR adapter defaults to dry-run and does not call an external response system.

## Prerequisites

- Ubuntu Server with Docker Engine and Docker Compose.
- NVIDIA Container Toolkit if the local Ollama container should use the GTX 1070 Ti.
- The selected Ollama model available locally.

## Run

```bash
chmod +x scripts/demo-e2e.sh
./scripts/demo-e2e.sh
```

The script sends five SSH-deny events from the same source IP. The configured correlation threshold is five events in five minutes. The expected chain is:

```
raw log
 -> parser
 -> normalization
 -> enrichment
 -> stateful correlation
 -> detection
 -> local AI analysis
 -> policy evaluation
 -> SOAR dry-run
 -> audit
```

## What to show the lecturer

1. The normalized event.
2. `CORR-REPEATED-SOURCE` detection.
3. AI analysis result.
4. Policy decision and idempotency key.
5. SOAR `SIMULATED` result.
6. The append-only audit record.

The pre-seeded firewall parser is deterministic and can also be used to demonstrate that a previously unknown log template can become a validated parser artifact.

## Safety

The default is:

```text
SOAR_DRY_RUN=true
```

Keep this value for the thesis demonstration unless a real Shuffle workflow has been configured and explicitly tested.
