# Universal Ingestion

Adapters normalize transport metadata into a common envelope without deciding whether a log is malicious.

Supported foundation:
- HTTP JSON/plaintext
- file tailing
- Syslog TCP/UDP design
- Wazuh adapter
- Suricata EVE adapter

All adapters preserve the raw event and attach source/transport metadata.
