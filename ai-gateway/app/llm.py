import json
import httpx

from .config import OLLAMA_BASE_URL, AI_MODEL
from .schemas import Decision

SYSTEM_PROMPT = """You are a SOC triage assistant.
Return ONLY JSON matching the requested schema.
Do not invent evidence.
Do not output shell commands or executable code.
Recommend only an approved playbook when evidence supports it.
"""

async def analyze(events: list[dict]) -> Decision:
    prompt = {
        "task": "triage_security_events",
        "events": events,
        "schema": {
            "classification": "string",
            "severity": "low|medium|high|critical",
            "confidence": "number 0..1",
            "playbook": "string|null",
            "action": "string|null",
            "requires_approval": "boolean",
            "reasoning_summary": "string",
            "observables": ["string"],
            "mitre_techniques": ["string"]
        }
    }

    async with httpx.AsyncClient(timeout=180) as client:
        response = await client.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": AI_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)}
                ],
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.1}
            }
        )
        response.raise_for_status()
        return Decision.model_validate_json(response.json()["message"]["content"])
