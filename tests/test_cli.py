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
        self.assertIn("reliable file transfer", result.stdout)
        self.assertIn("send", result.stdout)
        self.assertIn("receive", result.stdout)
        self.assertIn("benchmark", result.stdout)

    def test_version(self):
        result = self.run_cli("--version")
        self.assertEqual(result.returncode, 0)
        self.assertIn("RDTX 2.0.0", result.stdout)

    def test_send_help(self):
        result = self.run_cli("send", "--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("--stats-json", result.stdout)
        self.assertIn("--trace", result.stdout)
        self.assertIn("--reorder", result.stdout)

    def test_benchmark_help(self):
        result = self.run_cli("benchmark", "--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("--markdown", result.stdout)
        self.assertIn("--size-kib", result.stdout)

    def test_missing_file_is_reported_without_traceback(self):
        result = self.run_cli("send", "__rdtx_missing_file__.bin")
        self.assertEqual(result.returncode, 1)
        self.assertIn("RDTX error:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_invalid_reorder_probability_is_rejected(self):
        result = self.run_cli("send", "demo.txt", "--reorder", "1.5")
        self.assertEqual(result.returncode, 2)
        self.assertIn("probability must be between 0.0 and 1.0", result.stderr)


if __name__ == "__main__":
    unittest.main()
