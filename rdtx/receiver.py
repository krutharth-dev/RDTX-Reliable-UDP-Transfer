"""RDTX receiver: validate, reorder and reconstruct UDP file transfers."""

from __future__ import annotations

import argparse
import hashlib
import math
import os
import socket
import string
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import (
    DEFAULT_LINGER,
    DEFAULT_PORT,
    MAX_UDP_DATAGRAM,
    non_negative_float,
    port_number,
    probability,
)
from .protocol import (
    ChecksumError,
    MAX_PAYLOAD,
    Packet,
    PacketType,
    ProtocolError,
    json_payload,
    parse_json_payload,
)
from .reporting import save_stats
from .simulator import LossSimulator


@dataclass(slots=True)
class ReceiverStats:
    received_datagrams: int = 0
    unique_data_packets: int = 0
    duplicate_data_packets: int = 0
    invalid_data_packets: int = 0
    checksum_errors: int = 0
    ack_datagrams_sent: int = 0
    simulated_ack_drops: int = 0
    simulated_ack_corruptions: int = 0
    bytes_written: int = 0
    elapsed: float = 0.0

    @property
    def throughput_kib_s(self) -> float:
        if self.elapsed <= 0:
            return 0.0
        return (self.bytes_written / 1024.0) / self.elapsed


class RDTXReceiver:
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = DEFAULT_PORT,
        *,
        output_dir: str | os.PathLike[str] = "received",
        ack_loss: float = 0.0,
        ack_corruption: float = 0.0,
        ack_delay_ms: float = 0.0,
        seed: int | None = None,
        linger: float = DEFAULT_LINGER,
        verbose: bool = True,
        trace: bool = False,
    ) -> None:
        if not 1 <= port <= 65_535:
            raise ValueError("port must be between 1 and 65535")
        if linger < 0:
            raise ValueError("linger must be non-negative")

        self.bind_address = (host, port)
        self.output_dir = Path(output_dir)
        self.simulator = LossSimulator(ack_loss, ack_corruption, ack_delay_ms, seed)
        self.linger = linger
        self.verbose = verbose
        self.trace = trace
        self.stats = ReceiverStats()

    def _log(self, message: str) -> None:
        if self.verbose:
            print(message, flush=True)

    def _trace(self, message: str) -> None:
        if self.trace:
            print(f"[TRACE] {message}", flush=True)

    def _send(self, sock: socket.socket, packet: Packet, address: tuple[str, int]) -> None:
        result = self.simulator.sendto(sock, packet.encode(), address)
        if result.sent:
            self.stats.ack_datagrams_sent += 1
        else:
            self.stats.simulated_ack_drops += 1
        if result.corrupted:
            self.stats.simulated_ack_corruptions += 1

        if self.trace:
            state = "DROP" if not result.sent else "TX"
            label = packet.packet_type.name
            if packet.packet_type == PacketType.ACK:
                label += f" seq={packet.ack}"
            details = []
            if result.corrupted:
                details.append("simulated-corruption")
            if result.delayed_ms:
                details.append(f"delay={result.delayed_ms:.1f}ms")
            suffix = f" ({', '.join(details)})" if details else ""
            self._trace(f"{state} {label}{suffix}")

    @staticmethod
    def _safe_name(name: Any) -> str:
        candidate = Path(str(name)).name
        if candidate in {"", ".", ".."}:
            return "received.bin"
        return candidate

    @classmethod
    def _validate_metadata(cls, payload: bytes) -> dict[str, Any]:
        offered = parse_json_payload(payload)
        try:
            size = int(offered["size"])
            total_chunks = int(offered["total_chunks"])
            chunk_size = int(offered["chunk_size"])
            window_size = int(offered["window_size"])
            sha256 = str(offered["sha256"]).lower()
            filename = cls._safe_name(offered["filename"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ProtocolError(f"invalid HELLO metadata: {exc}") from exc

        if size < 0:
            raise ProtocolError("file size cannot be negative")
        if not 1 <= chunk_size <= MAX_PAYLOAD:
            raise ProtocolError(f"chunk_size must be between 1 and {MAX_PAYLOAD}")
        if window_size < 1:
            raise ProtocolError("window_size must be >= 1")
        if total_chunks < 0:
            raise ProtocolError("total_chunks cannot be negative")
        expected_chunks = math.ceil(size / chunk_size) if size else 0
        if total_chunks != expected_chunks:
            raise ProtocolError(
                f"total_chunks mismatch: expected {expected_chunks}, received {total_chunks}"
            )
        if len(sha256) != 64 or any(char not in string.hexdigits for char in sha256):
            raise ProtocolError("sha256 must be a 64-character hexadecimal digest")

        return {
            **offered,
            "filename": filename,
            "size": size,
            "total_chunks": total_chunks,
            "chunk_size": chunk_size,
            "window_size": window_size,
            "sha256": sha256,
        }

    @staticmethod
    def _expected_chunk_length(metadata: dict[str, Any], seq: int) -> int:
        total_chunks = int(metadata["total_chunks"])
        chunk_size = int(metadata["chunk_size"])
        size = int(metadata["size"])
        if total_chunks == 0:
            return 0
        if seq < total_chunks - 1:
            return chunk_size
        return size - chunk_size * (total_chunks - 1)

    def receive_one(self) -> tuple[Path, ReceiverStats]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.stats = ReceiverStats()

        session_id: int | None = None
        peer: tuple[str, int] | None = None
        metadata: dict[str, Any] | None = None
        chunks: dict[int, bytes] = {}
        started_at: float | None = None
        completed_path: Path | None = None
        fin_ack: Packet | None = None
        linger_deadline: float | None = None

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind(self.bind_address)
            sock.settimeout(0.2)
            actual_host, actual_port = sock.getsockname()

            self._log("=" * 60)
            self._log("RDTX RECEIVER")
            self._log("=" * 60)
            self._log(
                f"Listening    : {actual_host}:{actual_port}\n"
                f"Output dir   : {self.output_dir}"
            )

            while True:
                if linger_deadline is not None and time.monotonic() >= linger_deadline:
                    break

                try:
                    raw, address = sock.recvfrom(MAX_UDP_DATAGRAM)
                    self.stats.received_datagrams += 1
                    packet = Packet.decode(raw)
                except socket.timeout:
                    continue
                except ChecksumError:
                    self.stats.checksum_errors += 1
                    self._trace("RX corrupted datagram -> discarded")
                    continue
                except ProtocolError:
                    self._trace("RX invalid datagram -> discarded")
                    continue

                if packet.packet_type == PacketType.DATA:
                    self._trace(f"RX DATA seq={packet.seq}")
                else:
                    self._trace(f"RX {packet.packet_type.name}")

                if completed_path is not None:
                    if (
                        packet.packet_type == PacketType.FIN
                        and packet.session_id == session_id
                        and address == peer
                        and fin_ack is not None
                    ):
                        self._send(sock, fin_ack, address)
                        linger_deadline = time.monotonic() + self.linger
                    continue

                if packet.packet_type == PacketType.HELLO:
                    try:
                        offered = self._validate_metadata(packet.payload)
                    except ProtocolError as exc:
                        self._send(
                            sock,
                            Packet(
                                PacketType.ERROR,
                                packet.session_id,
                                payload=str(exc).encode("utf-8"),
                            ),
                            address,
                        )
                        continue

                    if session_id is None:
                        session_id = packet.session_id
                        peer = address
                        metadata = offered
                        started_at = time.monotonic()
                        self._log(
                            f"[RDTX] Session accepted from {address[0]}:{address[1]}\n"
                            f"File        : {metadata['filename']}\n"
                            f"Size        : {metadata['size']} bytes\n"
                            f"Chunks      : {metadata['total_chunks']}\n"
                            f"Window      : {metadata['window_size']}\n"
                            f"Session ID  : {session_id}"
                        )

                    if packet.session_id == session_id and address == peer:
                        self._send(sock, Packet(PacketType.HELLO_ACK, session_id), address)
                    continue

                if session_id is None or metadata is None or peer is None:
                    continue
                if packet.session_id != session_id or address != peer:
                    continue

                if packet.packet_type == PacketType.DATA:
                    total_chunks = int(metadata["total_chunks"])
                    if packet.seq >= total_chunks:
                        self.stats.invalid_data_packets += 1
                        self._trace(f"DATA seq={packet.seq} outside transfer range -> discarded")
                        continue

                    expected_length = self._expected_chunk_length(metadata, packet.seq)
                    if len(packet.payload) != expected_length:
                        self.stats.invalid_data_packets += 1
                        self._trace(
                            f"DATA seq={packet.seq} has {len(packet.payload)} bytes; "
                            f"expected {expected_length} -> discarded"
                        )
                        continue

                    if packet.seq in chunks:
                        self.stats.duplicate_data_packets += 1
                    else:
                        chunks[packet.seq] = packet.payload
                        self.stats.unique_data_packets += 1
                    self._send(sock, Packet(PacketType.ACK, session_id, ack=packet.seq), address)
                    continue

                if packet.packet_type == PacketType.FIN:
                    try:
                        final_meta = parse_json_payload(packet.payload)
                        if int(final_meta["size"]) != int(metadata["size"]):
                            raise ProtocolError("FIN size does not match HELLO")
                        if str(final_meta["sha256"]).lower() != str(metadata["sha256"]):
                            raise ProtocolError("FIN SHA-256 does not match HELLO")
                    except (KeyError, TypeError, ValueError, ProtocolError) as exc:
                        self._send(
                            sock,
                            Packet(PacketType.ERROR, session_id, payload=str(exc).encode("utf-8")),
                            address,
                        )
                        continue

                    expected_chunks = int(metadata["total_chunks"])
                    if len(chunks) != expected_chunks:
                        missing = expected_chunks - len(chunks)
                        self._send(
                            sock,
                            Packet(
                                PacketType.ERROR,
                                session_id,
                                payload=f"FIN received with {missing} chunks missing".encode(),
                            ),
                            address,
                        )
                        continue

                    assembled = b"".join(chunks[index] for index in range(expected_chunks))
                    expected_size = int(metadata["size"])
                    expected_hash = str(metadata["sha256"])
                    actual_hash = hashlib.sha256(assembled).hexdigest()
                    if len(assembled) != expected_size or actual_hash != expected_hash:
                        self._send(
                            sock,
                            Packet(
                                PacketType.ERROR,
                                session_id,
                                payload=b"final file integrity check failed",
                            ),
                            address,
                        )
                        continue

                    completed_path = self.output_dir / str(metadata["filename"])
                    completed_path.write_bytes(assembled)
                    self.stats.bytes_written = len(assembled)
                    self.stats.elapsed = time.monotonic() - (started_at or time.monotonic())
                    fin_ack = Packet(
                        PacketType.FIN_ACK,
                        session_id,
                        ack=packet.seq,
                        payload=json_payload(
                            {
                                "bytes": len(assembled),
                                "sha256": actual_hash,
                                "status": "ok",
                            }
                        ),
                    )
                    self._send(sock, fin_ack, address)
                    linger_deadline = time.monotonic() + self.linger

                    self._log("-" * 60)
                    self._log(
                        "TRANSFER COMPLETE\n"
                        f"Saved to        : {completed_path}\n"
                        f"Bytes written   : {self.stats.bytes_written}\n"
                        f"Duplicates      : {self.stats.duplicate_data_packets}\n"
                        f"Checksum errors : {self.stats.checksum_errors}\n"
                        f"ACK drops       : {self.stats.simulated_ack_drops}\n"
                        f"Throughput      : {self.stats.throughput_kib_s:.1f} KiB/s\n"
                        f"SHA-256         : {actual_hash}"
                    )
                    self._log("-" * 60)

        if completed_path is None:
            raise RuntimeError("receiver stopped before a transfer completed")
        return completed_path, self.stats


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Receive one RDTX file transfer over UDP.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--host", default="0.0.0.0", help="IPv4 interface to bind")
    parser.add_argument("--port", type=port_number, default=DEFAULT_PORT, help="UDP port to bind")
    parser.add_argument("--output-dir", default="received", help="directory for received files")
    parser.add_argument("--ack-loss", type=probability, default=0.0, help="simulated ACK/control loss probability")
    parser.add_argument("--ack-corrupt", type=probability, default=0.0, help="simulated ACK/control corruption probability")
    parser.add_argument("--ack-delay-ms", type=non_negative_float, default=0.0, help="maximum simulated ACK delay")
    parser.add_argument("--seed", type=int, default=None, help="random seed for repeatable ACK impairment")
    parser.add_argument("--linger", type=non_negative_float, default=DEFAULT_LINGER, help="seconds to re-ACK duplicate FIN packets")
    parser.add_argument("--stats-json", metavar="PATH", help="write transfer statistics to a JSON file")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--trace", action="store_true", help="show per-packet protocol activity")
    output.add_argument("--quiet", action="store_true", help="suppress progress output")
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    receiver = RDTXReceiver(
        args.host,
        args.port,
        output_dir=args.output_dir,
        ack_loss=args.ack_loss,
        ack_corruption=args.ack_corrupt,
        ack_delay_ms=args.ack_delay_ms,
        seed=args.seed,
        linger=args.linger,
        verbose=not args.quiet,
        trace=args.trace,
    )
    path, stats = receiver.receive_one()
    if args.stats_json:
        target = save_stats(
            args.stats_json,
            "receiver",
            stats,
            file=path.name,
            bind=f"{args.host}:{args.port}",
            ack_loss=args.ack_loss,
            ack_corruption=args.ack_corrupt,
            max_ack_delay_ms=args.ack_delay_ms,
            seed=args.seed,
        )
        if not args.quiet:
            print(f"[RDTX] Statistics written to {target}", flush=True)


if __name__ == "__main__":
    main()
