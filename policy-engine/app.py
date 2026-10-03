import os, time, hashlib
import redis
from fastapi import FastAPI
from pydantic import BaseModel, Field

REDIS_URL=os.getenv("REDIS_URL","redis://event-bus:6379/0")
MIN_CONFIDENCE=float(os.getenv("MIN_AUTOMATION_CONFIDENCE","0.90"))
RATE_LIMIT=int(os.getenv("ACTION_RATE_LIMIT","20"))
RATE_WINDOW=int(os.getenv("ACTION_RATE_WINDOW_SECONDS","300"))
r=redis.Redis.from_url(REDIS_URL,decode_responses=True)
api=FastAPI(title="Policy Engine",version="0.2.0")
POLICIES={"PB-BRUTEFORCE-BLOCK-IP":{"version":"1.0.0","action":"block_source_ip","approval":"auto","max_severity":"high"}}

class Decision(BaseModel):
    playbook:str
    action:str
    confidence:float=Field(ge=0,le=1)
    severity:str
    source_ip:str|None=None
    signal_id:str|None=None
    analyst_approved:bool=False

@api.get("/health")
def health(): r.ping(); return {"status":"ok","service":"policy-engine"}

@api.post("/v1/evaluate")
def evaluate(d:Decision):
    policy=POLICIES.get(d.playbook)
    reasons=[]
    if not policy: reasons.append("unknown_playbook")
    if policy and d.action!=policy["action"]: reasons.append("action_mismatch")
    if d.confidence<MIN_CONFIDENCE: reasons.append("confidence_below_threshold")
    if d.severity.lower()=="critical": reasons.append("critical_requires_approval")
    if not d.source_ip: reasons.append("missing_source_ip")
    idem=hashlib.sha256(f"{d.playbook}|{d.action}|{d.source_ip}|{d.signal_id}".encode()).hexdigest()
    if r.get(f"action:done:{idem}"): reasons.append("already_executed")
    if not reasons:
        bucket=f"rate:{d.playbook}:{int(time.time())//RATE_WINDOW}"
        count=int(r.incr(bucket)); r.expire(bucket,RATE_WINDOW+5)
        if count>RATE_LIMIT: reasons.append("rate_limit_exceeded")
    auto=not reasons
    if d.analyst_approved and policy and d.source_ip and d.action==policy["action"] and "already_executed" not in reasons:
        auto=True
    return {"allowed":auto,"requires_approval":not auto,"policy_version":policy["version"] if policy else None,
            "reasons":reasons or ["policy_match"],"idempotency_key":idem,"action":d.action,"playbook":d.playbook}

@api.post("/v1/mark-executed")
def mark_executed(payload:dict):
    key=payload.get("idempotency_key")
    if not key: return {"marked":False,"reason":"missing_idempotency_key"}
    r.setex(f"action:done:{key}",86400,"1")
    return {"marked":True}
