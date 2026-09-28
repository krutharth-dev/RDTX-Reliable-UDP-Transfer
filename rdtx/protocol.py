"""Wire format and packet helpers for the RDTX protocol."""

from __future__ import annotations

import json
import struct
import zlib
from dataclasses import dataclass
from enum import IntEnum
from typing import Any

MAGIC = b"RDTX"
VERSION = 1
_HEADER = struct.Struct("!4sBBHIIIHI")
HEADER_SIZE = _HEADER.size
MAX_PAYLOAD = 60_000


class PacketType(IntEnum):
    HELLO = 1
    HELLO_ACK = 2
    DATA = 3
    ACK = 4
    FIN = 5
    FIN_ACK = 6
    ERROR = 7


class ProtocolError(ValueError):
    """Raised when a datagram is not a valid RDTX packet."""


class ChecksumError(ProtocolError):
    """Raised when a packet's CRC32 does not match its contents."""


@dataclass(frozen=True, slots=True)
class Packet:
    packet_type: PacketType
    session_id: int
    seq: int = 0
    ack: int = 0
    payload: bytes = b""
    flags: int = 0

    def encode(self) -> bytes:
        if not (0 <= self.session_id <= 0xFFFFFFFF):
            raise ProtocolError("session_id must fit in uint32")
        if not (0 <= self.seq <= 0xFFFFFFFF):
            raise ProtocolError("seq must fit in uint32")
        if not (0 <= self.ack <= 0xFFFFFFFF):
            raise ProtocolError("ack must fit in uint32")
        if len(self.payload) > MAX_PAYLOAD:
            raise ProtocolError(f"payload too large: {len(self.payload)} bytes")

        header_without_crc = _HEADER.pack(
            MAGIC, VERSION, int(self.packet_type), self.flags,
            self.session_id, self.seq, self.ack, len(self.payload), 0,
        )
        checksum = zlib.crc32(header_without_crc + self.payload) & 0xFFFFFFFF
        header = _HEADER.pack(
            MAGIC, VERSION, int(self.packet_type), self.flags,
            self.session_id, self.seq, self.ack, len(self.payload), checksum,
        )
        return header + self.payload

    @classmethod
    def decode(cls, raw: bytes) -> "Packet":
        if len(raw) < HEADER_SIZE:
            raise ProtocolError("datagram shorter than RDTX header")

        magic, version, packet_type, flags, session_id, seq, ack, payload_len, checksum = _HEADER.unpack(
            raw[:HEADER_SIZE]
        )
        if magic != MAGIC:
            raise ProtocolError("invalid magic")
        if version != VERSION:
            raise ProtocolError(f"unsupported version: {version}")
        if payload_len != len(raw) - HEADER_SIZE:
            raise ProtocolError("payload length does not match header")
        if payload_len > MAX_PAYLOAD:
            raise ProtocolError("payload exceeds maximum size")

        try:
            kind = PacketType(packet_type)
        except ValueError as exc:
            raise ProtocolError(f"unknown packet type: {packet_type}") from exc

        payload = raw[HEADER_SIZE:]
        zero_crc_header = _HEADER.pack(
            magic, version, packet_type, flags, session_id, seq, ack, payload_len, 0
        )
        expected = zlib.crc32(zero_crc_header + payload) & 0xFFFFFFFF
        if checksum != expected:
            raise ChecksumError(
                f"CRC mismatch: packet={checksum:#010x}, calculated={expected:#010x}"
            )

        return cls(
            packet_type=kind,
            session_id=session_id,
            seq=seq,
            ack=ack,
            payload=payload,
            flags=flags,
        )


def json_payload(data: dict[str, Any]) -> bytes:
    return json.dumps(data, separators=(",", ":"), sort_keys=True).encode("utf-8")


def parse_json_payload(payload: bytes) -> dict[str, Any]:
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtocolError("invalid JSON payload") from exc
    if not isinstance(value, dict):
        raise ProtocolError("JSON payload must be an object")
    return value
