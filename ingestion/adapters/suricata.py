import json

def adapt(payload: str) -> dict:
    obj = json.loads(payload)
    return {
        "raw": payload,
        "source": "suricata",
        "transport": "eve-json",
        "metadata": {
            "event_type": obj.get("event_type"),
            "signature_id": obj.get("alert", {}).get("signature_id"),
            "signature": obj.get("alert", {}).get("signature")
        }
    }
