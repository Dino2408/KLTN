from datetime import datetime, timezone
from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Any

api = FastAPI(title="Universal Ingestion", version="0.1.0")

class Envelope(BaseModel):
    raw: str
    source: str = "unknown"
    transport: str = "http"
    received_at: str | None = None
    metadata: dict[str, Any] = {}

@api.get("/health")
def health(): return {"status":"ok","service":"ingestion"}

@api.post("/v1/events")
async def receive(event: Envelope):
    event.received_at = event.received_at or datetime.now(timezone.utc).isoformat()
    return {"accepted": True, "event": event.model_dump()}
