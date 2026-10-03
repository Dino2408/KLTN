import json, os
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel, Field

api = FastAPI(title="Audit Service", version="0.1.0")
AUDIT = Path(os.getenv("AUDIT_DIR","/app/audit"))
class Record(BaseModel):
    event_type: str
    payload: dict = Field(default_factory=dict)

@api.get("/health")
def health(): return {"status":"ok","service":"audit"}

@api.post("/v1/record")
def record(x: Record):
    AUDIT.mkdir(parents=True, exist_ok=True)
    item = {"timestamp":datetime.now(timezone.utc).isoformat(),**x.model_dump()}
    with (AUDIT/"events.jsonl").open("a") as f:
        f.write(json.dumps(item,separators=(",",":"))+"\n")
    return {"recorded":True,"timestamp":item["timestamp"]}
