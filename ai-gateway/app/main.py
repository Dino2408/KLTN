from fastapi import FastAPI, HTTPException

from .config import AI_MODEL, AI_MAX_EVENTS
from .llm import analyze
from .policy import apply_policy
from .schemas import AnalyzeRequest, AnalyzeResponse

app = FastAPI(title="AI-SIEM-SOAR AI Gateway", version="0.1.0")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "ai-gateway", "model": AI_MODEL}

@app.post("/api/v1/analyze", response_model=AnalyzeResponse)
async def analyze_events(request: AnalyzeRequest):
    if len(request.events) > AI_MAX_EVENTS:
        raise HTTPException(
            status_code=413,
            detail=f"Too many events. Maximum is {AI_MAX_EVENTS}."
        )

    decision = await analyze([event.model_dump() for event in request.events])
    allowed = apply_policy(decision)

    return AnalyzeResponse(
        decision=decision,
        model=AI_MODEL,
        event_count=len(request.events),
        automation_allowed=allowed
    )
