import hashlib, re
IP = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
HEX = re.compile(r"\b0x[0-9a-fA-F]+\b")
NUM = re.compile(r"\b\d+\b")
UUID = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F-]{27,}\b")

def fingerprint(raw: str) -> str:
    s = raw.strip()
    s = UUID.sub("<UUID>", s)
    s = IP.sub("<IP>", s)
    s = HEX.sub("<HEX>", s)
    s = NUM.sub("<NUM>", s)
    s = re.sub(r"\s+", " ", s)
    return hashlib.sha256(s.encode()).hexdigest()[:24]
