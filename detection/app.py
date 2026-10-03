from fastapi import FastAPI
from pydantic import BaseModel

api = FastAPI(title="Detection Engine", version="0.1.0")
class Signal(BaseModel):
    signal_type: str
    source_ip: str | None = None
    event_count: int = 0
    window: str = "5m"

@api.get("/health")
def health(): return {"status":"ok","service":"detection"}

@api.post("/v1/detect")
def detect(s: Signal):
    severity = "medium" if s.event_count < 20 else "high"
    return {
        "detected": True,
        "rule_id": "CORR-REPEATED-SOURCE",
        "severity": severity,
        "source_ip": s.source_ip,
        "evidence_count": s.event_count,
        "confidence": min(0.99, 0.70 + s.event_count / 100)
    }
