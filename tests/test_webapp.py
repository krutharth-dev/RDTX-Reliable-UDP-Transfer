import io
import socket
import tempfile
import threading
import time
import unittest

from rdtx.receiver import RDTXReceiver
from webapp.app import create_app


def free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class VisualLabTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.app = create_app({"TESTING": True, "DATA_DIR": self.temp.name, "MAX_ACTIVE_RUNS": 3})
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp.cleanup()

    def data(self, payload=b"visual-lab-test" * 200, **overrides):
        base = {
            "file": (io.BytesIO(payload), "sample.bin"),
            "mode": "local",
            "label": "web test",
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
        base.update(overrides)
        return base

    def wait_run(self, run_id, timeout=7):
        deadline = time.time() + timeout
        while time.time() < deadline:
            run = self.client.get(f"/api/runs/{run_id}").get_json()
            if run["status"] in {"completed", "failed"}:
                return run
            time.sleep(0.05)
        self.fail("run did not finish")

    def wait_matrix(self, matrix_id, timeout=15):
        deadline = time.time() + timeout
        while time.time() < deadline:
            job = self.client.get(f"/api/matrix/{matrix_id}").get_json()
            if str(job["status"]).startswith("completed"):
                return job
            time.sleep(0.1)
        self.fail("matrix did not finish")

    def test_local_run_report_export_and_download(self):
        original = b"visual-lab-test" * 200
        response = self.client.post("/api/runs", data=self.data(original), content_type="multipart/form-data")
        self.assertEqual(response.status_code, 202)
        run_id = response.get_json()["run_id"]
        run = self.wait_run(run_id)
        self.assertEqual(run["status"], "completed")
        self.assertEqual(run["result"]["integrity"], "PASS")
        self.assertGreater(run["result"]["sender"]["reordered_pairs"], 0)
        report = self.client.get(f"/api/runs/{run_id}/report.md")
        self.assertEqual(report.status_code, 200)
        self.assertIn(b"RDTX VisualLab Experiment Report", report.data)
        exported = self.client.get(f"/api/runs/{run_id}/export")
        self.assertEqual(exported.status_code, 200)
        downloaded = self.client.get(f"/api/runs/{run_id}/download")
        self.assertEqual(downloaded.data, original)

    def test_lan_mode_transfers_to_external_receiver(self):
        port = free_port()
        output = tempfile.TemporaryDirectory()
        receiver = RDTXReceiver("127.0.0.1", port, output_dir=output.name, linger=0.1, verbose=False)
        state = {}
        def receive():
            state["value"] = receiver.receive_one()
        thread = threading.Thread(target=receive, daemon=True)
        thread.start()
        response = self.client.post(
            "/api/runs",
            data=self.data(b"two-host-lan" * 300, mode="lan", reorder="0", target_host="127.0.0.1", target_port=str(port)),
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 202)
        run = self.wait_run(response.get_json()["run_id"])
        thread.join(timeout=2)
        self.assertEqual(run["status"], "completed")
        self.assertEqual(run["result"]["mode"], "lan")
        self.assertIn("FIN_ACK", run["result"]["verification"])
        output.cleanup()

    def test_matrix_window_sweep_and_report(self):
        response = self.client.post(
            "/api/matrix",
            data=self.data(b"matrix-data" * 200, reorder="0", dimension="window_size", values="1,2,4"),
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 202)
        matrix_id = response.get_json()["matrix_id"]
        job = self.wait_matrix(matrix_id)
        self.assertEqual(job["status"], "completed")
        self.assertEqual(len(job["rows"]), 3)
        self.assertTrue(all(row["result"]["integrity"] == "PASS" for row in job["rows"]))
        report = self.client.get(f"/api/matrix/{matrix_id}/report.md")
        self.assertEqual(report.status_code, 200)
        self.assertIn(b"Experiment Matrix Report", report.data)

    def test_health_mentions_lan_mode(self):
        health = self.client.get("/api/health").get_json()
        self.assertIn("lan", health["modes"])

    def test_invalid_matrix_rejected(self):
        response = self.client.post(
            "/api/matrix",
            data=self.data(dimension="window_size", values="0,100"),
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 400)

    def test_non_finite_impairment_rejected(self):
        response = self.client.post("/api/runs", data=self.data(loss="nan"), content_type="multipart/form-data")
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
