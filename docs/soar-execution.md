# SOAR execution boundary

The SOAR adapter is the only service that dispatches an approved response to an external executor such as Shuffle.

The adapter enforces:
- playbook/action allowlisting;
- source-IP presence for the current blocking action;
- explicit approval from the policy layer;
- configured Shuffle webhook;
- idempotency key propagation.

The LLM cannot call this service directly with arbitrary actions. A future production implementation should add signed service-to-service authentication, webhook secret validation, retry policy, circuit breaking and immutable execution receipts before exposing the executor outside the internal network.
