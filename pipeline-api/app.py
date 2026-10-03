import os, httpx
from datetime import datetime, timezone
from fastapi import FastAPI
from pydantic import BaseModel

PARSER = os.getenv("PARSER_URL","http://parser-engine:8000")
AIPARSER = os.getenv("AI_PARSER_URL","http://ai-parser:8090")
NORMALIZER = os.getenv("NORMALIZER_URL","http://normalization:8091")
VALIDATOR = os.getenv("VALIDATOR_URL","http://parser-validator:8092")
ENRICHMENT = os.getenv("ENRICHMENT_URL","http://enrichment:8000")
CORRELATION = os.getenv("CORRELATION_URL","http://correlation:8000")
DETECTION = os.getenv("DETECTION_URL","http://detection:8000")
AUDIT = os.getenv("AUDIT_URL","http://audit:8000")

api = FastAPI(title="Universal Log Pipeline", version="0.2.0")

class Ingest(BaseModel):
    raw: str
    source: str = "unknown"
    received_at: str | None = None

@api.get("/health")
def health(): return {"status":"ok","service":"universal-log-pipeline"}

@api.post("/v1/process")
async def process(x: Ingest):
    received = x.received_at or datetime.now(timezone.utc).isoformat()
    async with httpx.AsyncClient(timeout=120) as c:
        inspected = (await c.post(f"{PARSER}/v1/inspect", json=x.model_dump())).json()
        if not inspected["parser_found"]:
            ai = (await c.post(f"{AIPARSER}/v1/generate", json={"examples":[x.raw]})).json()
            validation = (await c.post(f"{VALIDATOR}/v1/validate", json={"parser":ai,"samples":[x.raw]})).json()
            if validation["status"] != "validated":
                await c.post(f"{AUDIT}/v1/record", json={"event_type":"unknown_parser","payload":{"source":x.source,"fingerprint":inspected["fingerprint"],"raw":x.raw}})
                return {"status":"UNKNOWN_FORMAT_REQUIRES_REVIEW","inspection":inspected,"validation":validation}
        parsed = (await c.post(f"{PARSER}/v1/parse", json=x.model_dump())).json()
        if parsed.get("status") == "UNKNOWN_FORMAT":
            return {"status":"UNKNOWN_FORMAT_REQUIRES_REVIEW","parsed":parsed}
        normalized = (await c.post(f"{NORMALIZER}/v1/normalize", json={
            "raw":x.raw,"parsed":parsed.get("fields",{}),
            "parser_id":parsed.get("parser_id"),
            "parser_confidence":parsed.get("confidence",0)
        })).json()
        normalized.setdefault("event",{})["created"] = received
        enriched = (await c.post(f"{ENRICHMENT}/v1/enrich", json={"event":normalized})).json()
        await c.post(f"{AUDIT}/v1/record", json={"event_type":"normalized_event","payload":{"event":enriched}})
        return {"status":"PROCESSED","parsed":parsed,"normalized":enriched}

@api.post("/v1/correlate")
async def correlate(events: list[dict]):
    async with httpx.AsyncClient(timeout=120) as c:
        return (await c.post(f"{CORRELATION}/v1/correlate", json={"events":events})).json()

@api.post("/v1/detect")
async def detect(signal: dict):
    async with httpx.AsyncClient(timeout=120) as c:
        return (await c.post(f"{DETECTION}/v1/detect", json=signal)).json()
