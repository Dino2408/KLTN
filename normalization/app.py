from datetime import datetime, timezone
from hashlib import sha256
from fastapi import FastAPI
from pydantic import BaseModel, Field

api = FastAPI(title="Normalization Engine", version="0.2.0")

class NormalizeRequest(BaseModel):
    raw: str
    parsed: dict = Field(default_factory=dict)
    parser_id: str | None = None
    parser_confidence: float = 0

def put(root: dict, path: str, value):
    parts = path.split(".")
    cur = root
    for p in parts[:-1]:
        cur = cur.setdefault(p, {})
    cur[parts[-1]] = value

def normalize(x: NormalizeRequest) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    p = x.parsed
    original = x.raw
    event_id = sha256(original.encode()).hexdigest()[:32]
    ts = p.get("timestamp") or now
    e = {
        "@timestamp": ts,
        "message": original,
        "event": {
            "id": event_id,
            "kind": "event",
            "created": now,
            "ingested": now,
            "original": original
        },
        "ecs": {"version": "8.x-compatible-mapping"},
        "ai_siem": {
            "parser_id": x.parser_id,
            "parser_confidence": x.parser_confidence
        }
    }
    mappings = {
        "src_ip":"source.ip", "dst_ip":"destination.ip",
        "src_port":"source.port", "dst_port":"destination.port",
        "action":"event.action", "result":"event.outcome",
        "user":"user.name", "process":"process.name",
        "severity":"event.severity", "rule_id":"rule.id",
        "service":"service.name", "hostname":"host.name"
    }
    for src,target in mappings.items():
        if src in p: put(e,target,p[src])
    if "src_ip" in p or "dst_ip" in p:
        e["event"]["category"] = ["network"]
    elif "process" in p:
        e["event"]["category"] = ["process"]
    else:
        e["event"]["category"] = ["generic"]
    return e

@api.get("/health")
def health(): return {"status":"ok","service":"normalization"}

@api.post("/v1/normalize")
def normalize_endpoint(x: NormalizeRequest): return normalize(x)
