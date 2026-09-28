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
            "MAX_ACTIVE_RUNS": 2,
        })
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp.cleanup()

    def start_run(self, payload=b"visual-lab-test" * 200, **overrides):
        data = {
            "file": (io.BytesIO(payload), "sample.bin"),
            "label": "automated web test",
            "window_size": "4",
            "chunk_size": "256",
            "timeout_ms": "100",
            "loss": "0",
            "ack_loss": "0",
            "corruption": "0",
            "ack_corruption": "0",
            "reorder": "100",
            "delay_ms": "0",
            "ack_delay_ms": "0",
            "seed": "7",
        }
        data.update(overrides)
        return self.client.post("/api/runs", data=data, content_type="multipart/form-data")

    def wait_for_run(self, run_id):
        deadline = time.time() + 5
        while time.time() < deadline:
            run = self.client.get(f"/api/runs/{run_id}").get_json()
            if run["status"] in {"completed", "failed"}:
                return run
            time.sleep(0.05)
        self.fail("VisualLab run did not finish")

    def test_dashboard_and_health_load(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"RDTX VisualLab", response.data)
        self.assertIn(b"Recent experiment comparison", response.data)

        health = self.client.get("/api/health")
        self.assertEqual(health.status_code, 200)
        payload = health.get_json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["transport"], "UDP")
        self.assertEqual(payload["arq"], "Selective Repeat")

    def test_real_udp_experiment_export_and_download(self):
        original = b"visual-lab-test" * 200
        response = self.start_run(payload=original)
        self.assertEqual(response.status_code, 202)
        run_id = response.get_json()["run_id"]
        run = self.wait_for_run(run_id)

        self.assertEqual(run["status"], "completed")
        self.assertEqual(run["result"]["integrity"], "PASS")
        self.assertGreater(run["result"]["sender"]["reordered_pairs"], 0)
        self.assertEqual(run["params"]["label"], "automated web test")

        exported = self.client.get(f"/api/runs/{run_id}/export")
        self.assertEqual(exported.status_code, 200)
        self.assertIn(run_id.encode(), exported.data)
        self.assertIn("attachment", exported.headers["Content-Disposition"])

        downloaded = self.client.get(f"/api/runs/{run_id}/download")
        self.assertEqual(downloaded.status_code, 200)
        self.assertEqual(downloaded.data, original)

        csv_response = self.client.get("/api/history.csv")
        self.assertEqual(csv_response.status_code, 200)
        self.assertIn(b"run_id,label,filename", csv_response.data)
        self.assertIn(b"automated web test", csv_response.data)

    def test_invalid_impairment_is_rejected(self):
        response = self.start_run(loss="nan")
        self.assertEqual(response.status_code, 400)
        self.assertIn("packet loss must be between 0 and 100", response.get_json()["error"])

    def test_upload_limit_returns_json_error(self):
        limited = create_app({
            "TESTING": True,
            "DATA_DIR": self.temp.name + "-limited",
            "MAX_CONTENT_LENGTH": 256,
        }).test_client()
        response = limited.post(
            "/api/runs",
            data={
                "file": (io.BytesIO(b"x" * 1024), "too-large.bin"),
                "window_size": "4",
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 413)
        self.assertIn("Maximum upload size", response.get_json()["error"])


if __name__ == "__main__":
    unittest.main()
