import os, time
import httpx
from fastapi import FastAPI
from pydantic import BaseModel

SHUFFLE_WEBHOOK_URL=os.getenv("SHUFFLE_WEBHOOK_URL","")
TIMEOUT=float(os.getenv("SOAR_TIMEOUT_SECONDS","15"))
DRY_RUN=os.getenv("SOAR_DRY_RUN","true").lower()=="true"
api=FastAPI(title="SOAR Adapter",version="0.2.0")
ALLOWED={"PB-BRUTEFORCE-BLOCK-IP":"block_source_ip"}

class Action(BaseModel):
    playbook:str
    action:str
    source_ip:str|None=None
    signal_id:str|None=None
    idempotency_key:str
    approved:bool=False

@api.get("/health")
def health():
    return {"status":"ok","service":"soar","shuffle_configured":bool(SHUFFLE_WEBHOOK_URL),"dry_run":DRY_RUN}

@api.post("/v1/execute")
async def execute(a:Action):
    if a.playbook not in ALLOWED or ALLOWED[a.playbook]!=a.action:
        return {"executed":False,"status":"REJECTED","reason":"action_not_allowlisted"}
    if not a.source_ip:
        return {"executed":False,"status":"REJECTED","reason":"missing_source_ip"}
    if not a.approved:
        return {"executed":False,"status":"APPROVAL_REQUIRED","reason":"policy_not_approved"}

    payload={"playbook":a.playbook,"action":a.action,"source_ip":a.source_ip,
             "signal_id":a.signal_id,"idempotency_key":a.idempotency_key,"requested_at":time.time()}

    if DRY_RUN:
        return {"executed":True,"status":"SIMULATED","mode":"dry-run","payload":payload}

    if not SHUFFLE_WEBHOOK_URL:
        return {"executed":False,"status":"NOT_CONFIGURED","reason":"shuffle_webhook_missing"}

    async with httpx.AsyncClient(timeout=TIMEOUT) as c:
        response=await c.post(SHUFFLE_WEBHOOK_URL,json=payload)
        return {"executed":response.is_success,
                "status":"DISPATCHED" if response.is_success else "FAILED",
                "http_status":response.status_code,"response":response.text[:1000]}
