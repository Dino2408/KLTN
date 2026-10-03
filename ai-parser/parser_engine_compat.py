import hashlib, re
def fingerprint(raw: str) -> str:
    s = re.sub(r"\s+", " ", raw.strip())
    s = re.sub(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "<IP>", s)
    s = re.sub(r"\b\d+\b", "<NUM>", s)
    return hashlib.sha256(s.encode()).hexdigest()[:24]
