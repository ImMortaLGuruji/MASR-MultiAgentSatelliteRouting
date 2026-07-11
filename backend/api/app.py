import asyncio
import os
import threading
import time
from dataclasses import asdict, replace
from collections import deque

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.schemas import (
    ChaosRequest,
    ConfigUpdateRequest,
    SetRoutingRequest,
    SpawnPacketRequest,
)
from backend.config import Config
from backend.engine import SimulationEngine, SimulationRunner

app = FastAPI(title="MASR", version="0.1.0")


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


API_KEY = os.getenv("MASR_API_KEY")
MAX_REQUEST_BYTES = _env_int("MASR_MAX_REQUEST_BYTES", 100_000)
RATE_LIMIT_PER_MIN = _env_int("MASR_RATE_LIMIT_PER_MIN", 300)
RATE_LIMIT_WINDOW_SEC = 60.0
UNAUTHENTICATED_PATHS = {"/", "/v1", "/docs", "/openapi.json", "/redoc"}
_rate_limit_buckets: dict[str, deque[float]] = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = SimulationEngine(Config())
engine_lock = threading.RLock()
runner = SimulationRunner(
    engine=engine, tick_interval=engine.config.tick_interval, lock=engine_lock
)
async_engine_lock = asyncio.Lock()


@app.middleware("http")
async def enforce_limits(request: Request, call_next):
    if API_KEY and request.url.path not in UNAUTHENTICATED_PATHS:
        if request.headers.get("x-api-key") != API_KEY:
            return JSONResponse(status_code=401, content={"detail": "unauthorized"})

    if MAX_REQUEST_BYTES > 0:
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > MAX_REQUEST_BYTES:
                    return JSONResponse(
                        status_code=413,
                        content={"detail": "request too large"},
                    )
            except ValueError:
                pass

    if RATE_LIMIT_PER_MIN > 0:
        client_host = request.client.host if request.client else "unknown"
        bucket = _rate_limit_buckets.setdefault(client_host, deque())
        now = time.monotonic()
        while bucket and now - bucket[0] > RATE_LIMIT_WINDOW_SEC:
            bucket.popleft()
        if len(bucket) >= RATE_LIMIT_PER_MIN:
            return JSONResponse(
                status_code=429, content={"detail": "rate limit exceeded"}
            )
        bucket.append(now)

    return await call_next(request)


def _runtime_config() -> dict:
    config = asdict(engine.config)
    config["runner_tick_interval"] = runner.tick_interval
    return config


def _state_payload() -> dict:
    snapshot = engine.snapshot()
    snapshot["runner"] = {
        "running": runner.is_running,
        "tick_interval": runner.tick_interval,
    }
    snapshot["config"] = _runtime_config()
    return snapshot


def _build_adjacency_from_links() -> dict[str, set[str]]:
    node_ids = sorted(
        set(engine.satellites.keys()) | set(engine.ground_stations.keys())
    )
    adjacency: dict[str, set[str]] = {node_id: set() for node_id in node_ids}
    for source_id, target_id in sorted(engine.active_links.keys()):
        if source_id not in adjacency:
            adjacency[source_id] = set()
        if target_id not in adjacency:
            adjacency[target_id] = set()
        adjacency[source_id].add(target_id)
        adjacency[target_id].add(source_id)
    return adjacency


def _reachable_nodes(source: str, adjacency: dict[str, set[str]]) -> list[str]:
    if source not in adjacency:
        return []
    queue: deque[str] = deque([source])
    seen = {source}
    while queue:
        node = queue.popleft()
        for neighbor in sorted(adjacency.get(node, set())):
            if neighbor in seen:
                continue
            seen.add(neighbor)
            queue.append(neighbor)
    return sorted(node for node in seen if node != source)


def _diff_payload(previous: dict | None, current: dict) -> dict:
    if previous is None:
        full = dict(current)
        full["diff"] = False
        return full

    changed_satellites = {
        satellite_id: state
        for satellite_id, state in current["satellites"].items()
        if previous.get("satellites", {}).get(satellite_id) != state
    }
    changed_packets = {
        packet_id: state
        for packet_id, state in current["packets"].items()
        if previous.get("packets", {}).get(packet_id) != state
    }
    removed_packets = sorted(
        set(previous.get("packets", {}).keys()) - set(current["packets"].keys())
    )

    links_changed = previous.get("links") != current.get("links")

    return {
        "diff": True,
        "tick": current["tick"],
        "changed_satellites": changed_satellites,
        "changed_packets": changed_packets,
        "removed_packets": removed_packets,
        "links": current["links"] if links_changed else None,
        "metrics": current["metrics"],
        "failed_satellites": current["failed_satellites"],
        "network_partition_enabled": current["network_partition_enabled"],
        "runner": current.get("runner", {}),
        "config": current.get("config", {}),
    }


@app.get("/")
@app.get("/v1")
def root() -> dict:
    return {"service": "MASR", "status": "ok"}


@app.get("/state")
@app.get("/v1/state")
def get_state() -> dict:
    with engine_lock:
        return _state_payload()


@app.get("/config")
@app.get("/v1/config")
def get_config() -> dict:
    with engine_lock:
        return _runtime_config()


@app.post("/config")
@app.post("/v1/config")
def update_config(request: ConfigUpdateRequest) -> dict:
    with engine_lock:
        updated = engine.config

        if request.routing_policy is not None:
            updated = replace(updated, routing_policy=request.routing_policy.value)
            for satellite_id in sorted(engine.satellites.keys()):
                engine.satellites[satellite_id].state.routing_policy = (
                    request.routing_policy.value
                )

        if request.drop_on_reject is not None:
            updated = replace(updated, drop_on_reject=request.drop_on_reject)

        if request.tick_interval is not None:
            updated = replace(updated, tick_interval=request.tick_interval)
            runner.tick_interval = request.tick_interval

        engine.config = updated
        return _runtime_config()


@app.get("/metrics")
@app.get("/v1/metrics")
def get_metrics() -> dict:
    with engine_lock:
        return engine.metrics.snapshot(current_tick=engine.tick)


@app.post("/spawn_packet")
@app.post("/v1/spawn_packet")
def spawn_packet(request: SpawnPacketRequest) -> dict:
    with engine_lock:
        if request.source not in engine.satellites:
            raise HTTPException(
                status_code=400, detail="source must be an existing satellite id"
            )
        valid_destinations = set(engine.satellites.keys()) | set(
            engine.ground_stations.keys()
        )
        if request.destination not in valid_destinations:
            raise HTTPException(
                status_code=400,
                detail="destination must be an existing satellite or ground station id",
            )
        try:
            packet = engine.spawn_packet(
                source=request.source,
                destination=request.destination,
                priority=request.priority,
                size=request.size,
                ttl=request.ttl,
            )
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return {"packet_id": packet.packet_id, "state": packet.state}


@app.post("/tick")
@app.post("/v1/tick")
def run_tick() -> dict:
    with engine_lock:
        engine.run_tick()
        return {"tick": engine.tick}


@app.post("/reset")
@app.post("/v1/reset")
def reset() -> dict:
    with engine_lock:
        engine.reset()
    return {"status": "ok"}


@app.post("/set_routing")
@app.post("/v1/set_routing")
def set_routing(request: SetRoutingRequest) -> dict:
    with engine_lock:
        engine.config = replace(engine.config, routing_policy=request.policy.value)
        for satellite_id in sorted(engine.satellites.keys()):
            engine.satellites[satellite_id].state.routing_policy = request.policy.value
    return {"status": "ok", "policy": request.policy.value}


@app.post("/chaos")
@app.post("/v1/chaos")
def chaos(request: ChaosRequest) -> dict:
    with engine_lock:
        ids = sorted(engine.satellites.keys())
        if request.mode == "mass_packet_generation":
            if not engine.active_links:
                engine.compute_link_visibility()
            generated = 0
            if len(ids) < 2:
                return {"status": "ok", "generated": 0}
            adjacency = _build_adjacency_from_links()
            for index in range(request.count):
                source = ids[index % len(ids)]
                reachable = _reachable_nodes(source, adjacency)
                if not reachable:
                    continue
                destination = reachable[index % len(reachable)]
                engine.spawn_packet(
                    source=source,
                    destination=destination,
                    priority=1 + (index % 3),
                    size=1,
                )
                generated += 1
            return {"status": "ok", "generated": generated}

        if request.mode == "reduce_bandwidth":
            for key in sorted(engine.active_links.keys()):
                engine.active_links[key].bandwidth = max(
                    engine.active_links[key].bandwidth * 0.5, 1.0
                )
            return {"status": "ok", "mode": request.mode}

        if request.mode in {"bandwidth_fluctuation", "fluctuate_bandwidth"}:
            engine.fluctuate_bandwidth()
            return {"status": "ok", "mode": request.mode}

        if request.mode in {"random_satellite_failure", "disable_random_satellites"}:
            disabled = engine.disable_random_satellites(request.count)
            return {
                "status": "ok",
                "mode": request.mode,
                "disabled": disabled,
                "failed_count": len(engine.failed_satellites),
            }

        if request.mode == "restore_satellites":
            restored = engine.restore_satellites(request.count)
            return {
                "status": "ok",
                "mode": request.mode,
                "restored": restored,
                "failed_count": len(engine.failed_satellites),
            }

        if request.mode == "network_partition":
            enabled = request.enabled if request.enabled is not None else True
            engine.set_network_partition(enabled)
            return {"status": "ok", "mode": request.mode, "enabled": enabled}

    raise HTTPException(status_code=400, detail="unsupported chaos mode")


@app.post("/runner/start")
@app.post("/v1/runner/start")
def start_runner() -> dict:
    started = runner.start()
    return {
        "status": "ok",
        "running": runner.is_running,
        "started": started,
        "tick_interval": runner.tick_interval,
    }


@app.post("/runner/stop")
@app.post("/v1/runner/stop")
def stop_runner() -> dict:
    stopped = runner.stop()
    return {"status": "ok", "running": runner.is_running, "stopped": stopped}


@app.get("/runner/status")
@app.get("/v1/runner/status")
def runner_status() -> dict:
    with engine_lock:
        tick = engine.tick
    return {
        "running": runner.is_running,
        "tick_interval": runner.tick_interval,
        "tick": tick,
    }


@app.websocket("/ws")
@app.websocket("/v1/ws")
async def stream_state(websocket: WebSocket) -> None:
    await websocket.accept()
    if API_KEY:
        provided_key = websocket.headers.get("x-api-key") or websocket.query_params.get(
            "api_key"
        )
        if provided_key != API_KEY:
            await websocket.close(code=1008)
            return
    auto_stream = True
    stream_interval = max(engine.config.tick_interval, 0.1)
    previous_snapshot: dict | None = None

    async def snapshot_with_lock() -> dict:
        def _build() -> dict:
            with engine_lock:
                return _state_payload()

        async with async_engine_lock:
            return await asyncio.to_thread(_build)

    async def run_engine_command(fn) -> None:
        def _run() -> None:
            with engine_lock:
                fn()

        async with async_engine_lock:
            await asyncio.to_thread(_run)

    async def run_runner_command(fn) -> None:
        await asyncio.to_thread(fn)

    try:
        initial_snapshot = await snapshot_with_lock()
        await websocket.send_json(_diff_payload(previous_snapshot, initial_snapshot))
        previous_snapshot = initial_snapshot
        while True:
            if auto_stream:
                try:
                    command = await asyncio.wait_for(
                        websocket.receive_text(), timeout=stream_interval
                    )
                    normalized = command.strip().lower()
                    if normalized == "tick":
                        await run_engine_command(engine.run_tick)
                    elif normalized == "reset":
                        await run_engine_command(engine.reset)
                        previous_snapshot = None
                    elif normalized == "runner:start":
                        await run_runner_command(runner.start)
                    elif normalized == "runner:stop":
                        await run_runner_command(runner.stop)
                    elif normalized == "stream:off":
                        auto_stream = False
                    elif normalized.startswith("stream:interval:"):
                        _, _, interval_value = normalized.partition("stream:interval:")
                        try:
                            parsed_interval = float(interval_value)
                            stream_interval = max(parsed_interval, 0.1)
                        except ValueError:
                            pass
                except asyncio.TimeoutError:
                    pass
            else:
                command = await websocket.receive_text()
                normalized = command.strip().lower()
                if normalized == "tick":
                    await run_engine_command(engine.run_tick)
                elif normalized == "reset":
                    await run_engine_command(engine.reset)
                    previous_snapshot = None
                elif normalized == "runner:start":
                    await run_runner_command(runner.start)
                elif normalized == "runner:stop":
                    await run_runner_command(runner.stop)
                elif normalized == "stream:on":
                    auto_stream = True

            snapshot = await snapshot_with_lock()
            await websocket.send_json(_diff_payload(previous_snapshot, snapshot))
            previous_snapshot = snapshot
    except WebSocketDisconnect:
        return
