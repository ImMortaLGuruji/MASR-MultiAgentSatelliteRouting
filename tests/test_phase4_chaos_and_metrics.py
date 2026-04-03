import unittest

from backend.config import Config
from backend.engine import SimulationEngine


class Phase4ChaosAndMetricsTests(unittest.TestCase):
    def test_random_satellite_failure_is_deterministic(self) -> None:
        config = Config(
            seed=99, num_orbits=2, satellites_per_orbit=3, max_link_distance=20000.0
        )
        first = SimulationEngine(config)
        second = SimulationEngine(config)

        first.run_tick()
        second.run_tick()

        disabled_first = first.disable_random_satellites(2)
        disabled_second = second.disable_random_satellites(2)

        self.assertEqual(disabled_first, disabled_second)
        self.assertEqual(
            sorted(first.failed_satellites), sorted(second.failed_satellites)
        )

    def test_network_partition_blocks_cross_partition_links(self) -> None:
        engine = SimulationEngine(
            Config(
                seed=11, num_orbits=1, satellites_per_orbit=4, max_link_distance=30000.0
            )
        )
        engine.run_tick()

        ids = sorted(engine.satellites.keys())
        left = set(ids[: len(ids) // 2])

        engine.set_network_partition(True)
        engine.run_tick()

        for source, target in engine.active_links.keys():
            self.assertEqual(source in left, target in left)

    def test_phase4_metrics_fields_present(self) -> None:
        engine = SimulationEngine(
            Config(
                seed=15, num_orbits=1, satellites_per_orbit=3, max_link_distance=20000.0
            )
        )
        engine.spawn_packet("sat-00-00", "sat-00-02", size=8)
        for _ in range(4):
            engine.run_tick()

        metrics = engine.metrics.snapshot(current_tick=engine.tick)

        self.assertIn("throughput", metrics)
        self.assertIn("link_utilization", metrics)
        self.assertIn("satellite_buffer_usage", metrics)
        self.assertIn("packet_drop_rate", metrics)
        self.assertGreaterEqual(metrics["packet_drop_rate"], 0.0)
        self.assertLessEqual(metrics["packet_drop_rate"], 1.0)


if __name__ == "__main__":
    unittest.main()
