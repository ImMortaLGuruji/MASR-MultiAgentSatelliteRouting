from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect

from backend.api.schemas import ChaosRequest, SetRoutingRequest, SpawnPacketRequest
from backend.config import Config
from backend.engine import SimulationEngine


app = FastAPI(title="MASR", version="0.1.0")
engine = SimulationEngine(Config())


@app.get("/state")
def get_state() -> dict:
    return engine.snapshot()


@app.get("/metrics")
def get_metrics() -> dict:
    return engine.metrics.snapshot()


@app.post("/spawn_packet")
def spawn_packet(request: SpawnPacketRequest) -> dict:
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
    engine.run_tick()
    return {"tick": engine.tick}


@app.post("/reset")
def reset() -> dict:
    engine.reset()
    return {"status": "ok"}


@app.post("/set_routing")
def set_routing(request: SetRoutingRequest) -> dict:
    for satellite_id in sorted(engine.satellites.keys()):
        engine.satellites[satellite_id].state.routing_policy = request.policy
    return {"status": "ok", "policy": request.policy}


@app.post("/chaos")
def chaos(request: ChaosRequest) -> dict:
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
                source=source, destination=destination, priority=1 + (index % 3), size=1
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


@app.websocket("/ws")
async def stream_state(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        await websocket.send_json(engine.snapshot())
        while True:
            command = await websocket.receive_text()
            if command.strip().lower() == "tick":
                engine.run_tick()
            elif command.strip().lower() == "reset":
                engine.reset()
            await websocket.send_json(engine.snapshot())
    except WebSocketDisconnect:
        return
