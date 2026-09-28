"""Run repeatable RDTX localhost experiments and write CSV/Markdown reports."""

from __future__ import annotations

import argparse
import csv
import platform
import socket
import tempfile
import threading
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path

from rdtx.receiver import RDTXReceiver
from rdtx.sender import RDTXSender


SCENARIOS = [
    {"name": "baseline", "data_loss": 0.00, "ack_loss": 0.00, "corruption": 0.00, "reorder": 0.00, "window": 8},
    {"name": "data_loss_10pct", "data_loss": 0.10, "ack_loss": 0.00, "corruption": 0.00, "reorder": 0.00, "window": 8},
    {"name": "data20_ack10", "data_loss": 0.20, "ack_loss": 0.10, "corruption": 0.00, "reorder": 0.00, "window": 8},
    {"name": "corruption_5pct", "data_loss": 0.00, "ack_loss": 0.00, "corruption": 0.05, "reorder": 0.00, "window": 8},
    {"name": "reorder_all_pairs", "data_loss": 0.00, "ack_loss": 0.00, "corruption": 0.00, "reorder": 1.00, "window": 8},
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
        reorder_rate=float(scenario["reorder"]),
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
        "reorder": scenario["reorder"],
        "window": scenario["window"],
        "file_bytes": sender_stats.file_bytes,
        "elapsed_s": f"{sender_stats.elapsed:.6f}",
        "throughput_kib_s": f"{sender_stats.throughput_kib_s:.3f}",
        "retransmissions": sender_stats.retransmissions,
        "simulated_drops": sender_stats.simulated_drops,
        "simulated_corruptions": sender_stats.simulated_corruptions,
        "reordered_pairs": sender_stats.reordered_pairs,
        "receiver_duplicates": receiver_stats.duplicate_data_packets,
        "receiver_checksum_errors": receiver_stats.checksum_errors,
        "integrity": "PASS",
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: list[dict[str, object]], *, size_kib: int, seed: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "# RDTX Benchmark Results",
        "",
        f"- Generated: {generated}",
        f"- Python: {platform.python_version()}",
        f"- Platform: {platform.system()} {platform.release()}",
        f"- File size: {size_kib} KiB",
        f"- Base seed: {seed}",
        "",
        "| Scenario | DATA loss | ACK loss | Corruption | Reorder | Retransmissions | Reordered pairs | Throughput (KiB/s) | Integrity |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            "| {scenario} | {data_loss:.0%} | {ack_loss:.0%} | {corruption:.0%} | "
            "{reorder:.0%} | {retransmissions} | {reordered_pairs} | "
            "{throughput_kib_s} | {integrity} |".format(
                scenario=row["scenario"],
                data_loss=float(row["data_loss"]),
                ack_loss=float(row["ack_loss"]),
                corruption=float(row["corruption"]),
                reorder=float(row["reorder"]),
                retransmissions=row["retransmissions"],
                reordered_pairs=row["reordered_pairs"],
                throughput_kib_s=row["throughput_kib_s"],
                integrity=row["integrity"],
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation notes",
            "",
            "- Loss and corruption should increase recovery work without changing final file integrity.",
            "- The reordering scenario intentionally transmits adjacent DATA pairs in reverse order to demonstrate receiver buffering.",
            "- Throughput is machine- and timer-dependent; use results from the actual demo laptop in the report.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run repeatable RDTX localhost benchmark scenarios.")
    parser.add_argument("--output", default="results/benchmark.csv", help="CSV output path")
    parser.add_argument("--markdown", default=None, help="Markdown output path (default: CSV name with .md)")
    parser.add_argument("--size-kib", type=int, default=64, help="benchmark file size in KiB")
    parser.add_argument("--seed", type=int, default=2026, help="deterministic simulator seed")
    args = parser.parse_args(argv)

    if args.size_kib < 1:
        parser.error("--size-kib must be >= 1")

    output = Path(args.output)
    markdown = Path(args.markdown) if args.markdown else output.with_suffix(".md")

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

    write_csv(output, rows)
    write_markdown(markdown, rows, size_kib=args.size_kib, seed=args.seed)

    print(f"[RDTX] Benchmark CSV: {output}")
    print(f"[RDTX] Benchmark report: {markdown}")
    for row in rows:
        print(
            f"  {row['scenario']:<18} "
            f"retransmissions={row['retransmissions']:<4} "
            f"reordered={row['reordered_pairs']:<3} "
            f"throughput={row['throughput_kib_s']} KiB/s "
            f"integrity={row['integrity']}"
        )


if __name__ == "__main__":
    main()
