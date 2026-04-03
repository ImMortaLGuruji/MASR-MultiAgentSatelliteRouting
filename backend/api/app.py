import asyncio
import threading
from dataclasses import asdict, replace
from collections import deque

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.api.schemas import (
    ChaosRequest,
    ConfigUpdateRequest,
    SetRoutingRequest,
    SpawnPacketRequest,
)
from backend.config import Config
from backend.engine import SimulationEngine, SimulationRunner


app = FastAPI(title="MASR", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = SimulationEngine(Config())
engine_lock = threading.RLock()
runner = SimulationRunner(
    engine=engine, tick_interval=engine.config.tick_interval, lock=engine_lock
)


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
    adjacency: dict[str, set[str]] = {
        satellite_id: set() for satellite_id in sorted(engine.satellites.keys())
    }
    for source_id, target_id in sorted(engine.active_links.keys()):
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
def root() -> dict:
    return {"service": "MASR", "status": "ok"}


@app.get("/state")
def get_state() -> dict:
    with engine_lock:
        return _state_payload()


@app.get("/config")
def get_config() -> dict:
    with engine_lock:
        return _runtime_config()


@app.post("/config")
def update_config(request: ConfigUpdateRequest) -> dict:
    with engine_lock:
        updated = engine.config

        if request.routing_policy is not None:
            updated = replace(updated, routing_policy=request.routing_policy)
            for satellite_id in sorted(engine.satellites.keys()):
                engine.satellites[satellite_id].state.routing_policy = (
                    request.routing_policy
                )

        if request.drop_on_reject is not None:
            updated = replace(updated, drop_on_reject=request.drop_on_reject)

        if request.tick_interval is not None:
            updated = replace(updated, tick_interval=request.tick_interval)
            runner.tick_interval = request.tick_interval

        engine.config = updated
        return _runtime_config()


@app.get("/metrics")
def get_metrics() -> dict:
    with engine_lock:
        return engine.metrics.snapshot(current_tick=engine.tick)


@app.post("/spawn_packet")
def spawn_packet(request: SpawnPacketRequest) -> dict:
    with engine_lock:
        if request.source not in engine.satellites:
            raise HTTPException(
                status_code=400, detail="source must be an existing satellite id"
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
def run_tick() -> dict:
    with engine_lock:
        engine.run_tick()
        return {"tick": engine.tick}


@app.post("/reset")
def reset() -> dict:
    with engine_lock:
        engine.reset()
    return {"status": "ok"}


@app.post("/set_routing")
def set_routing(request: SetRoutingRequest) -> dict:
    with engine_lock:
        engine.config = replace(engine.config, routing_policy=request.policy)
        for satellite_id in sorted(engine.satellites.keys()):
            engine.satellites[satellite_id].state.routing_policy = request.policy
    return {"status": "ok", "policy": request.policy}


@app.post("/chaos")
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
def start_runner() -> dict:
    started = runner.start()
    return {
        "status": "ok",
        "running": runner.is_running,
        "started": started,
        "tick_interval": runner.tick_interval,
    }


@app.post("/runner/stop")
def stop_runner() -> dict:
    stopped = runner.stop()
    return {"status": "ok", "running": runner.is_running, "stopped": stopped}


@app.get("/runner/status")
def runner_status() -> dict:
    with engine_lock:
        tick = engine.tick
    return {
        "running": runner.is_running,
        "tick_interval": runner.tick_interval,
        "tick": tick,
    }


@app.websocket("/ws")
async def stream_state(websocket: WebSocket) -> None:
    await websocket.accept()
    auto_stream = True
    stream_interval = max(engine.config.tick_interval, 0.1)
    previous_snapshot: dict | None = None
    try:
        with engine_lock:
            initial_snapshot = _state_payload()
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
                        with engine_lock:
                            engine.run_tick()
                    elif normalized == "reset":
                        with engine_lock:
                            engine.reset()
                    elif normalized == "runner:start":
                        runner.start()
                    elif normalized == "runner:stop":
                        runner.stop()
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
                    with engine_lock:
                        engine.run_tick()
                elif normalized == "reset":
                    with engine_lock:
                        engine.reset()
                elif normalized == "runner:start":
                    runner.start()
                elif normalized == "runner:stop":
                    runner.stop()
                elif normalized == "stream:on":
                    auto_stream = True

            with engine_lock:
                snapshot = _state_payload()
            await websocket.send_json(_diff_payload(previous_snapshot, snapshot))
            previous_snapshot = snapshot
    except WebSocketDisconnect:
        return
