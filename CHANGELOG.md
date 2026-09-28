# Changelog

## 2.0.0 — RDTX VisualLab

### Added

- Local Flask web dashboard for running real RDTX transfers from a browser.
- Live Server-Sent Events stream for sender/receiver protocol activity.
- Selective Repeat window visualization driven by real ACK events.
- File upload, impairment controls, metrics and experiment history.
- SQLite-backed experiment persistence.
- Web integration test that completes a real localhost UDP transfer.
- Research-gap document positioning the project against ARQ simulators, Wireshark, ns-3 and Mininet.
- `rdtx-web` launcher with proper `--host`, `--port`, `--help` and `--version`.

### Preserved

- The original RDTX protocol engine remains the networking core.
- CLI transfer, benchmarking, Selective Repeat, CRC32, SHA-256, loss/corruption/reordering simulation and tests remain available.

## 1.3.0 — Demonstration and reporting polish

- Added explicit packet reordering, report-ready benchmark output and cleaner CLI behavior.

## 1.2.0 — Protocol hardening

- Enforced strict Selective Repeat sender-window semantics.
- Added peer endpoint validation and dedicated sender-window tests.

## 1.1.0 — Professional mini-project release

- Added unified CLI, trace mode, statistics, benchmarks, expanded CI and submission documentation.

## 1.0.0 — Initial release

- Reliable UDP transfer with sequence numbers, ACKs, CRC32, retransmission, buffering and SHA-256 verification.
