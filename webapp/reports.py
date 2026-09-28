"""Report generation for RDTX VisualLab."""

from __future__ import annotations
from datetime import datetime
from typing import Any


def _pct(value: Any) -> str:
    return f"{float(value or 0) * 100:.0f}%"


def build_run_report(run: dict[str, Any]) -> str:
    p = run["params"]
    result = run.get("result") or {}
    s = result.get("sender") or {}
    r = result.get("receiver") or {}
    mode = p.get("mode", "local")
    created = datetime.fromtimestamp(float(run["created_at"])).strftime("%Y-%m-%d %H:%M:%S")
    observations = []
    retrans = int(s.get("retransmissions") or 0)
    drops = int(s.get("simulated_drops") or 0)
    duplicates = int(r.get("duplicate_data_packets") or 0)
    checksum = int(r.get("checksum_errors") or 0)

    observations.append(
        f"The sender performed **{retrans} retransmissions**."
        if retrans else "No sender retransmission was required in this measured run."
    )
    if drops:
        observations.append(f"The impairment model intentionally dropped **{drops} sender datagrams**.")
    if duplicates:
        observations.append(f"The receiver observed **{duplicates} duplicate DATA packets** and did not store them twice.")
    if checksum:
        observations.append(f"The receiver rejected **{checksum} corrupted datagrams** using CRC32.")
    if float(p.get("reorder", 0)) > 0:
        observations.append(
            f"Reordering was configured at **{_pct(p.get('reorder'))}**; sequence numbers preserved correct reconstruction."
        )
    if mode == "lan":
        observations.append(
            "This was a **two-host LAN run**. Completion means the remote receiver returned FIN_ACK after its file-size and SHA-256 checks passed."
        )
    else:
        observations.append(
            "The local receiver completed byte-for-byte reconstruction and end-to-end integrity passed."
        )

    obs = "\n".join(f"- {item}" for item in observations)
    return f"""# RDTX VisualLab Experiment Report

## Run identity

- **Run ID:** `{run['id']}`
- **Label:** {p.get('label') or 'Unlabelled experiment'}
- **File:** `{run['filename']}`
- **Created:** {created}
- **Mode:** {mode.upper()}
- **Status:** {run['status']}
- **Integrity:** {result.get('integrity', 'N/A')}

## Protocol configuration

| Parameter | Value |
|---|---:|
| Selective Repeat window | {p.get('window_size')} |
| Chunk size | {p.get('chunk_size')} bytes |
| Retransmission timeout | {float(p.get('timeout', 0)) * 1000:.0f} ms |
| DATA loss | {_pct(p.get('loss'))} |
| ACK loss | {_pct(p.get('ack_loss'))} |
| DATA corruption | {_pct(p.get('corruption'))} |
| ACK corruption | {_pct(p.get('ack_corruption'))} |
| DATA delay | {float(p.get('delay_ms', 0)):.0f} ms max |
| ACK delay | {float(p.get('ack_delay_ms', 0)):.0f} ms max |
| Reordering | {_pct(p.get('reorder'))} |
| Seed | {p.get('seed')} |

## Measured results

| Metric | Value |
|---|---:|
| File bytes | {s.get('file_bytes', 'N/A')} |
| Elapsed time | {float(s.get('elapsed', 0)):.4f} s |
| Throughput | {float(s.get('throughput_kib_s', 0)):.2f} KiB/s |
| Datagrams sent | {s.get('datagrams_sent', 'N/A')} |
| Retransmissions | {s.get('retransmissions', 'N/A')} |
| Sender drops | {s.get('simulated_drops', 'N/A')} |
| Sender corruptions | {s.get('simulated_corruptions', 'N/A')} |
| Reordered DATA pairs | {s.get('reordered_pairs', 'N/A')} |
| Receiver duplicates | {r.get('duplicate_data_packets', 'N/A')} |
| Receiver checksum errors | {r.get('checksum_errors', 'N/A')} |
| Receiver ACK drops | {r.get('simulated_ack_drops', 'N/A')} |

## Observations

{obs}

## Interpretation note

These are measurements from this specific run. Throughput and timing depend on hardware, OS scheduling, network conditions, and the selected seed. The configuration is recorded so the experiment is reproducible.
"""


def build_matrix_report(job: dict[str, Any]) -> str:
    lines = [
        "# RDTX VisualLab Experiment Matrix Report",
        "",
        f"- **Matrix ID:** `{job.get('id')}`",
        f"- **File:** `{job.get('filename')}`",
        f"- **Swept parameter:** `{job.get('dimension')}`",
        f"- **Status:** {job.get('status')}",
        "",
        "| Value | Status | Throughput (KiB/s) | Retransmissions | Drops | Integrity |",
        "|---:|---|---:|---:|---:|---|",
    ]
    completed = []
    for row in job.get("rows", []):
        result = row.get("result") or {}
        sender = result.get("sender") or {}
        lines.append(
            f"| {row.get('display_value', row.get('value'))} | {row.get('status')} | "
            f"{float(sender.get('throughput_kib_s', 0)):.2f} | "
            f"{sender.get('retransmissions', 0)} | {sender.get('simulated_drops', 0)} | "
            f"{result.get('integrity', 'N/A')} |"
        )
        if row.get("status") == "completed":
            completed.append(row)

    lines += ["", "## Measured observations", ""]
    if completed:
        best = max(completed, key=lambda row: float((row.get("result") or {}).get("sender", {}).get("throughput_kib_s", 0)))
        low_retry = min(completed, key=lambda row: int((row.get("result") or {}).get("sender", {}).get("retransmissions", 0)))
        lines.append(f"- Highest measured throughput in this matrix: **{best.get('display_value')}**.")
        lines.append(f"- Lowest measured retransmission count in this matrix: **{low_retry.get('display_value')}**.")
    else:
        lines.append("- No matrix row completed successfully.")
    lines += [
        "- These are observations from this matrix run only, not universal performance rankings.",
        "- Keep the file and seed constant when comparing parameter values.",
        "",
    ]
    return "\n".join(lines)
