import os, httpx
from fastapi import FastAPI
from pydantic import BaseModel

PARSER = os.getenv("PARSER_URL","http://parser-engine:8000")
AIPARSER = os.getenv("AI_PARSER_URL","http://ai-parser:8090")
NORMALIZER = os.getenv("NORMALIZER_URL","http://normalization:8091")
VALIDATOR = os.getenv("VALIDATOR_URL","http://parser-validator:8092")

api = FastAPI(title="Universal Log Pipeline", version="0.1.0")

class Ingest(BaseModel):
    raw: str
    source: str = "unknown"

@api.get("/health")
def health(): return {"status":"ok","service":"universal-log-pipeline"}

@api.post("/v1/ingest")
async def ingest(x: Ingest):
    async with httpx.AsyncClient(timeout=120) as c:
        inspected = (await c.post(f"{PARSER}/v1/inspect", json=x.model_dump())).json()
        if not inspected["parser_found"]:
            ai = (await c.post(f"{AIPARSER}/v1/generate", json={"examples":[x.raw]})).json()
            validation = (await c.post(f"{VALIDATOR}/v1/validate", json={"parser":ai,"samples":[x.raw]})).json()
            if validation["status"] != "validated":
                return {"status":"UNKNOWN_FORMAT_REQUIRES_REVIEW","inspection":inspected,"validation":validation}
        parsed = (await c.post(f"{PARSER}/v1/parse", json=x.model_dump())).json()
        if parsed.get("status") == "UNKNOWN_FORMAT":
            return {"status":"UNKNOWN_FORMAT_REQUIRES_REVIEW","parsed":parsed}
        normalized = (await c.post(f"{NORMALIZER}/v1/normalize", json={
            "raw":x.raw, "parsed":parsed.get("fields",{}),
            "parser_id":parsed.get("parser_id"),
            "parser_confidence":parsed.get("confidence",0)
        })).json()
        return {"status":"NORMALIZED","parsed":parsed,"normalized":normalized}
