from pydantic import BaseModel, Field
from typing import Any, Literal

class LogRecord(BaseModel):
    raw: str
    source: str = "unknown"
    timestamp: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class ParseField(BaseModel):
    source: str
    target: str
    type: Literal["string","integer","float","boolean","ip","datetime"] = "string"
    required: bool = False

class ParserSpec(BaseModel):
    parser_id: str
    version: str = "1.0.0"
    format: str
    fingerprint: str
    fields: list[ParseField]
    confidence: float = Field(ge=0, le=1)
    status: Literal["candidate","validated","rejected"] = "candidate"

class ParseResult(BaseModel):
    success: bool
    parser_id: str | None = None
    parser_version: str | None = None
    fields: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    confidence: float = 0
