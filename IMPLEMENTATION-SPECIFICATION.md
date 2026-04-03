# MASR – IMPLEMENTATION SPECIFICATION

### Deterministic Multi-Agent Satellite Routing System

---

# 0. GLOBAL IMPLEMENTATION CONTRACT

This section defines **non-negotiable system invariants**.

### 0.1 Determinism Rules

All implementations MUST follow:

```
1. No unordered iteration over dict/set without sorting
2. All randomness via seeded RNG only
3. Message delivery strictly ordered
4. No async race conditions affecting state
5. Engine loop must be single-thread deterministic core
```

### 0.2 Agent Isolation Rules

```
Agents MUST NOT:
- directly call methods of other agents
- mutate shared state
- access global registries

Agents MUST:
- communicate ONLY via message bus
```

---

# 1. CORE DATA MODELS

---

## 1.1 Global ID Types

```
AgentID = str
PacketID = str
MessageID = str
Tick = int
```

---

## 1.2 Vector3 (Position Model)

```
class Vector3:
    x: float
    y: float
    z: float
```

---

## 1.3 SatelliteState

```
class SatelliteState:
    satellite_id: str
    orbit_index: int
    position: Vector3
    neighbors: List[str]
    buffer_capacity: int
    bandwidth_capacity: float
    packet_queue: List[PacketID]
    link_table: Dict[str, LinkState]
    routing_policy: str
```

---

## 1.4 PacketState

```
class PacketState:
    packet_id: str
    source: str
    destination: str
    priority: int
    size: int
    ttl: int
    creation_tick: int
    current_holder: str
    route_history: List[str]
    state: str
```

---

## 1.5 LinkState

```
class LinkState:
    source: str
    target: str
    bandwidth: float
    delay: float
    quality: float
    active: bool
```

---

## 1.6 Message Object

```
class Message:
    message_id: str
    tick: int
    sender: str
    receiver: str
    type: str
    payload: Dict
```

---

# 2. ENGINE CORE

---

## 2.1 SimulationEngine Class

```
class SimulationEngine:

    def __init__(self, config):
        self.tick = 0
        self.config = config
        self.agents = {}
        self.message_bus = MessageBus()
        self.metrics = MetricsCollector()
        self.random = SeededRandom(config.seed)
```

---

## 2.2 Engine Main Loop

```
def run_tick():

    update_orbital_positions()

    compute_link_visibility()

    generate_link_events()

    message_bus.deliver_messages()

    process_agents()

    process_transfers()

    update_metrics()

    broadcast_snapshot()

    tick += 1
```

---

## 2.3 Deterministic Agent Processing

```
def process_agents():

    sorted_agents = sort(agent_ids)

    for agent_id in sorted_agents:
        agent = agents[agent_id]
        agent.process_tick()
```

---

# 3. MESSAGE BUS

---

## 3.1 MessageBus Class

```
class MessageBus:

    def __init__():
        self.queue = []

    def send(message):
        self.queue.append(message)

    def deliver_messages():
        sort queue by:
            (tick, sender, receiver, message_id)

        for message in queue:
            deliver(message)

        clear queue
```

---

## 3.2 Delivery Mechanism

```
def deliver(message):

    receiver = agents[message.receiver]

    receiver.receive(message)
```

---

# 4. AGENT BASE CLASS

---

```
class BaseAgent:

    def __init__(id):
        self.id = id
        self.inbox = []

    def receive(message):
        self.inbox.append(message)

    def process_tick():
        process_messages()
        perform_actions()

    def process_messages():
        for message in sorted(inbox):
            handle(message)

        clear inbox
```

---

# 5. SATELLITE AGENT

---

## 5.1 Initialization

```
class SatelliteAgent(BaseAgent):

    def __init__(state):
        self.state = state
```

---

## 5.2 Tick Processing

```
def process_tick():

    update_neighbors()

    process_messages()

    routing_step()

    manage_queue()
```

---

## 5.3 Routing Step

```
def routing_step():

    for packet in sorted(packet_queue):

        next_hop = routing_policy(packet)

        if next_hop exists:
            send_packet_offer(packet, next_hop)
```

---

## 5.4 Packet Offer

```
def send_packet_offer(packet, neighbor):

    message = Message(
        type="PACKET_OFFER",
        payload={
            packet_id,
            priority,
            size,
            destination
        }
    )

    message_bus.send(message)
```

---

## 5.5 Message Handlers

```
def handle(message):

    if message.type == "PACKET_OFFER":
        handle_offer(message)

    elif message.type == "PACKET_ACCEPT":
        handle_accept(message)

    elif message.type == "PACKET_REJECT":
        handle_reject(message)
```

---

## 5.6 Offer Handling

```
def handle_offer(msg):

    if buffer_available():

        send_accept(msg)

    else:

        send_reject(msg)
```

---

## 5.7 Accept Handling

```
def handle_accept(msg):

    transfer_packet(msg.packet_id, msg.sender)
```

---

# 6. PACKET TRANSFER SYSTEM

---

## 6.1 Transfer Execution

```
def process_transfers():

    for transfer in scheduled_transfers:

        move_packet(transfer)
```

---

## 6.2 Move Packet

```
def move_packet(transfer):

    packet.current_holder = transfer.target

    update route history
```

---

# 7. ROUTING ALGORITHMS

---

## 7.1 Shortest Path

```
def shortest_path(packet, satellite):

    graph = build_predicted_graph()

    return dijkstra(graph, source, destination)
```

---

## 7.2 Epidemic Routing

```
def epidemic(packet):

    for neighbor in neighbors:

        if neighbor not in packet.route_history:
            send_offer(packet)
```

---

## 7.3 Contact Graph Routing

```
def contact_graph(packet):

    predicted_links = predict_links()

    build temporal graph

    compute best route
```

---

# 8. ORBITAL MODEL

---

## 8.1 Update Position

```
def update_position(satellite):

    theta = angular_velocity * tick

    x = R * cos(theta)
    y = R * sin(theta)
    z = inclination_factor
```

---

# 9. LINK SYSTEM

---

## 9.1 Link Computation

```
def compute_links():

    for each satellite pair:

        if distance < threshold:

            create_link()
```

---

## 9.2 Distance Calculation

```
distance = sqrt(
    (x1-x2)^2 +
    (y1-y2)^2 +
    (z1-z2)^2
)
```

---

# 10. CONGESTION SYSTEM

---

## 10.1 Queue Control

```
if queue_size > buffer_capacity:

    drop_lowest_priority_packet()
```

---

## 10.2 Priority Preemption

```
if new_packet.priority > lowest.priority:

    replace_packet()
```

---

# 11. METRICS SYSTEM

---

## 11.1 MetricsCollector

```
class MetricsCollector:

    total_packets
    delivered_packets
    dropped_packets
    total_latency
```

---

## 11.2 Update Metrics

```
def record_delivery(packet):

    latency = current_tick - packet.creation_tick

    total_latency += latency
```

---

# 12. SNAPSHOT SYSTEM

---

## 12.1 Snapshot Structure

```
{
    tick,
    satellites,
    links,
    packets,
    metrics
}
```

---

# 13. API LAYER

---

## 13.1 FastAPI Setup

```
@app.get("/state")
def get_state()

@app.post("/spawn_packet")
def spawn_packet()

@app.post("/reset")
def reset()
```

---

# 14. CHAOS MODE

---

## 14.1 Chaos Events

```
spawn_mass_packets()
disable_random_satellites()
reduce_bandwidth()
```

---

# 15. CONFIGURATION

---

```
class Config:

    satellites_per_orbit
    num_orbits
    max_link_distance
    buffer_capacity
    bandwidth
    seed
```

---

# 16. FILE STRUCTURE

---

```
backend/
    engine/
    agents/
    routing/
    orbital/
    messaging/
    metrics/
    api/
```

---

# 17. ENGINE THREAD MODEL

---

```
main thread → API
background thread → simulation loop
```

---

# 18. EXTENSIBILITY CONTRACT

---

New routing algorithm must implement:

```
def compute_next_hop(packet, satellite)
```

---

# 19. TESTING STRATEGY

---

```
1. Determinism tests
2. Routing correctness tests
3. Congestion stress tests
4. Chaos mode tests
```

---

# 20. FINAL GUARANTEE

If implemented correctly:

* system is **fully deterministic**
* agents are **fully isolated**
* routing is **fully emergent**
* simulation is **fully reproducible**
