# Universal Log Pipeline

## Goal

The system is designed to accept heterogeneous security telemetry without requiring a pre-written parser for every vendor. It uses deterministic parsing for known templates and an isolated AI parser-generation path for unknown templates.

## Runtime contract

RAW LOG -> ingestion -> fingerprint/template -> parser registry -> deterministic parser OR AI parser candidate -> validation -> normalization -> enrichment -> correlation -> detection -> AI analysis -> policy -> SOAR.

## Unknown-format contract

An unknown template is never silently discarded. It is retained with its raw event, fingerprint and parser status. The AI parser generator proposes a parser specification; the validator must prove it against representative samples before the specification becomes active.

## Safety boundaries

- LLM never executes shell commands.
- LLM never directly invokes response actions.
- Parser candidates cannot become production parsers without deterministic validation.
- Raw events are retained for replay and parser reprocessing.
- Security actions require policy validation and explicit playbook allowlisting.

## Coverage definition

"Universal" means adaptive ingestion across heterogeneous and previously unseen templates within the supported transport/serialization envelope. It does not claim mathematical support for every possible proprietary format.
