import asyncio, json, os
from datetime import datetime, timezone
import httpx
import redis.asyncio as redis
from fastapi import FastAPI
from pydantic import BaseModel

PARSER=os.getenv("PARSER_URL","http://parser-engine:8000")
AIPARSER=os.getenv("AI_PARSER_URL","http://ai-parser:8090")
NORMALIZER=os.getenv("NORMALIZER_URL","http://normalization:8091")
VALIDATOR=os.getenv("VALIDATOR_URL","http://parser-validator:8092")
ENRICHMENT=os.getenv("ENRICHMENT_URL","http://enrichment:8000")
CORRELATION=os.getenv("CORRELATION_URL","http://correlation:8000")
DETECTION=os.getenv("DETECTION_URL","http://detection:8000")
AI_ANALYSIS=os.getenv("AI_ANALYSIS_URL","http://ai-analysis:8094")
POLICY=os.getenv("POLICY_URL","http://policy-engine:8000")
SOAR=os.getenv("SOAR_URL","http://soar:8095")
AUDIT=os.getenv("AUDIT_URL","http://audit:8000")
REDIS_URL=os.getenv("REDIS_URL","redis://event-bus:6379/0")
EVENT_STREAM=os.getenv("EVENT_STREAM","siem:events")
CONSUMER_GROUP=os.getenv("CONSUMER_GROUP","pipeline")
CONSUMER_NAME=os.getenv("CONSUMER_NAME","pipeline-1")
DLQ_STREAM=os.getenv("DLQ_STREAM","siem:dlq")

api=FastAPI(title="Universal Log Pipeline",version="0.4.0")
rdb=None
consumer_task=None

class Ingest(BaseModel):
    raw:str
    source:str="unknown"
    received_at:str|None=None

async def audit(c,event_type,payload):
    response=await c.post(f"{AUDIT}/v1/record",json={"event_type":event_type,"payload":payload})
    response.raise_for_status()

async def process_event(x:Ingest):
    received=x.received_at or datetime.now(timezone.utc).isoformat()
    async with httpx.AsyncClient(timeout=120) as c:
        inspected=(await c.post(f"{PARSER}/v1/inspect",json=x.model_dump())).json()
        if not inspected["parser_found"]:
            ai=(await c.post(f"{AIPARSER}/v1/generate",json={"examples":[x.raw]})).json()
            validation=(await c.post(f"{VALIDATOR}/v1/validate",json={"parser":ai,"samples":[x.raw]})).json()
            if validation["status"]!="validated":
                await audit(c,"unknown_parser",{"source":x.source,"fingerprint":inspected["fingerprint"],"raw":x.raw,"validation":validation})
                return {"status":"UNKNOWN_FORMAT_REQUIRES_REVIEW","inspection":inspected,"validation":validation}

        parsed=(await c.post(f"{PARSER}/v1/parse",json=x.model_dump())).json()
        if parsed.get("status")=="UNKNOWN_FORMAT":
            await audit(c,"unknown_format",{"source":x.source,"inspection":inspected,"parsed":parsed})
            return {"status":"UNKNOWN_FORMAT_REQUIRES_REVIEW","parsed":parsed}

        normalized=(await c.post(
            f"{NORMALIZER}/v1/normalize",
            json={"raw":x.raw,"parsed":parsed.get("fields",{}),"parser_id":parsed.get("parser_id"),
                  "parser_confidence":parsed.get("confidence",0)}
        )).json()
        normalized.setdefault("event",{})["created"]=received

        enriched=(await c.post(f"{ENRICHMENT}/v1/enrich",json={"event":normalized})).json()

        correlation=(await c.post(f"{CORRELATION}/v1/correlate",json={"events":[enriched]})).json()
        response_actions=[]

        for signal in correlation.get("signals",[]):
            detection=(await c.post(f"{DETECTION}/v1/detect",json=signal)).json()
            analysis=(await c.post(f"{AI_ANALYSIS}/v1/analyze",json={
                "signal_id":signal["signal_id"],
                "signal_type":signal["signal_type"],
                "severity":detection["severity"],
                "confidence":detection["confidence"],
                "source_ip":signal.get("source_ip"),
                "events":signal.get("events",[])
            })).json()

            # AI is advisory. The deterministic detection result selects the
            # allowlisted response proposal; policy-engine remains authoritative.
            playbook="PB-BRUTEFORCE-BLOCK-IP" if detection.get("rule_id")=="CORR-REPEATED-SOURCE" else ""
            action="block_source_ip" if playbook else ""
            policy=(await c.post(f"{POLICY}/v1/evaluate",json={
                "playbook":playbook,
                "action":action,
                "confidence":detection.get("confidence",0),
                "severity":detection.get("severity","medium"),
                "source_ip":signal.get("source_ip"),
                "signal_id":signal.get("signal_id"),
                "analyst_approved":False
            })).json()

            soar_result=None
            if policy.get("allowed"):
                soar_result=(await c.post(f"{SOAR}/v1/execute",json={
                    "playbook":policy["playbook"],
                    "action":policy["action"],
                    "source_ip":signal.get("source_ip"),
                    "signal_id":signal.get("signal_id"),
                    "idempotency_key":policy["idempotency_key"],
                    "approved":True
                })).json()
                if soar_result.get("executed"):
                    await c.post(f"{POLICY}/v1/mark-executed",json={"idempotency_key":policy["idempotency_key"]})

            action_record={"signal":signal,"detection":detection,"ai_analysis":analysis,
                           "policy":policy,"soar":soar_result}
            response_actions.append(action_record)
            await audit(c,"security_decision",action_record)

        await audit(c,"normalized_event",{"event":enriched,"correlation":correlation})
        return {"status":"PROCESSED","parsed":parsed,"normalized":enriched,
                "correlation":correlation,"response_actions":response_actions}

async def ensure_group():
    try:
        await rdb.xgroup_create(EVENT_STREAM,CONSUMER_GROUP,id="0",mkstream=True)
    except Exception as e:
        if "BUSYGROUP" not in str(e):
            raise

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
        except asyncio.CancelledError:
            raise
        except Exception:
            await asyncio.sleep(2)

@api.on_event("startup")
async def startup():
    global rdb,consumer_task
    rdb=redis.from_url(REDIS_URL,decode_responses=True)
    await rdb.ping()
    consumer_task=asyncio.create_task(consume())

@api.on_event("shutdown")
async def shutdown():
    if consumer_task:
        consumer_task.cancel()
    if rdb:
        await rdb.aclose()

@api.get("/health")
async def health():
    await rdb.ping()
    return {"status":"ok","service":"universal-log-pipeline","stream":EVENT_STREAM}

@api.post("/v1/process")
async def process(x:Ingest):
    return await process_event(x)

@api.get("/v1/queue")
async def queue_info():
    return {"stream_length":await rdb.xlen(EVENT_STREAM),"dlq_length":await rdb.xlen(DLQ_STREAM)}

@api.post("/v1/replay")
async def replay(limit:int=100):
    rows=await rdb.xrange(DLQ_STREAM,count=max(1,min(limit,1000)))
    replayed=0
    for msg_id,fields in rows:
        await rdb.xadd(EVENT_STREAM,{"payload":fields.get("payload","{}")},maxlen=100000,approximate=True)
        await rdb.xdel(DLQ_STREAM,msg_id)
        replayed+=1
    return {"replayed":replayed,"remaining_dlq":await rdb.xlen(DLQ_STREAM)}

@api.post("/v1/correlate")
async def correlate(events:list[dict]):
    async with httpx.AsyncClient(timeout=120) as client:
        return (await client.post(f"{CORRELATION}/v1/correlate",json={"events":events})).json()

@api.post("/v1/detect")
async def detect(signal:dict):
    async with httpx.AsyncClient(timeout=120) as client:
        return (await client.post(f"{DETECTION}/v1/detect",json=signal)).json()
