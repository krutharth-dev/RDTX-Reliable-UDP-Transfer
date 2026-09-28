import unittest

from rdtx.protocol import ChecksumError, Packet, PacketType, ProtocolError


class PacketTests(unittest.TestCase):
    def test_round_trip(self):
        original = Packet(
            PacketType.DATA,
            session_id=1234,
            seq=7,
            ack=3,
            payload=b"hello-rdtx",
            flags=2,
        )
        decoded = Packet.decode(original.encode())
        self.assertEqual(decoded, original)

    def test_corruption_is_detected(self):
        raw = bytearray(Packet(PacketType.DATA, 99, seq=1, payload=b"payload").encode())
        raw[-1] ^= 0x01
        with self.assertRaises(ChecksumError):
            Packet.decode(bytes(raw))

    def test_truncated_packet_is_rejected(self):
        with self.assertRaises(ProtocolError):
            Packet.decode(b"RDTX")


if __name__ == "__main__":
    unittest.main()
