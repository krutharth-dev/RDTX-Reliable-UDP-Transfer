import io
import tempfile
import time
import unittest

from webapp.app import create_app


class VisualLabTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.app = create_app({
            "TESTING": True,
            "DATA_DIR": self.temp.name,
        })
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp.cleanup()

    def test_dashboard_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"RDTX VisualLab", response.data)

    def test_real_udp_experiment_completes(self):
        response = self.client.post(
            "/api/runs",
            data={
                "file": (io.BytesIO(b"visual-lab-test" * 200), "sample.bin"),
                "window_size": "4",
                "chunk_size": "256",
                "timeout_ms": "100",
                "loss": "0",
                "ack_loss": "0",
                "corruption": "0",
                "reorder": "100",
                "delay_ms": "0",
                "seed": "7",
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 202)
        run_id = response.get_json()["run_id"]

        run = None
        deadline = time.time() + 5
        while time.time() < deadline:
            run = self.client.get(f"/api/runs/{run_id}").get_json()
            if run["status"] in {"completed", "failed"}:
                break
            time.sleep(0.05)

        self.assertIsNotNone(run)
        self.assertEqual(run["status"], "completed")
        self.assertEqual(run["result"]["integrity"], "PASS")
        self.assertGreater(run["result"]["sender"]["reordered_pairs"], 0)

        history = self.client.get("/api/history").get_json()
        self.assertEqual(history[0]["id"], run_id)


if __name__ == "__main__":
    unittest.main()
