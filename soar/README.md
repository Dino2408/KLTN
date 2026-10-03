# SOAR boundary

This directory will contain playbook contracts and adapters.

The policy engine is the only service allowed to approve automated response. The LLM never receives arbitrary shell execution privileges. Shuffle is an external executor/orchestrator behind an allowlisted playbook interface.
