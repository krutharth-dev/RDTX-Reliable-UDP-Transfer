import socket
import tempfile
import threading
import unittest
from pathlib import Path

from rdtx.receiver import RDTXReceiver
from rdtx.sender import RDTXSender


def free_udp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class IntegrationTests(unittest.TestCase):
    def test_localhost_transfer(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.bin"
            output = root / "received"
            source.write_bytes((b"RDTX integration test\n" * 300) + bytes(range(256)))
            port = free_udp_port()

            receiver = RDTXReceiver("127.0.0.1", port, output_dir=output, linger=0.1, verbose=False)
            result = {}

            def run_receiver():
                result["path"], result["stats"] = receiver.receive_one()

            thread = threading.Thread(target=run_receiver, daemon=True)
            thread.start()

            sender = RDTXSender("127.0.0.1", port, chunk_size=333, window_size=5, timeout=0.1, verbose=False)
            stats = sender.send_file(source)
            thread.join(timeout=3)

            self.assertFalse(thread.is_alive())
            self.assertEqual((output / source.name).read_bytes(), source.read_bytes())
            self.assertEqual(stats.file_bytes, source.stat().st_size)
            self.assertEqual(result["stats"].bytes_written, source.stat().st_size)

    def test_empty_file_transfer(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "empty.bin"
            output = root / "received"
            source.write_bytes(b"")
            port = free_udp_port()

            receiver = RDTXReceiver("127.0.0.1", port, output_dir=output, linger=0.1, verbose=False)
            thread = threading.Thread(target=receiver.receive_one, daemon=True)
            thread.start()

            sender = RDTXSender("127.0.0.1", port, timeout=0.1, verbose=False)
            stats = sender.send_file(source)
            thread.join(timeout=3)

            self.assertFalse(thread.is_alive())
            self.assertEqual((output / source.name).read_bytes(), b"")
            self.assertEqual(stats.file_bytes, 0)
            self.assertEqual(stats.data_packets, 0)

    def test_explicit_packet_reordering(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "reordered.bin"
            output = root / "received"
            source.write_bytes(bytes(range(256)) * 16)
            port = free_udp_port()

            receiver = RDTXReceiver("127.0.0.1", port, output_dir=output, linger=0.1, verbose=False)
            thread = threading.Thread(target=receiver.receive_one, daemon=True)
            thread.start()

            sender = RDTXSender(
                "127.0.0.1",
                port,
                chunk_size=256,
                window_size=4,
                timeout=0.1,
                reorder_rate=1.0,
                seed=99,
                verbose=False,
            )
            stats = sender.send_file(source)
            thread.join(timeout=3)

            self.assertFalse(thread.is_alive())
            self.assertEqual((output / source.name).read_bytes(), source.read_bytes())
            self.assertGreater(stats.reordered_pairs, 0)

    def test_transfer_with_repeatable_loss(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "lossy.txt"
            output = root / "received"
            source.write_text("Selective Repeat survives UDP loss.\n" * 200, encoding="utf-8")
            port = free_udp_port()

            receiver = RDTXReceiver(
                "127.0.0.1",
                port,
                output_dir=output,
                ack_loss=0.10,
                seed=17,
                linger=0.2,
                verbose=False,
            )
            thread = threading.Thread(target=receiver.receive_one, daemon=True)
            thread.start()

            sender = RDTXSender(
                "127.0.0.1",
                port,
                chunk_size=256,
                window_size=6,
                timeout=0.05,
                max_retries=80,
                loss=0.12,
                seed=7,
                verbose=False,
            )
            stats = sender.send_file(source)
            thread.join(timeout=5)

            self.assertFalse(thread.is_alive())
            self.assertEqual((output / source.name).read_bytes(), source.read_bytes())
            self.assertGreater(stats.retransmissions + stats.simulated_drops, 0)


if __name__ == "__main__":
    unittest.main()
