import subprocess
import sys
import unittest


class CLITests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "rdtx", *args],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_top_level_help(self):
        result = self.run_cli("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("reliable file transfer over UDP", result.stdout)
        self.assertIn("send", result.stdout)
        self.assertIn("receive", result.stdout)

    def test_version(self):
        result = self.run_cli("--version")
        self.assertEqual(result.returncode, 0)
        self.assertIn("RDTX 1.2.0", result.stdout)

    def test_send_help(self):
        result = self.run_cli("send", "--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("--stats-json", result.stdout)
        self.assertIn("--trace", result.stdout)


if __name__ == "__main__":
    unittest.main()
