import subprocess
import sys
import unittest


class CLITests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, "-m", "rdtx", *args], check=False, capture_output=True, text=True)

    def test_version(self):
        result = self.run_cli("--version")
        self.assertEqual(result.returncode, 0)
        self.assertIn("RDTX 2.2.0", result.stdout)

    def test_help(self):
        result = self.run_cli("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("send", result.stdout)
        self.assertIn("benchmark", result.stdout)


if __name__ == "__main__":
    unittest.main()
