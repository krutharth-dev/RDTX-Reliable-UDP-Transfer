"""RDTX sender: reliable file transfer over UDP using Selective Repeat."""

from __future__ import annotations

import argparse
import hashlib
import os
import random
import secrets
import socket
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from .config import (
    DEFAULT_CHUNK_SIZE,
    DEFAULT_MAX_RETRIES,
    DEFAULT_PORT,
    DEFAULT_TIMEOUT,
    DEFAULT_WINDOW_SIZE,
    MAX_UDP_DATAGRAM,
    non_negative_float,
    port_number,
    positive_float,
    positive_int,
    probability,
)
from .protocol import ChecksumError, MAX_PAYLOAD, Packet, PacketType, ProtocolError, json_payload
from .reporting import save_stats
from .simulator import LossSimulator
from .window import SelectiveRepeatWindow


@dataclass(slots=True)
class SenderStats:
    file_bytes: int = 0
    data_packets: int = 0
    datagrams_sent: int = 0
    simulated_drops: int = 0
    simulated_corruptions: int = 0
    retransmissions: int = 0
    ack_packets: int = 0
    checksum_errors: int = 0
    foreign_datagrams_ignored: int = 0
    reordered_pairs: int = 0
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
        port: int = DEFAULT_PORT,
        *,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        window_size: int = DEFAULT_WINDOW_SIZE,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        loss: float = 0.0,
        corruption: float = 0.0,
        delay_ms: float = 0.0,
        reorder_rate: float = 0.0,
        seed: int | None = None,
        verbose: bool = True,
        trace: bool = False,
    ) -> None:
        if not 1 <= port <= 65_535:
            raise ValueError("port must be between 1 and 65535")
        if not 1 <= chunk_size <= MAX_PAYLOAD:
            raise ValueError(f"chunk_size must be between 1 and {MAX_PAYLOAD}")
        if window_size < 1:
            raise ValueError("window_size must be >= 1")
        if timeout <= 0:
            raise ValueError("timeout must be > 0")
        if max_retries < 1:
            raise ValueError("max_retries must be >= 1")
        if not 0.0 <= reorder_rate <= 1.0:
            raise ValueError("reorder_rate must be between 0 and 1")

        try:
            resolved_host = socket.gethostbyname(host)
        except socket.gaierror as exc:
            raise ValueError(f"unable to resolve receiver host: {host}") from exc

        self.destination = (resolved_host, port)
        self.destination_name = host
        self.chunk_size = chunk_size
        self.window_size = window_size
        self.timeout = timeout
        self.max_retries = max_retries
        self.verbose = verbose
        self.trace = trace
        self.reorder_rate = reorder_rate
        reorder_seed = None if seed is None else seed ^ 0x5A17
        self._reorder_rng = random.Random(reorder_seed)
        self.simulator = LossSimulator(loss, corruption, delay_ms, seed)
        self.stats = SenderStats()

    def _log(self, message: str) -> None:
        if self.verbose:
            print(message, flush=True)

    def _trace(self, message: str) -> None:
        if self.trace:
            print(f"[TRACE] {message}", flush=True)

    def _send(
        self,
        sock: socket.socket,
        raw: bytes,
        *,
        label: str,
        retransmission: bool = False,
    ) -> None:
        result = self.simulator.sendto(sock, raw, self.destination)
        if result.sent:
            self.stats.datagrams_sent += 1
        else:
            self.stats.simulated_drops += 1
        if result.corrupted:
            self.stats.simulated_corruptions += 1
        if retransmission:
            self.stats.retransmissions += 1

        if self.trace:
            state = "DROP" if not result.sent else "TX"
            details = []
            if retransmission:
                details.append("retransmission")
            if result.corrupted:
                details.append("simulated-corruption")
            if result.delayed_ms:
                details.append(f"delay={result.delayed_ms:.1f}ms")
            suffix = f" ({', '.join(details)})" if details else ""
            self._trace(f"{state} {label}{suffix}")

    def _receive_from_peer(self, sock: socket.socket) -> bytes:
        """Receive one datagram and reject packets from unexpected UDP peers."""
        incoming, source = sock.recvfrom(MAX_UDP_DATAGRAM)
        if source != self.destination:
            self.stats.foreign_datagrams_ignored += 1
            self._trace(
                f"RX datagram from unexpected peer {source[0]}:{source[1]} -> ignored"
            )
            raise ProtocolError("unexpected UDP peer")
        return incoming

    def _send_data(
        self,
        sock: socket.socket,
        session_id: int,
        seq: int,
        payload: bytes,
        inflight: dict[int, InFlight],
    ) -> None:
        raw = Packet(
            PacketType.DATA,
            session_id,
            seq=seq,
            payload=payload,
        ).encode()
        self._send(sock, raw, label=f"DATA seq={seq}")
        inflight[seq] = InFlight(raw=raw, sent_at=time.monotonic())

    def _exchange_control(
        self,
        sock: socket.socket,
        packet: Packet,
        expected_type: PacketType,
        session_id: int,
    ) -> Packet:
        raw = packet.encode()
        for attempt in range(self.max_retries + 1):
            self._send(
                sock,
                raw,
                label=packet.packet_type.name,
                retransmission=attempt > 0,
            )
            deadline = time.monotonic() + self.timeout
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                sock.settimeout(remaining)
                try:
                    incoming = self._receive_from_peer(sock)
                    decoded = Packet.decode(incoming)
                except socket.timeout:
                    break
                except ChecksumError:
                    self.stats.checksum_errors += 1
                    self._trace("RX corrupted control/ACK datagram -> ignored")
                    continue
                except ProtocolError:
                    self._trace("RX invalid/unexpected datagram -> ignored")
                    continue

                if decoded.session_id != session_id:
                    self._trace(
                        f"RX session={decoded.session_id} while expecting {session_id} -> ignored"
                    )
                    continue
                self._trace(f"RX {decoded.packet_type.name}")
                if decoded.packet_type == PacketType.ERROR:
                    message = decoded.payload.decode("utf-8", errors="replace")
                    raise RuntimeError(f"receiver error: {message}")
                if decoded.packet_type == expected_type:
                    return decoded

        raise TimeoutError(
            f"no {expected_type.name} received after {self.max_retries} retries"
        )

    def send_file(self, file_path: str | os.PathLike[str]) -> SenderStats:
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"input file not found: {path}")

        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        chunks = [
            data[offset : offset + self.chunk_size]
            for offset in range(0, len(data), self.chunk_size)
        ]
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
            self._log("=" * 60)
            self._log("RDTX SENDER")
            self._log("=" * 60)
            self._log(
                f"Destination : {self.destination_name} "
                f"({self.destination[0]}):{self.destination[1]}\n"
                f"File        : {path.name}\n"
                f"Size        : {len(data)} bytes\n"
                f"Chunks      : {len(chunks)}\n"
                f"Window      : {self.window_size}\n"
                f"Session ID  : {session_id}"
            )

            self._exchange_control(
                sock,
                Packet(PacketType.HELLO, session_id, payload=json_payload(metadata)),
                PacketType.HELLO_ACK,
                session_id,
            )
            self._log("[RDTX] Handshake complete. Starting data transfer.")

            inflight: dict[int, InFlight] = {}
            window = SelectiveRepeatWindow(
                total_packets=len(chunks),
                window_size=self.window_size,
            )
            sock.settimeout(min(0.05, self.timeout))

            while not window.complete:
                while window.can_send:
                    first_seq = window.take_next()
                    should_reorder = (
                        self.reorder_rate > 0.0
                        and window.can_send
                        and self._reorder_rng.random() < self.reorder_rate
                    )
                    if should_reorder:
                        second_seq = window.take_next()
                        self.stats.reordered_pairs += 1
                        self._trace(
                            f"REORDER pair: DATA seq={second_seq} sent before seq={first_seq}"
                        )
                        self._send_data(
                            sock, session_id, second_seq, chunks[second_seq], inflight
                        )
                        self._send_data(
                            sock, session_id, first_seq, chunks[first_seq], inflight
                        )
                    else:
                        self._send_data(
                            sock, session_id, first_seq, chunks[first_seq], inflight
                        )

                try:
                    incoming = self._receive_from_peer(sock)
                    packet = Packet.decode(incoming)
                    if packet.session_id != session_id:
                        self._trace(
                            f"RX session={packet.session_id} while expecting {session_id} -> ignored"
                        )
                        continue
                    if packet.packet_type == PacketType.ERROR:
                        message = packet.payload.decode("utf-8", errors="replace")
                        raise RuntimeError(f"receiver error: {message}")
                    if packet.packet_type == PacketType.ACK:
                        self.stats.ack_packets += 1
                        old_base = window.base
                        if packet.ack in inflight and window.acknowledge(packet.ack):
                            inflight.pop(packet.ack, None)
                            self._trace(
                                f"RX ACK seq={packet.ack} | "
                                f"window base {old_base}->{window.base} "
                                f"range=[{window.base},{window.upper_bound})"
                            )
                        else:
                            self._trace(
                                f"RX duplicate/out-of-window ACK seq={packet.ack} -> ignored"
                            )
                except socket.timeout:
                    pass
                except ChecksumError:
                    self.stats.checksum_errors += 1
                    self._trace("RX corrupted ACK -> ignored")
                except ProtocolError:
                    self._trace("RX invalid/unexpected datagram -> ignored")

                now = time.monotonic()
                for seq, state in list(inflight.items()):
                    if now - state.sent_at < self.timeout:
                        continue
                    if state.retries >= self.max_retries:
                        raise TimeoutError(f"packet {seq} exceeded retry limit")
                    self._send(
                        sock,
                        state.raw,
                        label=f"DATA seq={seq}",
                        retransmission=True,
                    )
                    state.sent_at = time.monotonic()
                    state.retries += 1

            self._log("[RDTX] All DATA packets acknowledged.")
            fin_payload = json_payload({"sha256": digest, "size": len(data)})
            self._exchange_control(
                sock,
                Packet(PacketType.FIN, session_id, seq=len(chunks), payload=fin_payload),
                PacketType.FIN_ACK,
                session_id,
            )

        self.stats.elapsed = time.monotonic() - start
        self._log("-" * 60)
        self._log(
            "TRANSFER COMPLETE\n"
            f"Elapsed         : {self.stats.elapsed:.3f} s\n"
            f"Retransmissions : {self.stats.retransmissions}\n"
            f"Simulated drops : {self.stats.simulated_drops}\n"
            f"Corruptions     : {self.stats.simulated_corruptions}\n"
            f"Foreign ignored : {self.stats.foreign_datagrams_ignored}\n"
            f"Reordered pairs : {self.stats.reordered_pairs}\n"
            f"Throughput      : {self.stats.throughput_kib_s:.1f} KiB/s\n"
            f"SHA-256         : {digest}"
        )
        self._log("-" * 60)
        return self.stats


def _chunk_size(value: str) -> int:
    number = int(value)
    if not 1 <= number <= MAX_PAYLOAD:
        raise argparse.ArgumentTypeError(
            f"chunk size must be between 1 and {MAX_PAYLOAD}"
        )
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Send a file reliably over UDP using the RDTX protocol.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("file", help="path of the file to send")
    parser.add_argument("--host", default="127.0.0.1", help="receiver IPv4 host")
    parser.add_argument("--port", type=port_number, default=DEFAULT_PORT, help="receiver UDP port")
    parser.add_argument("--chunk-size", type=_chunk_size, default=DEFAULT_CHUNK_SIZE, help="payload bytes per DATA packet")
    parser.add_argument("--window", type=positive_int, default=DEFAULT_WINDOW_SIZE, help="Selective Repeat window size")
    parser.add_argument("--timeout", type=positive_float, default=DEFAULT_TIMEOUT, help="retransmission timeout in seconds")
    parser.add_argument("--max-retries", type=positive_int, default=DEFAULT_MAX_RETRIES, help="maximum retries per packet/control exchange")
    parser.add_argument("--loss", type=probability, default=0.0, help="simulated outgoing loss probability")
    parser.add_argument("--corrupt", type=probability, default=0.0, help="simulated outgoing corruption probability")
    parser.add_argument("--delay-ms", type=non_negative_float, default=0.0, help="maximum simulated outgoing delay")
    parser.add_argument("--reorder", type=probability, default=0.0, help="probability of reversing adjacent DATA packet pairs")
    parser.add_argument("--seed", type=int, default=None, help="random seed for repeatable impairment simulation")
    parser.add_argument("--stats-json", metavar="PATH", help="write transfer statistics to a JSON file")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--trace", action="store_true", help="show per-packet protocol activity")
    output.add_argument("--quiet", action="store_true", help="suppress progress output")
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
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
        reorder_rate=args.reorder,
        seed=args.seed,
        verbose=not args.quiet,
        trace=args.trace,
    )
    stats = sender.send_file(args.file)
    if args.stats_json:
        target = save_stats(
            args.stats_json,
            "sender",
            stats,
            file=Path(args.file).name,
            destination=f"{args.host}:{args.port}",
            chunk_size=args.chunk_size,
            window_size=args.window,
            timeout_seconds=args.timeout,
            loss=args.loss,
            corruption=args.corrupt,
            max_delay_ms=args.delay_ms,
            reorder=args.reorder,
            seed=args.seed,
        )
        if not args.quiet:
            print(f"[RDTX] Statistics written to {target}", flush=True)


if __name__ == "__main__":
    main()
