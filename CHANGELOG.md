# Changelog

All notable project changes are recorded here.

## 1.1.0 — Professional mini-project release

### Added

- Unified python -m rdtx command with send and receive subcommands.
- Trace mode for observing packet, ACK, and retransmission behavior during demos.
- JSON statistics export for repeatable experiments and report preparation.
- Professional architecture, experiment, report, and viva documentation.
- Makefile shortcuts for testing and demonstrations.
- CI testing across multiple supported Python versions.
- Additional CLI and validation tests.

### Improved

- Receiver metadata validation and final FIN verification.
- Transfer summaries and simulator statistics.
- Project metadata and repository documentation.

## 1.0.0 — Initial release

- Selective Repeat-style reliable file transfer over UDP.
- Sequence numbers, ACKs, CRC32, retransmission, out-of-order buffering, and SHA-256 verification.
- Loss, corruption, and delay simulation.
- Unit and integration test suite.
