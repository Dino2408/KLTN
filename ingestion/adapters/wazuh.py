import json

def adapt(payload: str) -> dict:
    obj = json.loads(payload)
    return {
        "raw": payload,
        "source": "wazuh",
        "transport": "wazuh",
        "metadata": {
            "rule_id": obj.get("rule", {}).get("id"),
            "agent_id": obj.get("agent", {}).get("id"),
            "agent_name": obj.get("agent", {}).get("name")
        }
    }
