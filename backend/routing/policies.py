from enum import Enum
from typing import Iterable, Optional

from backend.models import PacketState


class RoutingPolicy(str, Enum):
    SHORTEST_PATH = "SHORTEST_PATH"
    EPIDEMIC = "EPIDEMIC"
    STORE_AND_FORWARD = "STORE_AND_FORWARD"
    CONTACT_GRAPH_ROUTING = "CONTACT_GRAPH_ROUTING"


def compute_next_hop(
    policy: str, packet: PacketState, current_id: str, neighbors: Iterable[str]
) -> Optional[str]:
    ordered_neighbors = sorted(neighbors)
    if not ordered_neighbors:
        return None

    if policy == RoutingPolicy.SHORTEST_PATH.value:
        if packet.destination in ordered_neighbors:
            return packet.destination
        return ordered_neighbors[0]

    if policy == RoutingPolicy.EPIDEMIC.value:
        for neighbor in ordered_neighbors:
            if neighbor not in packet.route_history:
                return neighbor
        return ordered_neighbors[0]

    if policy == RoutingPolicy.STORE_AND_FORWARD.value:
        if packet.destination in ordered_neighbors:
            return packet.destination
        return ordered_neighbors[0]

    if policy == RoutingPolicy.CONTACT_GRAPH_ROUTING.value:
        if packet.destination in ordered_neighbors:
            return packet.destination
        return ordered_neighbors[0]

    return ordered_neighbors[0]
