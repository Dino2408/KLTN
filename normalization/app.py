from datetime import datetime, timezone
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Normalization Engine", version="0.1.0")

class NormalizeRequest(BaseModel):
    raw: str
    parsed: dict = Field(default_factory=dict)
    parser_id: str | None = None
    parser_confidence: float = 0

def normalize(x: NormalizeRequest) -> dict:
    p = x.parsed
    event = {
        "@timestamp": p.get("timestamp") or datetime.now(timezone.utc).isoformat(),
        "event": {
            "kind": "event",
            "category": ["network"] if any(k in p for k in ("src_ip","dst_ip")) else ["generic"],
            "original": x.raw
        },
        "ai_siem": {
            "parser_id": x.parser_id,
            "parser_confidence": x.parser_confidence
        }
    }
    mappings = {
        "src_ip": ("source","ip"), "dst_ip": ("destination","ip"),
        "src_port": ("source","port"), "dst_port": ("destination","port"),
        "action": ("event","action"), "result": ("event","outcome"),
        "user": ("user","name"), "process": ("process","name")
    }
    for src, (obj,key) in mappings.items():
        if src in p:
            event.setdefault(obj, {})[key] = p[src]
    return event

@app.get("/health")
def health(): return {"status":"ok","service":"normalization"}

@app.post("/v1/normalize")
def normalize_endpoint(x: NormalizeRequest):
    return normalize(x)
