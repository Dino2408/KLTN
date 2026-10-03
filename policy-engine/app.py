from fastapi import FastAPI
from pydantic import BaseModel

api = FastAPI(title="Policy Engine", version="0.1.0")
ALLOWED = {"PB-BRUTEFORCE-BLOCK-IP": "block_source_ip"}

class Decision(BaseModel):
    playbook: str
    action: str
    confidence: float
    severity: str
    source_ip: str | None = None

@api.get("/health")
def health(): return {"status":"ok","service":"policy-engine"}

@api.post("/v1/evaluate")
def evaluate(d: Decision):
    allowed = (
        d.playbook in ALLOWED and
        ALLOWED[d.playbook] == d.action and
        d.confidence >= 0.90 and
        d.severity != "critical" and
        bool(d.source_ip)
    )
    return {
        "allowed": allowed,
        "requires_approval": not allowed,
        "reason": "policy_match" if allowed else "policy_gate",
        "playbook": d.playbook,
        "action": d.action
    }
