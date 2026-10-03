import re

DEFAULT_START = re.compile(r"^(?:\d{4}-\d{2}-\d{2}|[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}|\{)")

def assemble(lines: list[str], start_pattern: str | None = None) -> list[str]:
    pattern = re.compile(start_pattern) if start_pattern else DEFAULT_START
    events, current = [], []
    for line in lines:
        if pattern.search(line):
            if current: events.append("\n".join(current))
            current = [line.rstrip("\n")]
        elif current:
            current.append(line.rstrip("\n"))
        else:
            events.append(line.rstrip("\n"))
    if current: events.append("\n".join(current))
    return events
