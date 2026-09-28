# Changelog

All notable project changes are recorded here.

## 1.2.0 — Final protocol hardening

### Corrected

- Enforces the textbook Selective Repeat sender-window rule: new sequence numbers remain inside `[base, base + window_size)`.
- Prevents the send window from advancing past a missing base packet merely because later ACKs arrived.
- Accepts control packets and ACKs only from the configured receiver UDP endpoint.

### Added

- Dedicated `SelectiveRepeatWindow` state model with focused unit tests.
- Window-base movement in trace output, making the ARQ algorithm easier to demonstrate.
- Counter for datagrams ignored from unexpected peers.

## 1.1.0 — Professional mini-project release

### Added

- Unified `python -m rdtx` command with send and receive subcommands.
- Trace mode for observing packet, ACK, and retransmission behavior during demos.
- JSON statistics export for repeatable experiments and report preparation.
- Professional architecture, experiment, report, demo, and viva documentation.
- Makefile shortcuts for testing and demonstrations.
- CI testing across multiple supported Python versions.
- Additional CLI and validation tests.

### Improved

- Receiver metadata validation and final FIN verification.
- Transfer summaries and simulator statistics.
- Project metadata and repository documentation.

## 1.0.0 — Initial release

- Reliable file transfer over UDP.
- Sequence numbers, ACKs, CRC32, retransmission, out-of-order buffering, and SHA-256 verification.
- Loss, corruption, and delay simulation.
- Unit and integration test suite.
