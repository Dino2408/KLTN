import asyncio, json, os
from datetime import datetime, timezone
import httpx
import redis.asyncio as redis
from fastapi import FastAPI
from pydantic import BaseModel

PARSER=os.getenv("PARSER_URL","http://parser-engine:8000"); AIPARSER=os.getenv("AI_PARSER_URL","http://ai-parser:8090")
NORMALIZER=os.getenv("NORMALIZER_URL","http://normalization:8091"); VALIDATOR=os.getenv("VALIDATOR_URL","http://parser-validator:8092")
ENRICHMENT=os.getenv("ENRICHMENT_URL","http://enrichment:8000"); AUDIT=os.getenv("AUDIT_URL","http://audit:8000")
REDIS_URL=os.getenv("REDIS_URL","redis://event-bus:6379/0"); EVENT_STREAM=os.getenv("EVENT_STREAM","siem:events")
CONSUMER_GROUP=os.getenv("CONSUMER_GROUP","pipeline"); CONSUMER_NAME=os.getenv("CONSUMER_NAME","pipeline-1"); DLQ_STREAM=os.getenv("DLQ_STREAM","siem:dlq")

api=FastAPI(title="Universal Log Pipeline",version="0.3.0")
rdb=None; consumer_task=None

class Ingest(BaseModel):
    raw:str; source:str="unknown"; received_at:str|None=None

async def audit(c,event_type,payload):
    try: await c.post(f"{AUDIT}/v1/record",json={"event_type":event_type,"payload":payload})
    except Exception: pass

async def process_event(x:Ingest):
    received=x.received_at or datetime.now(timezone.utc).isoformat()
    async with httpx.AsyncClient(timeout=120) as c:
        inspected=(await c.post(f"{PARSER}/v1/inspect",json=x.model_dump())).json()
        if not inspected["parser_found"]:
            ai=(await c.post(f"{AIPARSER}/v1/generate",json={"examples":[x.raw]})).json()
            validation=(await c.post(f"{VALIDATOR}/v1/validate",json={"parser":ai,"samples":[x.raw]})).json()
            if validation["status"]!="validated":
                await audit(c,"unknown_parser",{"source":x.source,"fingerprint":inspected["fingerprint"],"raw":x.raw})
                return {"status":"UNKNOWN_FORMAT_REQUIRES_REVIEW","inspection":inspected,"validation":validation}
        parsed=(await c.post(f"{PARSER}/v1/parse",json=x.model_dump())).json()
        if parsed.get("status")=="UNKNOWN_FORMAT": return {"status":"UNKNOWN_FORMAT_REQUIRES_REVIEW","parsed":parsed}
        normalized=(await c.post(f"{NORMALIZER}/v1/normalize",json={"raw":x.raw,"parsed":parsed.get("fields",{}),"parser_id":parsed.get("parser_id"),"parser_confidence":parsed.get("confidence",0)})).json()
        normalized.setdefault("event",{})["created"]=received
        enriched=(await c.post(f"{ENRICHMENT}/v1/enrich",json={"event":normalized})).json()
        await audit(c,"normalized_event",{"event":enriched})
        return {"status":"PROCESSED","parsed":parsed,"normalized":enriched}

async def ensure_group():
    try: await rdb.xgroup_create(EVENT_STREAM,CONSUMER_GROUP,id="0",mkstream=True)
    except Exception as e:
        if "BUSYGROUP" not in str(e): raise

async def consume():
    await ensure_group()
    while True:
        try:
            rows=await rdb.xreadgroup(CONSUMER_GROUP,CONSUMER_NAME,{EVENT_STREAM:">"},count=10,block=5000)
            for _,messages in rows:
                for msg_id,fields in messages:
                    try:
                        result=await process_event(Ingest(**json.loads(fields["payload"])))
                        if result.get("status")=="UNKNOWN_FORMAT_REQUIRES_REVIEW":
                            await rdb.xadd(DLQ_STREAM,{"payload":fields["payload"],"reason":"unknown_format"},maxlen=100000,approximate=True)
                        await rdb.xack(EVENT_STREAM,CONSUMER_GROUP,msg_id)
                    except Exception as exc:
                        await rdb.xadd(DLQ_STREAM,{"payload":fields.get("payload","{}"),"reason":str(exc)[:1000]},maxlen=100000,approximate=True)
                        await rdb.xack(EVENT_STREAM,CONSUMER_GROUP,msg_id)
        except asyncio.CancelledError: raise
        except Exception: await asyncio.sleep(2)

@api.on_event("startup")
async def startup():
    global rdb,consumer_task
    rdb=redis.from_url(REDIS_URL,decode_responses=True); await rdb.ping()
    consumer_task=asyncio.create_task(consume())

@api.on_event("shutdown")
async def shutdown():
    if consumer_task: consumer_task.cancel()
    if rdb: await rdb.aclose()

@api.get("/health")
async def health(): await rdb.ping(); return {"status":"ok","service":"universal-log-pipeline","stream":EVENT_STREAM}

@api.post("/v1/process")
async def process(x:Ingest): return await process_event(x)

@api.get("/v1/queue")
async def queue_info(): return {"stream_length":await rdb.xlen(EVENT_STREAM),"dlq_length":await rdb.xlen(DLQ_STREAM)}

@api.post("/v1/replay")
async def replay(limit:int=100):
    rows=await rdb.xrange(DLQ_STREAM,count=max(1,min(limit,1000))); replayed=0
    for msg_id,fields in rows:
        await rdb.xadd(EVENT_STREAM,{"payload":fields.get("payload","{}")},maxlen=100000,approximate=True)
        await rdb.xdel(DLQ_STREAM,msg_id); replayed+=1
    return {"replayed":replayed,"remaining_dlq":await rdb.xlen(DLQ_STREAM)}
