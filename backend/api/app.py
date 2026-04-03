import asyncio
import threading

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect

from backend.api.schemas import ChaosRequest, SetRoutingRequest, SpawnPacketRequest
from backend.config import Config
from backend.engine import SimulationEngine, SimulationRunner


app = FastAPI(title="MASR", version="0.1.0")
engine = SimulationEngine(Config())
engine_lock = threading.RLock()
runner = SimulationRunner(engine=engine, tick_interval=engine.config.tick_interval, lock=engine_lock)


@app.get("/")
def root() -> dict:
    return {"service": "MASR", "status": "ok"}


@app.get("/state")
def get_state() -> dict:
    with engine_lock:
        return engine.snapshot()


@app.get("/metrics")
def get_metrics() -> dict:
    with engine_lock:
        return engine.metrics.snapshot()


@app.post("/spawn_packet")
def spawn_packet(request: SpawnPacketRequest) -> dict:
    with engine_lock:
        if request.source not in engine.satellites:
            raise HTTPException(
                status_code=400, detail="source must be an existing satellite id"
            )
        packet = engine.spawn_packet(
            source=request.source,
            destination=request.destination,
            priority=request.priority,
            size=request.size,
            ttl=request.ttl,
        )
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
        for satellite_id in sorted(engine.satellites.keys()):
            engine.satellites[satellite_id].state.routing_policy = request.policy
    return {"status": "ok", "policy": request.policy}


@app.post("/chaos")
def chaos(request: ChaosRequest) -> dict:
    with engine_lock:
        ids = sorted(engine.satellites.keys())
        if request.mode == "mass_packet_generation":
            generated = 0
            if len(ids) < 2:
                return {"status": "ok", "generated": 0}
            for index in range(request.count):
                source = ids[index % len(ids)]
                destination = ids[-((index % len(ids)) + 1)]
                if source == destination:
                    continue
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
    return {"running": runner.is_running, "tick_interval": runner.tick_interval, "tick": tick}


@app.websocket("/ws")
async def stream_state(websocket: WebSocket) -> None:
    await websocket.accept()
    auto_stream = True
    stream_interval = max(engine.config.tick_interval, 0.1)
    try:
        with engine_lock:
            initial_snapshot = engine.snapshot()
        await websocket.send_json(initial_snapshot)
        while True:
            if auto_stream:
                try:
                    command = await asyncio.wait_for(websocket.receive_text(), timeout=stream_interval)
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
                snapshot = engine.snapshot()
            snapshot["runner"] = {"running": runner.is_running, "tick_interval": runner.tick_interval}
            await websocket.send_json(snapshot)
    except WebSocketDisconnect:
        return
