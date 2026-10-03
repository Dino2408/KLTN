from datetime import datetime, timezone
from fastapi import FastAPI
from pydantic import BaseModel

api = FastAPI(title="Enrichment Engine", version="0.1.0")
class Event(BaseModel):
    event: dict

@api.get("/health")
def health(): return {"status":"ok","service":"enrichment"}

@api.post("/v1/enrich")
def enrich(x: Event):
    e = x.event
    e.setdefault("event", {})["enriched_at"] = datetime.now(timezone.utc).isoformat()
    tags = e.setdefault("tags", [])
    if e.get("source",{}).get("ip"): tags.append("has-source-ip")
    if e.get("destination",{}).get("ip"): tags.append("has-destination-ip")
    return e
