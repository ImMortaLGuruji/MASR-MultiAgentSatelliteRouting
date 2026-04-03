import unittest

from fastapi.testclient import TestClient

from backend.api.app import app


class ApiContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.client.post("/runner/stop")
        self.client.post("/reset")
        self.client.post(
            "/config",
            json={
                "routing_policy": "SHORTEST_PATH",
                "drop_on_reject": False,
                "tick_interval": 1.0,
            },
        )

    def tearDown(self) -> None:
        self.client.post("/runner/stop")

    def test_config_update_reflects_in_state_payload(self) -> None:
        update = self.client.post(
            "/config",
            json={
                "routing_policy": "CONTACT_GRAPH_ROUTING",
                "drop_on_reject": True,
                "tick_interval": 0.5,
            },
        )
        self.assertEqual(update.status_code, 200)
        config = update.json()
        self.assertEqual(config["routing_policy"], "CONTACT_GRAPH_ROUTING")
        self.assertTrue(config["drop_on_reject"])
        self.assertEqual(config["runner_tick_interval"], 0.5)

        state_response = self.client.get("/state")
        self.assertEqual(state_response.status_code, 200)
        state = state_response.json()
        self.assertIn("config", state)
        self.assertIn("runner", state)
        self.assertEqual(state["config"]["routing_policy"], "CONTACT_GRAPH_ROUTING")
        self.assertTrue(state["config"]["drop_on_reject"])
        self.assertEqual(state["runner"]["tick_interval"], 0.5)

    def test_runner_lifecycle_endpoints(self) -> None:
        start = self.client.post("/runner/start")
        self.assertEqual(start.status_code, 200)
        self.assertTrue(start.json()["running"])

        status = self.client.get("/runner/status")
        self.assertEqual(status.status_code, 200)
        self.assertTrue(status.json()["running"])

        stop = self.client.post("/runner/stop")
        self.assertEqual(stop.status_code, 200)
        self.assertFalse(stop.json()["running"])

    def test_spawn_rejects_failed_source_satellite(self) -> None:
        fail = self.client.post(
            "/chaos",
            json={"mode": "random_satellite_failure", "count": 1},
        )
        self.assertEqual(fail.status_code, 200)
        disabled = fail.json().get("disabled", [])
        self.assertTrue(disabled)

        spawn = self.client.post(
            "/spawn_packet",
            json={
                "source": disabled[0],
                "destination": "sat-00-00",
                "priority": 1,
                "size": 1,
            },
        )
        self.assertEqual(spawn.status_code, 400)


if __name__ == "__main__":
    unittest.main()
