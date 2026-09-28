"""RDTX receiver: reorders, validates and reconstructs UDP file transfers."""

from __future__ import annotations

import argparse
import hashlib
import os
import socket
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .protocol import ChecksumError, Packet, PacketType, ProtocolError, json_payload, parse_json_payload
from .simulator import LossSimulator


@dataclass(slots=True)
class ReceiverStats:
    received_datagrams: int = 0
    unique_data_packets: int = 0
    duplicate_data_packets: int = 0
    checksum_errors: int = 0
    ack_datagrams_sent: int = 0
    simulated_ack_drops: int = 0
    bytes_written: int = 0
    elapsed: float = 0.0


class RDTXReceiver:
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 9000,
        *,
        output_dir: str | os.PathLike[str] = "received",
        ack_loss: float = 0.0,
        ack_corruption: float = 0.0,
        ack_delay_ms: float = 0.0,
        seed: int | None = None,
        linger: float = 1.5,
        verbose: bool = True,
    ) -> None:
        if linger < 0:
            raise ValueError("linger must be non-negative")
        self.bind_address = (host, port)
        self.output_dir = Path(output_dir)
        self.simulator = LossSimulator(ack_loss, ack_corruption, ack_delay_ms, seed)
        self.linger = linger
        self.verbose = verbose
        self.stats = ReceiverStats()

    def _log(self, message: str) -> None:
        if self.verbose:
            print(message, flush=True)

    def _send(self, sock: socket.socket, packet: Packet, address: tuple[str, int]) -> None:
        result = self.simulator.sendto(sock, packet.encode(), address)
        if result.sent:
            self.stats.ack_datagrams_sent += 1
        else:
            self.stats.simulated_ack_drops += 1

    @staticmethod
    def _safe_name(name: Any) -> str:
        candidate = Path(str(name)).name
        if candidate in {"", ".", ".."}:
            return "received.bin"
        return candidate

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
            self._log(f"[RDTX] receiver listening on {actual_host}:{actual_port}")

            while True:
                if linger_deadline is not None and time.monotonic() >= linger_deadline:
                    break

                try:
                    raw, address = sock.recvfrom(65_535)
                    self.stats.received_datagrams += 1
                    packet = Packet.decode(raw)
                except socket.timeout:
                    continue
                except ChecksumError:
                    self.stats.checksum_errors += 1
                    continue
                except ProtocolError:
                    continue

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
                        offered = parse_json_payload(packet.payload)
                        size = int(offered["size"])
                        total_chunks = int(offered["total_chunks"])
                        chunk_size = int(offered["chunk_size"])
                        sha256 = str(offered["sha256"])
                        filename = self._safe_name(offered["filename"])
                        if size < 0 or total_chunks < 0 or not (1 <= chunk_size <= 60_000):
                            raise ValueError("invalid transfer dimensions")
                        if len(sha256) != 64:
                            raise ValueError("invalid sha256")
                    except (KeyError, TypeError, ValueError, ProtocolError) as exc:
                        self._send(
                            sock,
                            Packet(PacketType.ERROR, packet.session_id, payload=str(exc).encode()),
                            address,
                        )
                        continue

                    if session_id is None:
                        session_id = packet.session_id
                        peer = address
                        metadata = {
                            **offered,
                            "filename": filename,
                            "size": size,
                            "total_chunks": total_chunks,
                            "chunk_size": chunk_size,
                            "sha256": sha256,
                        }
                        started_at = time.monotonic()
                        self._log(
                            f"[RDTX] accepted session={session_id} from {address[0]}:{address[1]} | "
                            f"file={filename} size={size} chunks={total_chunks}"
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
                        continue
                    if packet.seq in chunks:
                        self.stats.duplicate_data_packets += 1
                    else:
                        chunks[packet.seq] = packet.payload
                        self.stats.unique_data_packets += 1
                    self._send(sock, Packet(PacketType.ACK, session_id, ack=packet.seq), address)
                    continue

                if packet.packet_type == PacketType.FIN:
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
                            Packet(PacketType.ERROR, session_id, payload=b"final file integrity check failed"),
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
                    self._log(
                        f"[RDTX] saved {completed_path} | sha256={actual_hash[:12]}... | "
                        f"elapsed={self.stats.elapsed:.3f}s"
                    )

        if completed_path is None:
            raise RuntimeError("receiver stopped before a transfer completed")
        return completed_path, self.stats


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Receive one RDTX file transfer over UDP."
    )
    parser.add_argument("--host", default="0.0.0.0", help="interface to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=9000, help="UDP port to bind (default: 9000)")
    parser.add_argument("--output-dir", default="received", help="directory for received files")
    parser.add_argument("--ack-loss", type=float, default=0.0, help="simulated ACK/control loss rate")
    parser.add_argument("--ack-corrupt", type=float, default=0.0, help="simulated ACK/control corruption rate")
    parser.add_argument("--ack-delay-ms", type=float, default=0.0, help="maximum simulated ACK delay")
    parser.add_argument("--seed", type=int, default=None, help="random seed for repeatable ACK impairment")
    parser.add_argument("--linger", type=float, default=1.5, help="seconds to re-ACK duplicate FIN packets")
    parser.add_argument("--quiet", action="store_true", help="suppress progress output")
    return parser


def main() -> None:
    args = build_parser().parse_args()
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
    )
    receiver.receive_one()


if __name__ == "__main__":
    main()
