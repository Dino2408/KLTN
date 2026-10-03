import re
from datetime import datetime, timezone
from .models import ParserSpec, ParseResult

def _convert(value: str, kind: str):
    if kind == "integer": return int(value)
    if kind == "float": return float(value)
    if kind == "boolean": return value.lower() in {"1","true","yes","on"}
    if kind == "ip":
        parts = value.split(".")
        if len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
            return value
        raise ValueError("invalid IPv4")
    if kind == "datetime":
        return value
    return value

def parse(raw: str, spec: ParserSpec) -> ParseResult:
    values = {}
    errors = []
    for field in spec.fields:
        if field.source.startswith("kv:"):
            key = field.source[3:]
            m = re.search(rf"\b{re.escape(key)}=([^\s]+)", raw)
            if not m:
                if field.required: errors.append(f"missing:{key}")
                continue
            value = m.group(1)
        elif field.source.startswith("regex:"):
            m = re.search(field.source[6:], raw)
            if not m:
                if field.required: errors.append(f"regex_miss:{field.target}")
                continue
            value = m.group(1) if m.groups() else m.group(0)
        else:
            errors.append(f"unsupported_source:{field.source}")
            continue
        try:
            values[field.target] = _convert(value, field.type)
        except Exception as exc:
            errors.append(f"conversion:{field.target}:{exc}")
    ok = not errors
    return ParseResult(
        success=ok,
        parser_id=spec.parser_id,
        parser_version=spec.version,
        fields=values,
        errors=errors,
        confidence=spec.confidence if ok else 0
    )
