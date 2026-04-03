from __future__ import annotations

from collections import deque
from typing import Any, Callable, Dict, Iterable, Mapping, Optional, Set, cast

from backend.models import PacketState

RoutingContext = Mapping[str, Any]
RoutingStrategy = Callable[
    [PacketState, str, Iterable[str], RoutingContext], Optional[str]
]


def _ordered_neighbors(neighbors: Iterable[str]) -> list[str]:
    return sorted(neighbors)


def _adjacency_from_context(context: RoutingContext) -> Dict[str, Set[str]]:
    raw = context.get("adjacency", {})
    adjacency: Dict[str, Set[str]] = {}
    if isinstance(raw, Mapping):
        typed_raw = cast(Mapping[object, Iterable[object]], raw)
        for node, linked in typed_raw.items():
            adjacency[str(node)] = set(str(item) for item in linked)
    return adjacency


def _bfs_next_hop(
    current_id: str, destination: str, adjacency: Dict[str, Set[str]]
) -> Optional[str]:
    if current_id == destination:
        return None
    if current_id not in adjacency:
        return None

    queue: deque[str] = deque([current_id])
    parents: Dict[str, Optional[str]] = {current_id: None}

    while queue:
        node = queue.popleft()
        for neighbor in sorted(adjacency.get(node, set())):
            if neighbor in parents:
                continue
            parents[neighbor] = node
            if neighbor == destination:
                cursor = destination
                while parents.get(cursor) != current_id:
                    parent = parents.get(cursor)
                    if parent is None:
                        return None
                    cursor = parent
                return cursor
            queue.append(neighbor)
    return None


def shortest_path_strategy(
    packet: PacketState,
    current_id: str,
    neighbors: Iterable[str],
    context: RoutingContext,
) -> Optional[str]:
    ordered = _ordered_neighbors(neighbors)
    if not ordered:
        return None

    if packet.destination in ordered:
        return packet.destination

    adjacency = _adjacency_from_context(context)
    if adjacency:
        next_hop = _bfs_next_hop(current_id, packet.destination, adjacency)
        if next_hop is not None and next_hop in ordered:
            return next_hop

    return ordered[0]


def epidemic_strategy(
    packet: PacketState,
    current_id: str,
    neighbors: Iterable[str],
    context: RoutingContext,
) -> Optional[str]:
    ordered = _ordered_neighbors(neighbors)
    if not ordered:
        return None

    for neighbor in ordered:
        if neighbor not in packet.route_history:
            return neighbor
    return ordered[0]


def store_and_forward_strategy(
    packet: PacketState,
    current_id: str,
    neighbors: Iterable[str],
    context: RoutingContext,
) -> Optional[str]:
    ordered = _ordered_neighbors(neighbors)
    if not ordered:
        return None

    if packet.destination in ordered:
        return packet.destination

    adjacency = _adjacency_from_context(context)
    if adjacency:
        next_hop = _bfs_next_hop(current_id, packet.destination, adjacency)
        if next_hop is not None and next_hop in ordered:
            return next_hop

    return ordered[0]


def contact_graph_strategy(
    packet: PacketState,
    current_id: str,
    neighbors: Iterable[str],
    context: RoutingContext,
) -> Optional[str]:
    ordered = _ordered_neighbors(neighbors)
    if not ordered:
        return None

    predicted = context.get("predicted_adjacency")
    if isinstance(predicted, Mapping):
        typed_predicted = cast(Mapping[object, Iterable[object]], predicted)
        adjacency: Dict[str, Set[str]] = {}
        for node, linked in typed_predicted.items():
            adjacency[str(node)] = set(str(item) for item in linked)
        next_hop = _bfs_next_hop(current_id, packet.destination, adjacency)
        if next_hop is not None and next_hop in ordered:
            return next_hop

    if packet.destination in ordered:
        return packet.destination
    return ordered[0]
