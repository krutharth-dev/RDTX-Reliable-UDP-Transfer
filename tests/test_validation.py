import json
import tempfile
import unittest
from pathlib import Path

from rdtx.protocol import ProtocolError, json_payload
from rdtx.receiver import RDTXReceiver
from rdtx.reporting import save_stats
from rdtx.sender import SenderStats


class ValidationTests(unittest.TestCase):
    def valid_metadata(self):
        return {
            "filename": "demo.bin",
            "size": 2048,
            "sha256": "a" * 64,
            "chunk_size": 1024,
            "total_chunks": 2,
            "window_size": 8,
        }

    def test_receiver_accepts_consistent_metadata(self):
        metadata = RDTXReceiver._validate_metadata(json_payload(self.valid_metadata()))
        self.assertEqual(metadata["total_chunks"], 2)
        self.assertEqual(metadata["filename"], "demo.bin")

    def test_receiver_rejects_inconsistent_chunk_count(self):
        metadata = self.valid_metadata()
        metadata["total_chunks"] = 3
        with self.assertRaises(ProtocolError):
            RDTXReceiver._validate_metadata(json_payload(metadata))

    def test_receiver_sanitizes_filename(self):
        metadata = self.valid_metadata()
        metadata["filename"] = "../../outside.txt"
        validated = RDTXReceiver._validate_metadata(json_payload(metadata))
        self.assertEqual(validated["filename"], "outside.txt")

    def test_stats_export_is_structured_json(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "stats.json"
            stats = SenderStats(file_bytes=100, data_packets=2, elapsed=0.5)
            save_stats(target, "sender", stats, scenario="unit-test")
            payload = json.loads(target.read_text(encoding="utf-8"))

            self.assertEqual(payload["project"], "RDTX")
            self.assertEqual(payload["version"], "1.1.0")
            self.assertEqual(payload["role"], "sender")
            self.assertEqual(payload["context"]["scenario"], "unit-test")
            self.assertEqual(payload["stats"]["file_bytes"], 100)


if __name__ == "__main__":
    unittest.main()
