import os, json, httpx
from fastapi import FastAPI
from pydantic import BaseModel, Field

OLLAMA=os.getenv("OLLAMA_BASE_URL","http://ollama:11434")
MODEL=os.getenv("AI_MODEL","qwen2.5-coder:7b")
api=FastAPI(title="AI Security Analysis",version="0.1.0")

class Signal(BaseModel):
    signal_id:str
    signal_type:str
    severity:str="medium"
    confidence:float=Field(ge=0,le=1)
    source_ip:str|None=None
    events:list[dict]=Field(default_factory=list)

SYSTEM="""You are a SOC analyst. Analyze only evidence supplied in the signal.
Return JSON only with: classification, severity, confidence, summary, evidence,
mitre_techniques, recommended_playbook, recommended_action, requires_approval.
Never invent observables. Never execute commands. Never request arbitrary shell
execution. Recommended actions are proposals; policy-engine is the only authority
that can approve automation."""

@api.get("/health")
async def health(): return {"status":"ok","service":"ai-analysis","model":MODEL}

@api.post("/v1/analyze")
async def analyze(signal:Signal):
    prompt=SYSTEM+"\nSIGNAL:\n"+json.dumps(signal.model_dump(),ensure_ascii=False)
    async with httpx.AsyncClient(timeout=120) as c:
        resp=await c.post(f"{OLLAMA}/api/chat",json={"model":MODEL,"messages":[{"role":"system","content":SYSTEM},{"role":"user","content":prompt}],"stream":False,"format":"json","options":{"temperature":0.1}})
        resp.raise_for_status()
        raw=resp.json()["message"]["content"]
    result=json.loads(raw)
    result["signal_id"]=signal.signal_id
    result["source_ip"]=signal.source_ip
    result["requires_approval"]=True if signal.severity.lower()=="critical" else result.get("requires_approval",True)
    return result
