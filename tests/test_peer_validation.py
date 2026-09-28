import socket
import unittest

from rdtx.protocol import ProtocolError
from rdtx.sender import RDTXSender


class SenderPeerValidationTests(unittest.TestCase):
    def test_accepts_only_configured_receiver_endpoint(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as trusted:
            trusted.bind(("127.0.0.1", 0))
            sender = RDTXSender(
                "127.0.0.1",
                trusted.getsockname()[1],
                verbose=False,
            )

            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as incoming:
                incoming.bind(("127.0.0.1", 0))
                incoming.settimeout(1.0)

                trusted.sendto(b"trusted", incoming.getsockname())
                self.assertEqual(sender._receive_from_peer(incoming), b"trusted")

                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as rogue:
                    rogue.bind(("127.0.0.1", 0))
                    rogue.sendto(b"rogue", incoming.getsockname())
                    with self.assertRaises(ProtocolError):
                        sender._receive_from_peer(incoming)

                self.assertEqual(sender.stats.foreign_datagrams_ignored, 1)


if __name__ == "__main__":
    unittest.main()
