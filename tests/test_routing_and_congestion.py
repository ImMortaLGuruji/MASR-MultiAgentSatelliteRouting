import unittest

from backend.config import Config
from backend.engine import SimulationEngine
from backend.models import Message, PacketState
from backend.routing import RoutingPolicy, compute_next_hop


class RoutingAndCongestionTests(unittest.TestCase):
    def test_shortest_path_prefers_destination_neighbor(self) -> None:
        packet = PacketState(
            packet_id="pkt-x",
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
        next_hop = compute_next_hop(
            RoutingPolicy.SHORTEST_PATH.value,
            packet,
            current_id="sat-a",
            neighbors=["sat-b", "sat-d", "sat-c"],
        )
        self.assertEqual(next_hop, "sat-d")

    def test_message_ordering_is_deterministic(self) -> None:
        config = Config(seed=1, num_orbits=1, satellites_per_orbit=2)
        engine = SimulationEngine(config)

        received: list[Message] = []
        messages = [
            Message("m3", 2, "sat-00-01", "sat-00-00", "X", {}),
            Message("m1", 1, "sat-00-01", "sat-00-00", "X", {}),
            Message("m2", 1, "sat-00-00", "sat-00-01", "X", {}),
            Message("m4", 2, "sat-00-00", "sat-00-01", "X", {}),
        ]
        for message in messages:
            engine.message_bus.send(message)

        engine.message_bus.deliver_messages(lambda message: received.append(message))

        order = [message.message_id for message in received]
        self.assertEqual(order, ["m2", "m1", "m4", "m3"])

    def test_rejected_offer_keeps_packet_queued(self) -> None:
        config = Config(
            seed=5,
            num_orbits=1,
            satellites_per_orbit=2,
            max_link_distance=20000.0,
            buffer_capacity=3,
        )
        engine = SimulationEngine(config)

        target_id = "sat-00-01"
        engine.satellites[target_id].state.buffer_capacity = 0

        packet = engine.spawn_packet("sat-00-00", target_id)

        for _ in range(3):
            engine.run_tick()

        self.assertEqual(engine.packets[packet.packet_id].state, "IN_QUEUE")
        self.assertEqual(engine.metrics.dropped_packets, 0)

    def test_rejected_offer_drops_packet_in_strict_mode(self) -> None:
        config = Config(
            seed=5,
            num_orbits=1,
            satellites_per_orbit=2,
            max_link_distance=20000.0,
            buffer_capacity=3,
            drop_on_reject=True,
        )
        engine = SimulationEngine(config)

        target_id = "sat-00-01"
        engine.satellites[target_id].state.buffer_capacity = 0

        packet = engine.spawn_packet("sat-00-00", target_id)

        for _ in range(3):
            engine.run_tick()

        self.assertEqual(engine.packets[packet.packet_id].state, "DROPPED")
        self.assertEqual(engine.metrics.dropped_packets, 1)


if __name__ == "__main__":
    unittest.main()
