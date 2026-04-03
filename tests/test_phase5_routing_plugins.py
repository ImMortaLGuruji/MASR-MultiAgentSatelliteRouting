import unittest
from typing import Any, Dict

from backend.models import PacketState
from backend.routing import ROUTING_STRATEGIES, RoutingPolicy, compute_next_hop


class Phase5RoutingPluginTests(unittest.TestCase):
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
        next_hop = compute_next_hop(
            policy="NOT_A_POLICY",
            packet=self.packet,
            current_id="sat-a",
            neighbors=["sat-c", "sat-b"],
            context={},
        )
        self.assertEqual(next_hop, "sat-b")


if __name__ == "__main__":
    unittest.main()
