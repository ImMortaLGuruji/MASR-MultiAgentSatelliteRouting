import unittest
from typing import Any, Dict

from backend.models import PacketState
from backend.routing import ROUTING_STRATEGIES, RoutingPolicy, compute_next_hop


class RoutingPluginTests(unittest.TestCase):
    def setUp(self) -> None:
        self.packet = PacketState(
            packet_id="pkt-route",
            source="sat-a",
            destination="sat-d",
            priority=1,
            size=1,
            ttl=10,
            creation_tick=0,
            current_holder="sat-a",
            route_history=["sat-a"],
            state="IN_QUEUE",
        )

    def test_registry_contains_all_policies(self) -> None:
        for policy in RoutingPolicy:
            self.assertIn(policy.value, ROUTING_STRATEGIES)

    def test_shortest_path_uses_graph_context(self) -> None:
        context: Dict[str, Any] = {
            "adjacency": {
                "sat-a": {"sat-b", "sat-c"},
                "sat-b": {"sat-a", "sat-d"},
                "sat-c": {"sat-a"},
                "sat-d": {"sat-b"},
            }
        }
        next_hop = compute_next_hop(
            policy=RoutingPolicy.SHORTEST_PATH.value,
            packet=self.packet,
            current_id="sat-a",
            neighbors=["sat-b", "sat-c"],
            context=context,
        )
        self.assertEqual(next_hop, "sat-b")

    def test_contact_graph_uses_predicted_adjacency(self) -> None:
        context: Dict[str, Any] = {
            "adjacency": {
                "sat-a": {"sat-b", "sat-c"},
                "sat-b": {"sat-a"},
                "sat-c": {"sat-a"},
                "sat-d": set(),
            },
            "predicted_adjacency": {
                "sat-a": {"sat-b", "sat-c"},
                "sat-b": {"sat-a", "sat-d"},
                "sat-c": {"sat-a"},
                "sat-d": {"sat-b"},
            },
        }
        next_hop = compute_next_hop(
            policy=RoutingPolicy.CONTACT_GRAPH_ROUTING.value,
            packet=self.packet,
            current_id="sat-a",
            neighbors=["sat-b", "sat-c"],
            context=context,
        )
        self.assertEqual(next_hop, "sat-b")

    def test_unknown_policy_falls_back_to_shortest_path(self) -> None:
        # With no adjacency context, shortest_path returns None for a
        # destination that is not a direct neighbour.
        next_hop = compute_next_hop(
            policy="NOT_A_POLICY",
            packet=self.packet,
            current_id="sat-a",
            neighbors=["sat-c", "sat-b"],
            context={},
        )
        self.assertIsNone(next_hop)

    def test_store_and_forward_holds_when_path_not_found(self) -> None:
        """S&F returns None (hold) when topology known but destination unreachable."""
        from backend.routing.strategies import store_and_forward_strategy

        context: Dict[str, Any] = {
            "adjacency": {
                "sat-a": {"sat-b"},
                "sat-b": {"sat-a"},
                # sat-d completely absent — no path
            }
        }
        result = store_and_forward_strategy(self.packet, "sat-a", ["sat-b"], context)
        self.assertIsNone(
            result, "S&F should hold (None) when topology known but no path"
        )

    def test_store_and_forward_forwards_without_topology(self) -> None:
        """S&F falls back to unvisited-neighbour forwarding when no context available."""
        from backend.routing.strategies import store_and_forward_strategy

        result = store_and_forward_strategy(
            self.packet, "sat-a", ["sat-b", "sat-c"], {}
        )
        self.assertIn(result, ["sat-b", "sat-c"])

    def test_epidemic_does_not_loop_when_all_neighbors_visited(self) -> None:
        """Epidemic routing returns None when all neighbours are in route history."""
        from backend.routing.strategies import epidemic_strategy

        packet = PacketState(
            packet_id="pkt-ep",
            source="sat-a",
            destination="sat-d",
            priority=1,
            size=1,
            ttl=10,
            creation_tick=0,
            current_holder="sat-b",
            route_history=["sat-a", "sat-b", "sat-c"],  # all neighbours visited
            state="IN_QUEUE",
        )
        result = epidemic_strategy(packet, "sat-b", ["sat-a", "sat-c"], {})
        self.assertIsNone(
            result, "Epidemic should hold (None) when all neighbours visited"
        )


if __name__ == "__main__":
    unittest.main()
