"""Run repeatable RDTX localhost experiments and write a CSV report."""

from __future__ import annotations

import argparse
import csv
import socket
import tempfile
import threading
from pathlib import Path

from rdtx.receiver import RDTXReceiver
from rdtx.sender import RDTXSender


SCENARIOS = [
    {
        "name": "baseline",
        "data_loss": 0.00,
        "ack_loss": 0.00,
        "corruption": 0.00,
        "window": 8,
    },
    {
        "name": "data_loss_10pct",
        "data_loss": 0.10,
        "ack_loss": 0.00,
        "corruption": 0.00,
        "window": 8,
    },
    {
        "name": "data20_ack10",
        "data_loss": 0.20,
        "ack_loss": 0.10,
        "corruption": 0.00,
        "window": 8,
    },
    {
        "name": "corruption_5pct",
        "data_loss": 0.00,
        "ack_loss": 0.00,
        "corruption": 0.05,
        "window": 8,
    },
]


def free_udp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def run_scenario(source: Path, output_root: Path, scenario: dict[str, object], seed: int) -> dict[str, object]:
    port = free_udp_port()
    receiver = RDTXReceiver(
        "127.0.0.1",
        port,
        output_dir=output_root / str(scenario["name"]),
        ack_loss=float(scenario["ack_loss"]),
        seed=seed + 100,
        linger=0.10,
        verbose=False,
    )

    state: dict[str, object] = {}

    def receive() -> None:
        try:
            path, stats = receiver.receive_one()
            state["path"] = path
            state["receiver_stats"] = stats
        except BaseException as exc:
            state["error"] = exc

    thread = threading.Thread(target=receive, daemon=True)
    thread.start()

    sender = RDTXSender(
        "127.0.0.1",
        port,
        chunk_size=1024,
        window_size=int(scenario["window"]),
        timeout=0.06,
        max_retries=100,
        loss=float(scenario["data_loss"]),
        corruption=float(scenario["corruption"]),
        seed=seed,
        verbose=False,
    )
    sender_stats = sender.send_file(source)
    thread.join(timeout=10)

    if thread.is_alive():
        raise RuntimeError(f"receiver did not finish for scenario {scenario['name']}")
    if "error" in state:
        raise RuntimeError(f"receiver failed for scenario {scenario['name']}") from state["error"]

    received_path = state["path"]
    if not isinstance(received_path, Path) or received_path.read_bytes() != source.read_bytes():
        raise RuntimeError(f"integrity check failed for scenario {scenario['name']}")

    receiver_stats = state["receiver_stats"]
    return {
        "scenario": scenario["name"],
        "data_loss": scenario["data_loss"],
        "ack_loss": scenario["ack_loss"],
        "corruption": scenario["corruption"],
        "window": scenario["window"],
        "file_bytes": sender_stats.file_bytes,
        "elapsed_s": f"{sender_stats.elapsed:.6f}",
        "throughput_kib_s": f"{sender_stats.throughput_kib_s:.3f}",
        "retransmissions": sender_stats.retransmissions,
        "simulated_drops": sender_stats.simulated_drops,
        "simulated_corruptions": sender_stats.simulated_corruptions,
        "receiver_duplicates": receiver_stats.duplicate_data_packets,
        "receiver_checksum_errors": receiver_stats.checksum_errors,
        "integrity": "PASS",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run repeatable RDTX localhost benchmark scenarios.")
    parser.add_argument("--output", default="results/benchmark.csv", help="CSV output path")
    parser.add_argument("--size-kib", type=int, default=64, help="benchmark file size in KiB")
    parser.add_argument("--seed", type=int, default=2026, help="deterministic simulator seed")
    args = parser.parse_args()

    if args.size_kib < 1:
        parser.error("--size-kib must be >= 1")

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        source = root / "benchmark.bin"
        pattern = bytes(range(256))
        repeats = (args.size_kib * 1024 + len(pattern) - 1) // len(pattern)
        source.write_bytes((pattern * repeats)[: args.size_kib * 1024])

        rows = []
        for index, scenario in enumerate(SCENARIOS):
            print(f"[RDTX] Running {scenario['name']}...")
            rows.append(run_scenario(source, root / "received", scenario, args.seed + index))

    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"[RDTX] Benchmark complete: {output}")
    for row in rows:
        print(
            f"  {row['scenario']:<18} "
            f"retransmissions={row['retransmissions']:<4} "
            f"throughput={row['throughput_kib_s']} KiB/s "
            f"integrity={row['integrity']}"
        )


if __name__ == "__main__":
    main()
