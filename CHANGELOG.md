# Changelog

## 2.1.0 — VisualLab professional dashboard

### Added

- Scenario presets and labeled experiments.
- Filterable live protocol timeline.
- Richer live/final transfer metrics.
- Visual comparison of recent throughput and retransmissions.
- Per-run JSON export and reconstructed-file download.
- CSV export for experiment history.
- Engine health endpoint and active-run reporting.
- Configurable ACK corruption and ACK delay in the web UI.
- Upload-limit error handling and browser security headers.
- Bounded concurrent experiment execution.
- Web architecture documentation.

### Improved

- Event stream now includes structured sequence/window metadata.
- Experiment history is easier to inspect and compare.
- Dashboard is more responsive and presentation-ready.
- Backend validates non-finite numeric inputs and output download paths.

## 2.0.0 — RDTX VisualLab

- Added Flask dashboard, real UDP experiment orchestration, live SSE events, SQLite history, research-gap documentation, and web integration tests.

## 1.3.0 — Demonstration and reporting polish

- Added explicit packet reordering, report-ready benchmark output, and cleaner CLI behavior.

## 1.2.0 — Protocol hardening

- Enforced strict Selective Repeat sender-window semantics and peer validation.

## 1.0.0 — Initial reliable UDP transfer
