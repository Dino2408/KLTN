# KLTN — AI-SIEM-SOAR

KLTN is an AI-augmented SIEM/SOAR research platform whose core ingestion objective is **adaptive processing of heterogeneous and previously unseen log templates**.

## Core architecture

```
Any Log
  -> Ingestion
  -> Fingerprint / Template
  -> Parser Registry
       | known -> Deterministic Parser
       | unknown -> AI Parser Generator -> Validator -> Active Registry
  -> ECS-oriented Normalization
  -> Enrichment
  -> Correlation
  -> Detection
  -> AI Security Analysis
  -> Policy Engine
  -> SOAR
```

The system preserves the original event so that parser versions can be replayed and corrected without losing evidence. The LLM proposes parser specifications and security reasoning; deterministic services validate, execute and enforce policy.

## Current implementation

- `parser-engine/` — fingerprinting, parser registry and deterministic runtime.
- `ai-parser/` — isolated local-LLM parser proposal service.
- `parser-validator/` — deterministic candidate validation and activation gate.
- `normalization/` — ECS-oriented normalized event construction.
- `pipeline-api/` — end-to-end ingestion path.
- `ai-gateway/` — security analysis and policy layer inherited from the MVP foundation.
- `parsers/active/` — validated parser artifacts.
- `parsers/candidates/` — rejected or pending parser artifacts.
- `tests/` — parser regression tests.
- `docs/universal-log-pipeline.md` — architecture and safety contract.
- `docs/implementation-roadmap.md` — next implementation phases.

## Universal does not mean an unbounded claim

The project does not claim that a finite parser can understand every proprietary format in existence. Instead, it defines universal ingestion as an adaptive pipeline that can retain unknown logs, fingerprint their templates, generate candidate parsers with a local LLM, validate them deterministically, and activate only validated parser artifacts.

## Deployment

Docker Compose remains the development orchestration layer. The Compose Specification is the current recommended Compose format. The production deployment will later split ingestion, storage, correlation and SOAR into independently scalable services.

See `docs/universal-log-pipeline.md`, `docs/parser-validation.md`, and `docs/implementation-roadmap.md`.
