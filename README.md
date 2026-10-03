# KLTN — AI-SIEM-SOAR

MVP for an AI-augmented SIEM/SOAR platform built by integrating open-source security tools.

## MVP stack

- Wazuh — SIEM / endpoint telemetry and detection
- Suricata — network IDS
- Ollama — local LLM runtime
- AI Gateway — event normalization, LLM analysis and policy validation
- Shuffle — SOAR orchestration and response playbooks

## Architecture

Wazuh / Suricata
        |
        v
   AI Gateway
        |
        v
     Ollama
        |
        v
 Schema validation
        |
        v
 Policy validation
        |
        v
 Approved Shuffle playbook
        |
        v
 Controlled response

The LLM does not receive arbitrary command execution privileges. Automated actions are restricted by an explicit policy allowlist.

## Repository structure

```
.
├── ai-gateway/
├── docs/
├── scripts/
├── suricata/
├── docker-compose.yml
├── .env.example
└── README.md
```

Docker Compose is used as the MVP orchestration layer for reproducible multi-container deployment. See the official Compose reference. 
