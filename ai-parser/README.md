# AI Parser Engine

This service is responsible only for proposing parser specifications from unknown log templates.
It does not execute security actions and does not directly write validated parsers into production.

Flow:
1. Receive clustered unknown templates.
2. Ask the local LLM for a JSON parser specification.
3. Parser Validator tests the candidate.
4. Only validated candidates enter the parser registry.
