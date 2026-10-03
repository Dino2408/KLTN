import os, hashlib, time
import httpx
from fastapi import FastAPI
from pydantic import BaseModel

SHUFFLE_WEBHOOK_URL=os.getenv("SHUFFLE_WEBHOOK_URL","")
TIMEOUT=float(os.getenv("SOAR_TIMEOUT_SECONDS","15"))
api=FastAPI(title="SOAR Adapter",version="0.1.0")
ALLOWED={"PB-BRUTEFORCE-BLOCK-IP":"block_source_ip"}

class Action(BaseModel):
    playbook:str
    action:str
    source_ip:str|None=None
    signal_id:str|None=None
    idempotency_key:str
    approved:bool=False

@api.get("/health")
def health(): return {"status":"ok","service":"soar","shuffle_configured":bool(SHUFFLE_WEBHOOK_URL)}

@api.post("/v1/execute")
async def execute(a:Action):
    if a.playbook not in ALLOWED or ALLOWED[a.playbook]!=a.action:
        return {"executed":False,"status":"REJECTED","reason":"action_not_allowlisted"}
    if not a.source_ip:
        return {"executed":False,"status":"REJECTED","reason":"missing_source_ip"}
    if not a.approved:
        return {"executed":False,"status":"APPROVAL_REQUIRED","reason":"policy_not_approved"}
    if not SHUFFLE_WEBHOOK_URL:
        return {"executed":False,"status":"NOT_CONFIGURED","reason":"shuffle_webhook_missing"}
    payload={"playbook":a.playbook,"action":a.action,"source_ip":a.source_ip,
             "signal_id":a.signal_id,"idempotency_key":a.idempotency_key,
             "requested_at":time.time()}
    async with httpx.AsyncClient(timeout=TIMEOUT) as c:
        r=await c.post(SHUFFLE_WEBHOOK_URL,json=payload)
        return {"executed":r.is_success,"status":"DISPATCHED" if r.is_success else "FAILED",
                "http_status":r.status_code,"response":r.text[:1000]}
