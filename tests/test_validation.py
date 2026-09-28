import json
import tempfile
import unittest
from pathlib import Path

from rdtx.reporting import save_stats
from rdtx.sender import SenderStats


class ValidationTests(unittest.TestCase):
    def test_stats_version(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "stats.json"
            save_stats(target, "sender", SenderStats(file_bytes=100, elapsed=0.5))
            self.assertEqual(json.loads(target.read_text())["version"], "2.2.0")


if __name__ == "__main__":
    unittest.main()
