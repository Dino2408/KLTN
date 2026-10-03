from fastapi import FastAPI
from .fingerprint import fingerprint, templateize
from .models import LogRecord, ParseResult
from .registry import ParserRegistry
from .runtime import parse

app = FastAPI(title="Universal Parser Engine", version="0.1.0")
registry = ParserRegistry("/app/parsers")

@app.get("/health")
def health():
    return {"status": "ok", "service": "parser-engine"}

@app.post("/v1/inspect")
def inspect(record: LogRecord):
    fp = fingerprint(record.raw)
    return {"fingerprint": fp, "template": templateize(record.raw), "parser_found": registry.get(fp) is not None}

@app.post("/v1/parse")
def parse_log(record: LogRecord):
    fp = fingerprint(record.raw)
    spec = registry.get(fp)
    if not spec:
        return {"status": "UNKNOWN_FORMAT", "fingerprint": fp, "template": templateize(record.raw)}
    return parse(record.raw, spec).model_dump()
