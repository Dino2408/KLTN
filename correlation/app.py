import os, time, json, hashlib
from collections import defaultdict
from datetime import datetime, timezone
import redis
from fastapi import FastAPI
from pydantic import BaseModel, Field

REDIS_URL=os.getenv("REDIS_URL","redis://event-bus:6379/0")
WINDOW_SECONDS=int(os.getenv("CORRELATION_WINDOW_SECONDS","300"))
THRESHOLD=int(os.getenv("REPEATED_SOURCE_THRESHOLD","5"))
r=redis.Redis.from_url(REDIS_URL,decode_responses=True)
api=FastAPI(title="Stateful Correlation Engine",version="0.2.0")

class EventBatch(BaseModel):
    events:list[dict]=Field(min_length=1,max_length=500)

def key_for(ip): return f"corr:src:{ip}"

@api.get("/health")
def health():
    r.ping()
    return {"status":"ok","service":"correlation","window_seconds":WINDOW_SECONDS}

@api.post("/v1/correlate")
def correlate(x:EventBatch):
    now=time.time(); buckets=defaultdict(list)
    for e in x.events:
        ip=e.get("source",{}).get("ip")
        if ip: buckets[ip].append(e)
    signals=[]
    for ip, events in buckets.items():
        key=key_for(ip)
        pipe=r.pipeline()
        for e in events:
            eid=e.get("event",{}).get("id") or hashlib.sha256(json.dumps(e,sort_keys=True).encode()).hexdigest()[:32]
            pipe.zadd(key,{json.dumps({"id":eid,"event":e},sort_keys=True):now})
        pipe.expire(key,WINDOW_SECONDS*2)
        pipe.execute()
        r.zremrangebyscore(key,0,now-WINDOW_SECONDS)
        count=r.zcard(key)
        if count>=THRESHOLD:
            members=r.zrange(key,max(0,count-50),-1)
            retained=[json.loads(m)["event"] for m in members]
            signals.append({"signal_id":hashlib.sha256(f"repeated-source:{ip}:{int(now)//WINDOW_SECONDS}".encode()).hexdigest()[:24],
                "signal_type":"repeated-source","source_ip":ip,"event_count":count,
                "window_seconds":WINDOW_SECONDS,"first_seen":datetime.fromtimestamp(now-WINDOW_SECONDS,tz=timezone.utc).isoformat(),
                "last_seen":datetime.now(timezone.utc).isoformat(),"events":retained})
    return {"signals":signals}
