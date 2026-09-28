import tempfile
import unittest
from pathlib import Path

from experiments.benchmark import write_markdown


class BenchmarkReportTests(unittest.TestCase):
    def test_markdown_report_contains_report_ready_table(self):
        rows = [{
            "scenario": "reorder_all_pairs",
            "data_loss": 0.0,
            "ack_loss": 0.0,
            "corruption": 0.0,
            "reorder": 1.0,
            "window": 8,
            "file_bytes": 8192,
            "elapsed_s": "0.100000",
            "throughput_kib_s": "80.000",
            "retransmissions": 0,
            "simulated_drops": 0,
            "simulated_corruptions": 0,
            "reordered_pairs": 4,
            "receiver_duplicates": 0,
            "receiver_checksum_errors": 0,
            "integrity": "PASS",
        }]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "benchmark.md"
            write_markdown(path, rows, size_kib=8, seed=2026)
            report = path.read_text(encoding="utf-8")

        self.assertIn("# RDTX Benchmark Results", report)
        self.assertIn("reorder_all_pairs", report)
        self.assertIn("100%", report)
        self.assertIn("PASS", report)


if __name__ == "__main__":
    unittest.main()
