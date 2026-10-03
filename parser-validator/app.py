import json, os, shutil
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel, Field
import re

api = FastAPI(title="Parser Validator", version="0.1.0")
ACTIVE = Path(os.getenv("ACTIVE_DIR","/app/active"))
CANDIDATES = Path(os.getenv("CANDIDATE_DIR","/app/candidates"))
THRESHOLD = float(os.getenv("PARSER_VALIDATION_THRESHOLD","0.95"))

class ValidationRequest(BaseModel):
    parser: dict
    samples: list[str] = Field(min_length=1, max_length=100)

def parse_sample(raw: str, spec: dict):
    values, errors = {}, []
    for f in spec.get("fields", []):
        source = f.get("source","")
        m = None
        if source.startswith("kv:"):
            key = re.escape(source[3:])
            m = re.search(rf"\\b{key}=([^\\s]+)", raw)
        elif source.startswith("regex:"):
            m = re.search(source[6:], raw)
        if not m:
            if f.get("required"): errors.append(f"missing:{f.get('target')}")
            continue
        values[f["target"]] = m.group(1) if m.groups() else m.group(0)
    return values, errors

@api.get("/health")
def health(): return {"status":"ok","service":"parser-validator"}

@api.post("/v1/validate")
def validate(req: ValidationRequest):
    successes = 0
    required_hits = 0
    total_required = sum(1 for f in req.parser.get("fields",[]) if f.get("required"))
    for sample in req.samples:
        vals, errors = parse_sample(sample, req.parser)
        if not errors: successes += 1
        if total_required:
            required_hits += sum(1 for f in req.parser.get("fields",[]) if f.get("required") and f["target"] in vals)
        else:
            required_hits += 1
    rate = successes / len(req.samples)
    req.parser["confidence"] = round(rate,4)
    req.parser["status"] = "validated" if rate >= THRESHOLD else "rejected"
    if req.parser["status"] == "validated":
        ACTIVE.mkdir(parents=True, exist_ok=True)
        (ACTIVE / f'{req.parser["fingerprint"]}.json').write_text(json.dumps(req.parser,indent=2))
    else:
        CANDIDATES.mkdir(parents=True, exist_ok=True)
        (CANDIDATES / f'{req.parser["fingerprint"]}.json').write_text(json.dumps(req.parser,indent=2))
    return {"status": req.parser["status"], "confidence": rate, "sample_count": len(req.samples), "parser": req.parser}
