# MVP Architecture

## Data flow

Wazuh / Suricata
  -> AI Gateway
  -> Ollama
  -> structured decision validation
  -> policy validation
  -> approved Shuffle playbook
  -> controlled response

## Security boundary

The LLM has no Docker socket, SSH credentials or arbitrary command execution interface.

The AI Gateway is read-only and uses no-new-privileges.

Only explicitly allowlisted playbooks can be automated. Critical events remain approval-gated.

Wazuh and Shuffle are consumed from their upstream deployment repositories rather than copied into this repository.
