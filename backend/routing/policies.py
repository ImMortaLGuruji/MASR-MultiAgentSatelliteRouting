from enum import Enum
from typing import Dict, Iterable, Optional

from backend.models import PacketState
from backend.routing.strategies import (
    RoutingContext,
    RoutingStrategy,
    contact_graph_strategy,
    epidemic_strategy,
    shortest_path_strategy,
    store_and_forward_strategy,
)


class RoutingPolicy(str, Enum):
    SHORTEST_PATH = "SHORTEST_PATH"
    EPIDEMIC = "EPIDEMIC"
    STORE_AND_FORWARD = "STORE_AND_FORWARD"
    CONTACT_GRAPH_ROUTING = "CONTACT_GRAPH_ROUTING"


ROUTING_STRATEGIES: Dict[str, RoutingStrategy] = {
    RoutingPolicy.SHORTEST_PATH.value: shortest_path_strategy,
    RoutingPolicy.EPIDEMIC.value: epidemic_strategy,
    RoutingPolicy.STORE_AND_FORWARD.value: store_and_forward_strategy,
    RoutingPolicy.CONTACT_GRAPH_ROUTING.value: contact_graph_strategy,
}


def compute_next_hop(
    policy: str,
    packet: PacketState,
    current_id: str,
    neighbors: Iterable[str],
    context: Optional[RoutingContext] = None,
) -> Optional[str]:
    ordered_neighbors = sorted(neighbors)
    if not ordered_neighbors:
        return None

    strategy = ROUTING_STRATEGIES.get(policy)
    if strategy is None:
        return ordered_neighbors[0]

    strategy = strategy or shortest_path_strategy
    return strategy(packet, current_id, ordered_neighbors, context or {})
