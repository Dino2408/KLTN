import os, json
from pathlib import Path
import httpx
from parser_engine_compat import fingerprint

OLLAMA = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
MODEL = os.getenv("AI_MODEL", "qwen2.5-coder:7b")
PARSER_DIR = Path(os.getenv("PARSER_DIR", "/app/parsers"))

SYSTEM = """You are an adaptive security-log parser generator.
Return ONLY JSON matching:
{"format": "...", "fields":[{"source":"kv:key|regex:(capture regex)","target":"ECS path","type":"string|integer|float|boolean|ip|datetime","required":false}]}
Never invent values. Infer mappings only from the supplied examples. Prefer kv: sources when the log is key=value.
"""

async def generate(examples: list[str]) -> dict:
    prompt = SYSTEM + "\nExamples:\n" + "\n".join(examples)
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(f"{OLLAMA}/api/chat", json={
            "model": MODEL,
            "messages":[{"role":"system","content":SYSTEM},{"role":"user","content":prompt}],
            "stream":False, "format":"json",
            "options":{"temperature":0}
        })
        r.raise_for_status()
        return json.loads(r.json()["message"]["content"])

def parser_path(fp: str) -> Path:
    return PARSER_DIR / f"{fp}.json"
