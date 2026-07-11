# 🚀 MASR — Multi-Agent Satellite Routing

### Deterministic Distributed Simulation of LEO Satellite Networks

MASR is a **research-grade simulation platform** that models packet routing across autonomous satellite constellations in Low Earth Orbit (LEO).

It explores how decentralized agents coordinate under **dynamic topology, intermittent connectivity, and resource constraints** — without centralized control.

---

## 🌌 Why MASR?

Modern satellite constellations (e.g., Starlink-like systems) operate in environments where:

* Network topology changes continuously
* Links appear and disappear due to orbital motion
* Bandwidth and buffer resources are constrained
* Centralized routing is impractical

MASR models this as a **distributed systems problem**, not just a visualization.

---

## 🧠 Key Highlights

* ⚡ **Deterministic Simulation Engine**
  Fully reproducible execution using seeded randomness and ordered message delivery

* 🤖 **Multi-Agent Architecture**
  Satellites act as autonomous routing agents

* 🔗 **Dynamic Inter-Satellite Links**
  Connectivity changes based on orbital motion

* 📡 **Delay-Tolerant Networking**
  Supports store-and-forward, epidemic, and predictive routing

* 📊 **Real-Time Visualization**
  Interactive frontend rendering satellites, links, and packet flows

* 🧪 **Research-Oriented Design**
  Built for experimentation, benchmarking, and protocol analysis

---

## 🏗️ System Architecture

```
Frontend (React + Canvas/WebGL)
        │
WebSocket (State Streaming)
        │
FastAPI Backend
        │
Deterministic Simulation Engine
        │
Multi-Agent System
(Satellites | Ground Stations | Packets)
```

---

## ⚙️ Core Concepts

### 🛰️ Satellite Agents

Each satellite:

* Maintains a packet buffer
* Tracks visible neighbors
* Negotiates packet forwarding
* Applies routing policies

---

### 📦 Packet Lifecycle

```
Created → Queued → Transferred → Delivered / Dropped
```

---

### 🔄 Message-Based Coordination

Agents communicate via structured messages:

* PACKET_OFFER
* PACKET_ACCEPT
* PACKET_REJECT
* LINK_ESTABLISHED

No direct agent-to-agent calls.

---

### 🌐 Dynamic Topology

The network is modeled as:

```
G(t) = (V, E(t))
```

Where edges change over time due to orbital motion.

---

## 🚀 Features

* Deterministic replayable simulations
* Multiple routing strategies
* Congestion-aware packet handling
* Real-time visualization
* Chaos mode for stress testing
* Configurable simulation parameters

---

## 🧪 Routing Algorithms

* Shortest Path
* Epidemic Routing
* Store-and-Forward
* Contact Graph Routing (planned)

---

## 📊 Metrics

MASR tracks:

* Packet Delivery Ratio
* Average Latency
* Throughput
* Packet Loss Rate
* Link Utilization

---

## 🎮 Frontend Visualization

* Satellite constellation rendering
* Inter-satellite link visualization
* Packet movement animation
* Metrics dashboard
* Interactive controls

---

## ⚡ Getting Started

### Backend

```bash
uvicorn backend.api.app:app --reload
```

---

### Frontend

```bash
npm install
npm run dev
```

---

## 🐳 Docker

Run the backend container:

```bash
docker build -t masr-backend .
docker run -p 8000:8000 masr-backend
```

Run full stack with Docker Compose:

```bash
docker compose up --build
```

---

## 🔧 Configuration

Simulation parameters can be adjusted:

* Number of satellites
* Orbit configuration
* Bandwidth limits
* Buffer sizes
* Routing policy
* Tick interval

Backend configuration can be overridden via environment variables:

* `MASR_SATELLITES_PER_ORBIT`, `MASR_NUM_ORBITS`, `MASR_ORBITAL_ALTITUDE_KM`
* `MASR_MAX_LINK_DISTANCE_KM`, `MASR_BUFFER_CAPACITY`, `MASR_BANDWIDTH`
* `MASR_TICK_INTERVAL`, `MASR_SEED`, `MASR_ROUTING_POLICY`
* `MASR_PACKET_TTL`, `MASR_PACKET_RETENTION_TICKS`
* `MASR_GS_LAT_DEG`, `MASR_GS_LON_DEG`
* `MASR_CONTACT_PREDICTION_HORIZON_TICKS`

Optional API protection and limits:

* `MASR_API_KEY` (require `X-API-Key` header)
* `MASR_RATE_LIMIT_PER_MIN` (per-IP rate limit)
* `MASR_MAX_REQUEST_BYTES` (request size cap)

Frontend API targets can be configured with Vite env vars:

* `VITE_API_URL` (default: `http://localhost:8000`)
* `VITE_WS_URL` (default: `ws://localhost:8000`)
* `VITE_API_KEY` (optional API key for HTTP + WS)

---

## 🧠 Design Principles

* Determinism over randomness
* Decentralized coordination
* Strict agent isolation
* Reproducibility
* Observability

---

## 📈 Use Cases

* Distributed systems research
* Network protocol experimentation
* Satellite communication modeling
* Systems engineering portfolio

---

## 🚀 Future Work

* Real orbital data (TLE integration)
* AI-based routing agents
* Replay and time-travel debugging
* WebGL 3D visualization
* Experiment benchmarking suite

---

## 🤝 Contributing

Contributions are welcome.
Focus areas:

* Routing algorithms
* Performance optimization
* Visualization improvements

---

## 📄 License

MIT License

---

## ⭐ Why This Project

MASR is not just another simulation — it is a **deterministic, multi-agent coordination framework** that bridges:

* distributed systems
* networking
* space systems
* simulation engineering

This makes it a **high-impact portfolio and research project**.

---
