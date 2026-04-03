import unittest

from backend.config import Config
from backend.engine import SimulationEngine


class Phase6PriorityCongestionTests(unittest.TestCase):
    def test_spawn_preempts_lowest_priority_when_full(self) -> None:
        engine = SimulationEngine(
            Config(seed=21, num_orbits=1, satellites_per_orbit=2, buffer_capacity=2)
        )

        low = engine.spawn_packet("sat-00-00", "sat-00-01", priority=1)
        mid = engine.spawn_packet("sat-00-00", "sat-00-01", priority=2)
        high = engine.spawn_packet("sat-00-00", "sat-00-01", priority=5)

        queue = engine.satellites["sat-00-00"].state.packet_queue
        self.assertNotIn(low.packet_id, queue)
        self.assertIn(mid.packet_id, queue)
        self.assertIn(high.packet_id, queue)
        self.assertEqual(engine.packets[low.packet_id].state, "DROPPED")

    def test_transfer_preempts_lowest_priority_when_full(self) -> None:
        engine = SimulationEngine(
            Config(
                seed=22,
                num_orbits=1,
                satellites_per_orbit=2,
                buffer_capacity=2,
                max_link_distance=30000.0,
            )
        )

        target = "sat-00-01"
        existing_low = engine.spawn_packet(target, "sat-00-00", priority=1)
        existing_mid = engine.spawn_packet(target, "sat-00-00", priority=2)

        incoming = engine.spawn_packet("sat-00-00", target, priority=9)

        engine.schedule_transfer(incoming.packet_id, "sat-00-00", target)
        engine.process_transfers()

        target_queue = engine.satellites[target].state.packet_queue
        self.assertNotIn(existing_low.packet_id, target_queue)
        self.assertIn(existing_mid.packet_id, target_queue)
        self.assertEqual(engine.packets[incoming.packet_id].state, "DELIVERED")
        self.assertEqual(engine.packets[existing_low.packet_id].state, "DROPPED")


if __name__ == "__main__":
    unittest.main()
