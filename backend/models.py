from dataclasses import dataclass, field
from typing import Any, Dict, List

AgentID = str
PacketID = str
MessageID = str
Tick = int


@dataclass(frozen=True)
class Vector3:
    x: float
    y: float
    z: float


@dataclass
class LinkState:
    source: str
    target: str
    bandwidth: float
    delay: float
    quality: float
    active: bool = True


@dataclass
class SatelliteState:
    satellite_id: str
    orbit_index: int
    position: Vector3
    neighbors: List[str] = field(default_factory=list)
    buffer_capacity: int = 0
    bandwidth_capacity: float = 0.0
    packet_queue: List[PacketID] = field(default_factory=list)
    link_table: Dict[str, LinkState] = field(default_factory=dict)
    routing_policy: str = "SHORTEST_PATH"

    # Energy model
    battery_capacity: float = 100.0
    current_battery: float = 100.0
    in_eclipse: bool = False


@dataclass
class PacketState:
    packet_id: str
    source: str
    destination: str
    priority: int
    size: int
    ttl: int
    creation_tick: int
    current_holder: str
    route_history: List[str] = field(default_factory=list)
    state: str = "CREATED"


@dataclass(frozen=True)
class Message:
    message_id: str
    tick: int
    sender: str
    receiver: str
    type: str
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Transfer:
    packet_id: str
    source: str
    target: str
