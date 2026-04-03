# MASR: Multi-Agent Satellite Routing

### Deterministic Distributed Simulation of Autonomous Satellite Networks

MASR is a **deterministic multi-agent simulation platform** modeling packet routing across a constellation of autonomous satellites operating in Low Earth Orbit (LEO).

The system explores **distributed routing, delay-tolerant networking, congestion dynamics, and physical layer constraints in time-varying networks**. 

Unlike traditional network simulators, MASR enforces:
* Strict agent isolation
* Deterministic message passing
* Reproducible seeded execution
* Emergent coordination without centralized routing

MASR is designed as a **research-grade coordination framework** for evaluating routing algorithms and congestion control strategies in dynamic satellite topologies.

## Core Capabilities

- **Deterministic Simulation Engine**: Absolute reproducibility through seeded random number generators, sorted data structures, and isolated tick-based message passing.
- **Pluggable Routing Architecture**: Dynamically hot-swappable routing policies (e.g., Shortest Path, Epidemic, Store-and-Forward, Contact Graph Routing) utilizing graph-aware connection predictions.
- **Priority-Based Congestion Control**: Satellites maintain limited buffers with strict, priority-driven packet preemption and dropping strategies under heavy loads.
- **Physical & Energy Constraints**: Models orbital mechanics, visibility constraints, Line-of-Sight (LoS), and real-time battery tracking dictated by orbital shadowing (solar eclipses/Earth occlusion).
- **Chaos Engineering**: API-driven failure injection including random satellite failures, network partitions, and dynamic bandwidth degradation.
- **Real-Time Telemetry & Visualization**: Unidirectional WebSocket streams driving a high-performance React/Canvas purely functional frontend for state inspection.

---

## 1. Quickstart & Operations

### Prerequisites
- Python 3.10+
- Node.js (for the frontend visualization)

### Installation
Deploy the backend simulation engine and its dependencies:

```bash
make setup
```

### Running the System
Start the backend simulation and API on `localhost:8000`:
```bash
make run
```

In a separate terminal, launch the frontend visualization on `localhost:5173`:
```bash
make frontend
```

### Running Test Suites
MASR includes a rigorous test suite enforcing API contracts, determinism, routing properties, and congestion preemption.
```bash
make test
```

---

## 2. API Reference

MASR provides a comprehensive REST API to interact with the simulation runtime, alongside a state-streaming WebSocket.

### Simulation Controls
- `POST /runner/start`: Begin the autonomous background tick loop.
- `POST /runner/stop`: Pause the background tick loop.
- `GET /runner/status`: Check runner state.
- `POST /tick`: Manually advance the simulation by one tick.
- `POST /reset`: Reset the entire simulation state to pristine initialization.

### Runtime Configuration
- `GET /config`: Retrieve the current runtime configuration.
- `POST /config`: Dynamically update routing policy, runner speed, and strict congestion behavior.
  ```json
  {
    "routing_policy": "CONTACT_GRAPH_ROUTING",
    "drop_on_reject": true,
    "tick_interval": 0.5
  }
  ```

### Telemetry & State
- `GET /state`: Retrieve a full snapshot of the simulation.
- `GET /metrics`: Retrieve running KPIs (throughput, latency, drop rates).
- `WebSocket /ws`: Streams JSON engine snapshots continuously for decoupled remote rendering.

### Chaos Engineering
- `POST /chaos`: Inject failure modes into the active simulation.
  Supported modes: `random_satellite_failure`, `restore_satellites`, `bandwidth_fluctuation`, `network_partition`.
  ```json
  {"type": "network_partition", "enabled": true}
  ```

---

## 3. High-Level Architecture

```text
+-----------------------------+
|    React/Canvas Frontend    |  Visualization & Control Display
+-----------------------------+
|    WebSocket / REST API     |  State Streaming & Commands
+-----------------------------+
|    Deterministic Engine     |  Tick Orchestrator & Coordinator
+-----------------------------+
|      Message Bus Layer      |  Deterministic Event Delivery
+-----------------------------+
|      Autonomous Agents      |
| Satellite | Ground | Packet |  Isolated State Machines
+-----------------------------+
```

---

## 4. The Deterministic Engine

The simulation engine is the absolute **deterministic orchestrator**. The engine processes actions strictly phase-by-phase without intruding on autonomous agent decisions.

### Simulation Tick Lifecycle
Every tick follows an immutable execution chain:
1. Update orbital positions (Euler mechanics)
2. Compute geometric solar eclipses / adjust energy states
3. Recalculate link visibility & geometries
4. Generate & drop network partition links (ISL)
5. Deliver queued agent messages deterministically
6. Agents process received messages and update personal state machines
7. Agents emit outbound messages
8. Packet transfers execute based on bandwidth boundaries
9. Metrics are aggregated
10. System snapshot broadcast to WebSockets

### Determinism Guarantees
Rules enforcing absolute reprodubility:
- Global seeded PRNG.
- Ordered message queues sorted by `[tick, sender_id, receiver_id, message_id]`.
- All agent iterations use sorted deterministic topological iterations.

---

## 5. Agent Systems

Agents cannot directly invoke methods on each other. All interaction relies on asynchronous message passing, accurately mapping to real-world RF latency and propagation limits.

### Satellite Agent
Satellite agents act as **autonomous routers** in a space segment.
- **State Managed**: Orbital kinematics, battery capacity, neighbor tables, link states, priority packet queues. 
- **Responsibilities**: Form ad-hoc topologies, enforce bandwidth limits, enact buffer isolation, and intelligently route packets using dynamic contextual data.

### Ground Station Agent
Ground nodes act as network ingress/egress points. They generate multi-priority traffic and compute topological contact windows.

### Packet Agent
Packets possess individual priority, TTL, destination, and route history parameters mapping network flows.

---

## 6. Physical & Orbital Modeling

### Constellation Kinematics
Satellites revolve in idealized uniform circular orbits parameterized by:
- Number of orbits & satellites per orbit
- Altitude (e.g., 550km LEO)
- Inclination & Phase offsets

### Visibility Algorithms
Inter-Satellite Links (ISL) establish dynamically per-tick if they satisfy distance constraints within propagation threshold limits. 

### Energy Shadowing
The engine dynamically computes planetary occlusion. When a satellite enters the Earth's cylindrical orbital shadow (Eclipse phase), charging ceases. Sustained maneuvers deplete the internal battery until operations natively halt, forcing neighboring topologies to adapt.

---

## 7. Routing Policies

Routing policies act as functional plugins evaluating local knowledge.
- **SHORTEST_PATH**: Dijkstra evaluation on the instantaneously predicted graph topology.
- **CONTACT_GRAPH_ROUTING** (CGR): Evaluates historical connectivity to predict optimal delay-tolerant schedules over time-varying ISLs.
- **STORE_AND_FORWARD**: Stores packets iteratively until a link geometry to the target becomes active.
- **EPIDEMIC**: Broadcasts packet replication across all available outgoing spatial links.

---

## 8. Congestion & Priority Preemption

Satellite buffers are finite. The system processes congestion via strict, customizable constraints:
- Evaluates queue length against `buffer_capacity`.
- Evaluates active transmission bandwidth exhaustion. 
- **Preemption Rule**: High-priority network traffic natively overrides low-priority queued packets. Dropped packet vectors generate backpressure routing notifications if `drop_on_reject` policies are enabled.

---

*MASR acts as a foundational research block for analyzing satellite constellation topologies and testing fault-tolerant coordination models.*
