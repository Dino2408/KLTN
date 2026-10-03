import re, hashlib
from collections import Counter
from fastapi import FastAPI
from pydantic import BaseModel, Field

api = FastAPI(title="Template Engine", version="0.1.0")
class Samples(BaseModel):
    logs: list[str] = Field(min_length=1, max_length=10000)

def template(s: str) -> str:
    s = re.sub(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F-]{27,}\b","<UUID>",s)
    s = re.sub(r"\b(?:\d{1,3}\.){3}\d{1,3}\b","<IP>",s)
    s = re.sub(r"\b(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}\b","<MAC>",s)
    s = re.sub(r"\b\d+\b","<NUM>",s)
    return re.sub(r"\s+"," ",s.strip())

@api.get("/health")
def health(): return {"status":"ok","service":"template-engine"}

@api.post("/v1/cluster")
def cluster(x: Samples):
    groups = {}
    for raw in x.logs:
        t = template(raw)
        fp = hashlib.sha256(t.encode()).hexdigest()[:24]
        groups.setdefault(fp, {"fingerprint":fp,"template":t,"samples":[]})
        if len(groups[fp]["samples"]) < 20: groups[fp]["samples"].append(raw)
    return {"clusters":list(groups.values()),"cluster_count":len(groups)}
