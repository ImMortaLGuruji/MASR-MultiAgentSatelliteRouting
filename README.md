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
uvicorn backend.api.main:app --reload
```

---

### Frontend

```bash
npm install
npm run dev
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
