from collections import defaultdict
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI
from pydantic import BaseModel, Field

api = FastAPI(title="Correlation Engine", version="0.1.0")
WINDOW = timedelta(minutes=5)
class Batch(BaseModel):
    events: list[dict] = Field(min_length=1, max_length=5000)

@api.get("/health")
def health(): return {"status":"ok","service":"correlation"}

@api.post("/v1/correlate")
def correlate(x: Batch):
    buckets = defaultdict(list)
    for e in x.events:
        ip = e.get("source",{}).get("ip")
        if ip: buckets[ip].append(e)
    signals = []
    for ip, events in buckets.items():
        if len(events) >= 5:
            signals.append({
                "signal_type":"repeated-source",
                "source_ip":ip,
                "event_count":len(events),
                "window":"5m",
                "events":events[:50]
            })
    return {"signals":signals}
