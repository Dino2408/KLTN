import os, json
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel, Field
from app import generate
from parser_engine_compat import fingerprint

api = FastAPI(title="AI Adaptive Parser", version="0.1.0")
PARSER_DIR = Path(os.getenv("PARSER_DIR", "/app/parsers"))

class GenerateRequest(BaseModel):
    examples: list[str] = Field(min_length=1, max_length=100)

@api.get("/health")
def health():
    return {"status": "ok", "service": "ai-parser"}

@api.post("/v1/generate")
async def generate_parser(req: GenerateRequest):
    fp = fingerprint(req.examples[0])
    candidate = await generate(req.examples)
    candidate.update({
        "parser_id": f"ai-{fp}",
        "fingerprint": fp,
        "version": "0.1.0",
        "confidence": 0.0,
        "status": "candidate"
    })
    return candidate
