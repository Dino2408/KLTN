import asyncio
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import redis.asyncio as redis
from fastapi import FastAPI
from pydantic import BaseModel, Field

REDIS_URL = os.getenv("REDIS_URL", "redis://event-bus:6379/0")
EVENT_STREAM = os.getenv("EVENT_STREAM", "siem:events")
INPUT_DIR = Path(os.getenv("INPUT_DIR", "/var/log/ingest"))
FILE_POLL_SECONDS = float(os.getenv("FILE_POLL_SECONDS", "1.0"))
SYSLOG_TCP_PORT = int(os.getenv("SYSLOG_TCP_PORT", "5514"))
SYSLOG_UDP_PORT = int(os.getenv("SYSLOG_UDP_PORT", "5514"))

api = FastAPI(title="Universal Ingestion", version="0.3.0")
rdb: redis.Redis | None = None
_tasks: list[asyncio.Task] = []
_servers: list[Any] = []

class Envelope(BaseModel):
    raw: str
    source: str = "unknown"
    transport: str = "http"
    received_at: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

async def publish(event: Envelope) -> str:
    if rdb is None:
        raise RuntimeError("event bus unavailable")
    event.received_at = event.received_at or datetime.now(timezone.utc).isoformat()
    return await rdb.xadd(EVENT_STREAM, {"payload": event.model_dump_json()}, maxlen=100000, approximate=True)

async def publish_raw(raw: str, source: str, transport: str, metadata: dict[str, Any] | None = None):
    return await publish(Envelope(raw=raw.rstrip("\r\n"), source=source, transport=transport, metadata=metadata or {}))

class UDPProtocol(asyncio.DatagramProtocol):
    def datagram_received(self, data, addr):
        raw = data.decode("utf-8", errors="replace")
        _tasks.append(asyncio.create_task(publish_raw(raw, f"syslog:{addr[0]}", "syslog-udp", {"peer": addr[0]})))

async def tcp_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    peer = writer.get_extra_info("peername")
    source = f"syslog:{peer[0]}" if peer else "syslog:tcp"
    try:
        while chunk := await reader.readline():
            await publish_raw(chunk.decode("utf-8", errors="replace"), source, "syslog-tcp", {"peer": peer[0] if peer else None})
    finally:
        writer.close()
        await writer.wait_closed()

async def tail_file(path: Path):
    with path.open("r", encoding="utf-8", errors="replace") as f:
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if line:
                await publish_raw(line, f"file:{path.name}", "file", {"path": str(path)})
            else:
                await asyncio.sleep(FILE_POLL_SECONDS)

async def discover_files():
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    known: set[Path] = set()
    while True:
        for path in INPUT_DIR.glob("*.log"):
            if path not in known:
                known.add(path)
                _tasks.append(asyncio.create_task(tail_file(path)))
        await asyncio.sleep(FILE_POLL_SECONDS)

@api.on_event("startup")
async def startup():
    global rdb
    rdb = redis.from_url(REDIS_URL, decode_responses=True)
    await rdb.ping()
    loop = asyncio.get_running_loop()
    transport, _ = await loop.create_datagram_endpoint(UDPProtocol, local_addr=("0.0.0.0", SYSLOG_UDP_PORT))
    tcp = await asyncio.start_server(tcp_client, "0.0.0.0", SYSLOG_TCP_PORT)
    _servers.extend([transport, tcp])
    _tasks.append(asyncio.create_task(discover_files()))

@api.on_event("shutdown")
async def shutdown():
    for task in _tasks:
        task.cancel()
    for server in _servers:
        server.close()
        if hasattr(server, "wait_closed"):
            await server.wait_closed()
    if rdb:
        await rdb.aclose()

@api.get("/health")
async def health():
    await rdb.ping()
    return {"status": "ok", "service": "ingestion", "stream": EVENT_STREAM}

@api.post("/v1/events")
async def receive(event: Envelope):
    message_id = await publish(event)
    return {"accepted": True, "queued": True, "stream": EVENT_STREAM, "message_id": message_id}

@api.get("/v1/stream")
async def stream_info():
    return {"stream": EVENT_STREAM, "length": await rdb.xlen(EVENT_STREAM)}
