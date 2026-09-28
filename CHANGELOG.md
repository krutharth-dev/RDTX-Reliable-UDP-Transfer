# Changelog

## 1.3.0 — Demonstration and reporting polish

### Added

- Explicit DATA-packet reordering simulation with `--reorder`.
- Reordering counters and trace events.
- `rdtx benchmark` in the unified CLI.
- Report-ready Markdown benchmark output alongside CSV.
- Reordering integration tests and benchmark-report tests.
- Clean runtime error messages on the unified CLI.

### Improved

- Benchmark includes a deterministic reordering scenario.
- README, experiments, demo, report, testing and viva material match the implemented features.
- Makefile and README formatting defects were corrected.
- The experiments package is included in the installable project.

## 1.2.0 — Protocol hardening

- Enforced strict Selective Repeat sender-window semantics.
- Added peer endpoint validation and dedicated sender-window tests.

## 1.1.0 — Professional mini-project release

- Added unified CLI, trace mode, statistics, benchmarks, expanded CI and submission documentation.

## 1.0.0 — Initial release

- Reliable UDP transfer with sequence numbers, ACKs, CRC32, retransmission, buffering and SHA-256 verification.
