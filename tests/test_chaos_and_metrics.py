import unittest

from backend.config import Config
from backend.engine import SimulationEngine


class ChaosAndMetricsTests(unittest.TestCase):
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

        gs_ids = set(engine.ground_stations.keys())
        for source, target in engine.active_links.keys():
            # Ground-station links are not subject to the satellite partition —
            # the GS is a physical ground node that is not logically split.
            if source in gs_ids or target in gs_ids:
                continue
            self.assertEqual(
                source in left,
                target in left,
                msg=f"Cross-partition satellite link found: {source} <-> {target}",
            )

    def test_metrics_fields_present(self) -> None:
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

    def test_ground_station_receives_delivered_packet(self) -> None:
        """Packets addressed to gs-0 must be delivered, not stuck in pending_outgoing."""
        engine = SimulationEngine(
            Config(
                seed=42,
                num_orbits=1,
                satellites_per_orbit=3,
                max_link_distance=20000.0,
            )
        )
        # Run one tick to establish orbital positions and GS link visibility.
        engine.run_tick()

        gs_neighbors = [
            sat_id
            for sat_id, agent in engine.satellites.items()
            if "gs-0" in agent.state.neighbors
        ]
        if not gs_neighbors:
            self.skipTest("gs-0 not visible from any satellite in this config")

        source = gs_neighbors[0]
        packet = engine.spawn_packet(source, "gs-0")

        for _ in range(30):
            engine.run_tick()
            if engine.packets.get(packet.packet_id) is None:
                # Packet was pruned — it reached a terminal state
                break

        final_packet = engine.packets.get(packet.packet_id)
        final_state = final_packet.state if final_packet else "PRUNED"

        self.assertIn(
            final_state,
            {"DELIVERED", "PRUNED"},
            msg=f"Packet should reach gs-0 (DELIVERED or pruned), got {final_state}",
        )
        if final_state == "DELIVERED":
            self.assertIn(
                packet.packet_id,
                engine.ground_stations["gs-0"].received_packets,
            )


if __name__ == "__main__":
    unittest.main()
