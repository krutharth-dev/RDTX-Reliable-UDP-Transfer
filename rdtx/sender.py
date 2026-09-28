"""RDTX sender: reliable file transfer over UDP using Selective Repeat."""

from __future__ import annotations

import argparse
import hashlib
import os
import secrets
import socket
import time
from dataclasses import dataclass
from pathlib import Path

from .protocol import ChecksumError, Packet, PacketType, ProtocolError, json_payload
from .simulator import LossSimulator


@dataclass(slots=True)
class SenderStats:
    file_bytes: int = 0
    data_packets: int = 0
    datagrams_sent: int = 0
    simulated_drops: int = 0
    retransmissions: int = 0
    ack_packets: int = 0
    checksum_errors: int = 0
    elapsed: float = 0.0

    @property
    def throughput_kib_s(self) -> float:
        if self.elapsed <= 0:
            return 0.0
        return (self.file_bytes / 1024.0) / self.elapsed


@dataclass(slots=True)
class InFlight:
    raw: bytes
    sent_at: float
    retries: int = 0


class RDTXSender:
    def __init__(
        self,
        host: str,
        port: int = 9000,
        *,
        chunk_size: int = 1024,
        window_size: int = 8,
        timeout: float = 0.35,
        max_retries: int = 40,
        loss: float = 0.0,
        corruption: float = 0.0,
        delay_ms: float = 0.0,
        seed: int | None = None,
        verbose: bool = True,
    ) -> None:
        if not 1 <= chunk_size <= 60_000:
            raise ValueError("chunk_size must be between 1 and 60000")
        if window_size < 1:
            raise ValueError("window_size must be >= 1")
        if timeout <= 0:
            raise ValueError("timeout must be > 0")
        if max_retries < 1:
            raise ValueError("max_retries must be >= 1")

        self.destination = (host, port)
        self.chunk_size = chunk_size
        self.window_size = window_size
        self.timeout = timeout
        self.max_retries = max_retries
        self.verbose = verbose
        self.simulator = LossSimulator(loss, corruption, delay_ms, seed)
        self.stats = SenderStats()

    def _log(self, message: str) -> None:
        if self.verbose:
            print(message, flush=True)

    def _send(self, sock: socket.socket, raw: bytes, *, retransmission: bool = False) -> None:
        result = self.simulator.sendto(sock, raw, self.destination)
        if result.sent:
            self.stats.datagrams_sent += 1
        else:
            self.stats.simulated_drops += 1
        if retransmission:
            self.stats.retransmissions += 1

    def _exchange_control(
        self,
        sock: socket.socket,
        packet: Packet,
        expected_type: PacketType,
        session_id: int,
    ) -> Packet:
        raw = packet.encode()
        for attempt in range(self.max_retries + 1):
            self._send(sock, raw, retransmission=attempt > 0)
            deadline = time.monotonic() + self.timeout
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                sock.settimeout(remaining)
                try:
                    incoming, _ = sock.recvfrom(65_535)
                    decoded = Packet.decode(incoming)
                except socket.timeout:
                    break
                except ChecksumError:
                    self.stats.checksum_errors += 1
                    continue
                except ProtocolError:
                    continue
                if decoded.session_id != session_id:
                    continue
                if decoded.packet_type == PacketType.ERROR:
                    message = decoded.payload.decode("utf-8", errors="replace")
                    raise RuntimeError(f"receiver error: {message}")
                if decoded.packet_type == expected_type:
                    return decoded
        raise TimeoutError(f"no {expected_type.name} received after {self.max_retries} retries")

    def send_file(self, file_path: str | os.PathLike[str]) -> SenderStats:
        path = Path(file_path)
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        chunks = [data[i : i + self.chunk_size] for i in range(0, len(data), self.chunk_size)]
        session_id = secrets.randbits(32) or 1
        self.stats = SenderStats(file_bytes=len(data), data_packets=len(chunks))

        metadata = {
            "filename": path.name,
            "size": len(data),
            "sha256": digest,
            "chunk_size": self.chunk_size,
            "total_chunks": len(chunks),
            "window_size": self.window_size,
        }

        start = time.monotonic()
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            self._log(
                f"[RDTX] session={session_id} destination={self.destination[0]}:{self.destination[1]}"
            )
            self._log(
                f"[RDTX] file={path.name} size={len(data)} bytes chunks={len(chunks)} window={self.window_size}"
            )
            self._exchange_control(
                sock,
                Packet(PacketType.HELLO, session_id, payload=json_payload(metadata)),
                PacketType.HELLO_ACK,
                session_id,
            )
            self._log("[RDTX] HELLO acknowledged; starting data transfer")

            inflight: dict[int, InFlight] = {}
            acked: set[int] = set()
            next_seq = 0
            sock.settimeout(min(0.05, self.timeout))

            while len(acked) < len(chunks):
                while next_seq < len(chunks) and len(inflight) < self.window_size:
                    raw = Packet(
                        PacketType.DATA,
                        session_id,
                        seq=next_seq,
                        payload=chunks[next_seq],
                    ).encode()
                    self._send(sock, raw)
                    inflight[next_seq] = InFlight(raw=raw, sent_at=time.monotonic())
                    next_seq += 1

                try:
                    incoming, _ = sock.recvfrom(65_535)
                    packet = Packet.decode(incoming)
                    if packet.session_id == session_id and packet.packet_type == PacketType.ACK:
                        self.stats.ack_packets += 1
                        if packet.ack in inflight:
                            inflight.pop(packet.ack, None)
                            acked.add(packet.ack)
                except socket.timeout:
                    pass
                except ChecksumError:
                    self.stats.checksum_errors += 1
                except ProtocolError:
                    pass

                now = time.monotonic()
                for seq, state in list(inflight.items()):
                    if now - state.sent_at < self.timeout:
                        continue
                    if state.retries >= self.max_retries:
                        raise TimeoutError(f"packet {seq} exceeded retry limit")
                    self._send(sock, state.raw, retransmission=True)
                    state.sent_at = time.monotonic()
                    state.retries += 1

            self._log("[RDTX] all DATA packets acknowledged")
            fin_payload = json_payload({"sha256": digest, "size": len(data)})
            self._exchange_control(
                sock,
                Packet(PacketType.FIN, session_id, seq=len(chunks), payload=fin_payload),
                PacketType.FIN_ACK,
                session_id,
            )

        self.stats.elapsed = time.monotonic() - start
        self._log(
            f"[RDTX] transfer complete in {self.stats.elapsed:.3f}s | "
            f"retransmissions={self.stats.retransmissions} | "
            f"throughput={self.stats.throughput_kib_s:.1f} KiB/s"
        )
        return self.stats


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Send a file reliably over UDP using the RDTX protocol."
    )
    parser.add_argument("file", help="path of the file to send")
    parser.add_argument("--host", default="127.0.0.1", help="receiver host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=9000, help="receiver UDP port (default: 9000)")
    parser.add_argument("--chunk-size", type=int, default=1024, help="payload bytes per DATA packet")
    parser.add_argument("--window", type=int, default=8, help="Selective Repeat window size")
    parser.add_argument("--timeout", type=float, default=0.35, help="retransmission timeout in seconds")
    parser.add_argument("--max-retries", type=int, default=40, help="maximum retries per packet/control exchange")
    parser.add_argument("--loss", type=float, default=0.0, help="simulated outgoing loss rate, e.g. 0.2")
    parser.add_argument("--corrupt", type=float, default=0.0, help="simulated outgoing corruption rate")
    parser.add_argument("--delay-ms", type=float, default=0.0, help="maximum simulated outgoing delay")
    parser.add_argument("--seed", type=int, default=None, help="random seed for repeatable impairment simulation")
    parser.add_argument("--quiet", action="store_true", help="suppress progress output")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    sender = RDTXSender(
        args.host,
        args.port,
        chunk_size=args.chunk_size,
        window_size=args.window,
        timeout=args.timeout,
        max_retries=args.max_retries,
        loss=args.loss,
        corruption=args.corrupt,
        delay_ms=args.delay_ms,
        seed=args.seed,
        verbose=not args.quiet,
    )
    sender.send_file(args.file)


if __name__ == "__main__":
    main()
