# MASR: Multi-Agent Satellite Routing

### Deterministic Distributed Simulation of Autonomous Satellite Networks

MASR is a **deterministic multi-agent simulation platform** modeling packet routing across a constellation of autonomous satellites operating in Low Earth Orbit (LEO).

The system explores **distributed routing, delay-tolerant networking, and congestion dynamics in time-varying networks**.

Unlike traditional network simulators, MASR enforces:

* strict agent isolation
* deterministic message passing
* reproducible seeded execution
* emergent coordination without centralized routing

MASR is designed as a **research-grade coordination framework** rather than a simple visualization or toy simulation.

## Current Implementation Status (Phase 8)

Implemented now:

* deterministic backend core (`backend/`)
* deterministic message bus and isolated agents
* simulation engine tick loop + metrics + snapshots
* FastAPI endpoints (`/state`, `/metrics`, `/spawn_packet`, `/tick`, `/reset`, `/set_routing`, `/chaos`) and websocket (`/ws`)
* deterministic tests in `tests/`
* minimal frontend websocket snapshot viewer in `frontend/`
* phase 3 deterministic background runner + websocket auto-stream controls
* configurable strict congestion policy via `Config.drop_on_reject`
* phase 4 deterministic chaos extensions (satellite failure + network partition + bandwidth fluctuation)
* phase 4 metrics (`throughput`, `link_utilization`, `satellite_buffer_usage`, `packet_drop_rate`)
* phase 5 routing strategy plugin layer (registry-based policies with graph-aware shortest-path/contact-graph handlers)
* phase 6 deterministic priority-based congestion handling (drop-lowest-priority and preemption)
* phase 7 API/frontend control parity for routing, chaos, runner, and runtime config
* phase 8 packaging/ops hardening (`pyproject.toml`, `Makefile`, CI workflow, operations guide)
* polish pass: API contract tests for `/config`, `/state`, `/runner/*`, and failed-source spawn handling

Quick start:

```bash
pip install -r requirements.txt
python -m backend.main
```

Using Makefile shortcuts:

```bash
make setup
make run
make test
make frontend
```

Run tests:

```bash
python -m unittest discover -s tests -v
```

Open frontend viewer:

```bash
cd frontend
python -m http.server 5500
```

Then open:

```text
http://localhost:5500
```

Phase 3 API controls:

```text
POST /runner/start
POST /runner/stop
GET  /runner/status
```

Phase 7 runtime config API:

```text
GET  /config
POST /config
```

`POST /config` example:

```json
{
  "routing_policy": "CONTACT_GRAPH_ROUTING",
  "drop_on_reject": true,
  "tick_interval": 0.5
}
```

Phase 4 chaos modes for `POST /chaos`:

```text
mass_packet_generation
random_satellite_failure
restore_satellites
bandwidth_fluctuation
network_partition
```

`network_partition` accepts optional JSON field:

```json
{"mode":"network_partition","enabled":true}
```

Phase 3 websocket commands:

```text
tick
reset
runner:start
runner:stop
stream:off
stream:on
stream:interval:<seconds>
```

---

# 1 Core Design Goals

MASR aims to explore fundamental problems in distributed networking:

1. Routing in **dynamic topologies**
2. **Delay-tolerant networking**
3. **Autonomous packet forwarding**
4. **distributed bandwidth allocation**
5. **congestion control under intermittent links**
6. **emergent routing behavior**

The architecture is designed for **controlled experimentation**.

---

# 2 Conceptual Model

MASR models a satellite constellation as a **time-varying communication graph**.

Nodes:

```
Satellite Nodes
Ground Station Nodes
Packet Entities
```

Edges:

```
Inter-Satellite Links (ISL)
Satellite-Ground Links
```

Graph properties change over time due to **orbital motion**.

---

# 3 High-Level Architecture

```
+-----------------------------------+
|           Visualization           |
+-----------------------------------+
|           WebSocket API           |
+-----------------------------------+
|           REST Control API        |
+-----------------------------------+
|         Deterministic Engine      |
+-----------------------------------+
|          Message Bus Layer        |
+-----------------------------------+
|         Autonomous Agents         |
|  Satellite | Ground | Packet      |
+-----------------------------------+
```

---

# 4 Simulation Engine

The simulation engine is the **deterministic orchestrator**.

Responsibilities:

```
advance_simulation_tick()
update_orbital_positions()
compute_link_visibility()
deliver_messages()
process_agent_actions()
execute_packet_transfers()
update_metrics()
broadcast_snapshot()
```

Important constraint:

The engine **does not modify agent decisions**.

---

# 5 Simulation Tick Lifecycle

Each simulation step follows a strict sequence.

```
Tick Start
│
├─ Update orbital positions
│
├─ Recalculate link visibility
│
├─ Generate link events
│
├─ Deliver queued messages
│
├─ Agents process messages
│
├─ Agents emit new messages
│
├─ Packet transfers executed
│
├─ Metrics updated
│
└─ Snapshot broadcast
```

---

# 6 Agent System

MASR contains three agent types.

```
SatelliteAgent
GroundStationAgent
PacketAgent
```

Each agent operates independently.

---

# 7 Satellite Agent

Satellite agents act as **autonomous routers**.

Internal state:

```
satellite_id
orbit_index
position_vector
neighbor_table
packet_queue
buffer_capacity
bandwidth_capacity
routing_policy
link_state_table
```

Satellite agents must:

```
detect_neighbors()
manage_packet_queue()
negotiate_packet_transfer()
enforce_bandwidth_limits()
predict_future_links()
```

---

# 8 Satellite Agent State Machine

Satellite behavior is governed by a state machine.

```
            +----------------+
            |   IDLE         |
            +----------------+
                  |
                  | link detected
                  v
            +----------------+
            | LINK_AVAILABLE |
            +----------------+
                  |
                  | negotiate transfer
                  v
            +----------------+
            | TRANSFERRING   |
            +----------------+
                  |
                  | transfer complete
                  v
            +----------------+
            | LINK_RELEASED  |
            +----------------+
```

Transitions occur only during tick processing.

---

# 9 Ground Station Agent

Ground stations inject and receive packets.

State:

```
station_id
geographic_location
visible_satellites
packet_generation_rate
received_packets
```

Responsibilities:

```
generate_packets()
receive_packets()
track_contact_windows()
```

---

# 10 Packet Agent

Packets represent network traffic.

State:

```
packet_id
source
destination
priority
ttl
creation_tick
current_holder
route_history
size_bytes
```

Lifecycle:

```
CREATED
IN_TRANSIT
DELIVERED
DROPPED
EXPIRED
```

---

# 11 Packet State Machine

```
CREATED
  |
  v
IN_QUEUE
  |
  v
IN_TRANSFER
  |
  v
IN_QUEUE
  |
  +----> DELIVERED
  |
  +----> EXPIRED
  |
  +----> DROPPED
```

---

# 12 Message Bus

All communication occurs via the message bus.

Agents **cannot directly invoke methods on other agents**.

---

# 13 Message Delivery Rules

Messages are processed in deterministic order.

Ordering rules:

```
tick
sender_id
receiver_id
message_id
```

This guarantees **reproducible execution**.

---

# 14 Message Types

Primary message types:

```
LINK_ESTABLISHED
LINK_TERMINATED
PACKET_OFFER
PACKET_ACCEPT
PACKET_REJECT
PACKET_TRANSFER
BUFFER_FULL
ROUTING_UPDATE
```

---

# 15 Message Schema

Example message schema:

```
{
  message_id: UUID
  tick: int
  sender: agent_id
  receiver: agent_id
  type: message_type
  payload: {}
}
```

Example payload for packet offer:

```
{
  packet_id: string
  packet_priority: int
  packet_size: int
  destination: node_id
}
```

---

# 16 Sequence Diagram – Packet Transfer

```
GroundStation -> Satellite A : PACKET_INJECT
Satellite A -> Satellite B : PACKET_OFFER
Satellite B -> Satellite A : PACKET_ACCEPT
Satellite A -> Satellite B : PACKET_TRANSFER
Satellite B -> Satellite A : TRANSFER_COMPLETE
```

---

# 17 Sequence Diagram – Link Establishment

```
Engine -> Satellite A : LINK_ESTABLISHED
Engine -> Satellite B : LINK_ESTABLISHED

Satellite A -> Satellite B : HELLO
Satellite B -> Satellite A : HELLO_ACK
```

---

# 18 Orbital Model

Satellites move in deterministic circular orbits.

Parameters:

```
altitude
inclination
orbital_period
phase_offset
```

Position computation:

```
theta = angular_velocity * tick
x = radius * cos(theta)
y = radius * sin(theta)
z = inclination * sin(theta)
```

---

# 19 Link Visibility Algorithm

Two satellites form a link if:

```
distance <= max_link_distance
line_of_sight == true
```

Distance computed via Euclidean space.

---

# 20 Link State

Each link contains:

```
source_satellite
target_satellite
bandwidth
propagation_delay
quality
active
```

---

# 21 Routing Policies

Routing algorithms are pluggable.

Supported strategies:

```
SHORTEST_PATH
EPIDEMIC
STORE_AND_FORWARD
CONTACT_GRAPH_ROUTING
```

---

# 22 Routing Pseudocode – Shortest Path

```
function compute_route(packet, satellite):

    graph = predicted_link_graph()

    path = dijkstra(
        graph,
        source = satellite.id,
        destination = packet.destination
    )

    return path.next_hop
```

---

# 23 Routing Pseudocode – Epidemic

```
function epidemic_routing(packet, satellite):

    for neighbor in satellite.neighbors:
        if neighbor.has_not_seen(packet):
            offer_packet(packet, neighbor)
```

---

# 24 Routing Pseudocode – Store and Forward

```
function store_and_forward(packet, satellite):

    best_future_link = predict_best_link(packet.destination)

    if best_future_link exists:
        wait_for_link()
    else:
        forward_to_best_neighbor()
```

---

# 25 Congestion Model

Each satellite has limited resources.

```
buffer_capacity
queue_limit
bandwidth_limit
```

If buffer full:

```
drop_low_priority_packet()
```

---

# 26 Congestion Handling Pseudocode

```
if queue_length >= buffer_capacity:

    lowest_priority_packet = find_lowest_priority()

    drop_packet(lowest_priority_packet)
```

---

# 27 Chaos Mode

Chaos mode injects extreme network conditions.

Examples:

```
mass_packet_generation
random_satellite_failure
bandwidth_fluctuation
network_partition
```

All events remain deterministic.

---

# 28 Metrics System

Metrics recorded per run.

```
packet_delivery_ratio
average_latency
throughput
link_utilization
satellite_buffer_usage
packet_drop_rate
```

Metrics reset when simulation resets.

---

# 29 Determinism Guarantees

MASR enforces strict determinism.

Rules:

```
seeded random generator
ordered message queue
sorted agent iteration
atomic engine reset
```

No nondeterministic operations allowed.

---

# 30 Snapshot System

Snapshots represent full simulation state.

Snapshot contains:

```
tick
satellite_positions
active_links
packet_locations
metrics
```

Snapshots must be **JSON serializable**.

---

# 31 API Endpoints

```
GET /state
GET /metrics
POST /spawn_packet
POST /reset
POST /chaos
POST /set_routing
```

WebSocket:

```
/ws
```

Streams snapshots.

---

# 32 Visualization

Frontend renders:

```
Earth sphere
satellite orbits
satellite nodes
inter-satellite links
packet flows
congestion heatmap
```

Rendering pipeline:

```
WebGL
requestAnimationFrame
snapshot-driven updates
```

---

# 33 Configuration Parameters

```
num_orbits
satellites_per_orbit
orbital_altitude
max_link_distance
bandwidth_capacity
buffer_capacity
tick_interval
packet_spawn_rate
seed
```

---

# 34 Project Structure

```
masr
│
├── backend
│   ├── engine
│   ├── agents
│   ├── routing
│   ├── orbital
│   ├── messaging
│   ├── metrics
│   └── api
│
├── frontend
│   ├── renderer
│   ├── websocket
│   └── controls
│
└── README.md
```

---

# 35 Implementation Constraints for Codex

Critical implementation requirements:

1 Agents must not reference each other directly.
2 All communication must occur through the message bus.
3 Simulation loop must be deterministic.
4 Agent iteration must use sorted order.
5 Snapshots must be fully serializable.

---

# 36 Role of MASR in ATLAS

MASR is intended to become a module in the larger system:

```
ATLAS
Agent Testing Lab for Autonomous Systems
```

Modules may include:

```
ATLAS-Satellite
ATLAS-Traffic
ATLAS-Compute
ATLAS-Network
```

All modules share a **deterministic multi-agent simulation engine**.
