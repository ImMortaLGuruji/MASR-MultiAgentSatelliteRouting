import json
import unittest

from backend.config import Config
from backend.engine import SimulationEngine


class DeterminismTests(unittest.TestCase):
    def test_reproducible_run_snapshot(self) -> None:
        config = Config(
            seed=123, num_orbits=1, satellites_per_orbit=3, max_link_distance=20000.0
        )

        first = SimulationEngine(config)
        second = SimulationEngine(config)

        first.spawn_packet("sat-00-00", "sat-00-02", priority=2, size=1)
        second.spawn_packet("sat-00-00", "sat-00-02", priority=2, size=1)

        for _ in range(5):
            first.run_tick()
            second.run_tick()

        first_snapshot = json.dumps(first.snapshot(), sort_keys=True)
        second_snapshot = json.dumps(second.snapshot(), sort_keys=True)
        self.assertEqual(first_snapshot, second_snapshot)

    def test_reset_restores_initial_state(self) -> None:
        engine = SimulationEngine(
            Config(
                seed=7, num_orbits=1, satellites_per_orbit=2, max_link_distance=20000.0
            )
        )
        engine.spawn_packet("sat-00-00", "sat-00-01")
        engine.run_tick()
        engine.run_tick()

        engine.reset()

        self.assertEqual(engine.tick, 0)
        self.assertEqual(engine.metrics.total_packets, 0)
        self.assertEqual(len(engine.packets), 0)
        self.assertEqual(len(engine.satellites), 2)


if __name__ == "__main__":
    unittest.main()
