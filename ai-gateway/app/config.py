import os

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434").rstrip("/")
AI_MODEL = os.getenv("AI_MODEL", "qwen2.5-coder:7b")
AI_MAX_EVENTS = int(os.getenv("AI_MAX_EVENTS", "50"))
AI_CONFIDENCE_THRESHOLD = float(os.getenv("AI_CONFIDENCE_THRESHOLD", "0.90"))
