# Changelog

## 2.2.1 — Professional finish

### Improved

- Rebuilt the README as a complete project landing page with architecture, demo flow, evidence, scope, and documentation map.
- Updated stale submission/testing/research-gap documentation to match VisualLab 2.2.
- Added experimental reproducibility guidance and demo troubleshooting.
- Added security/deployment notes for the local web app and LAN receiver.
- Added a pull-request template and stronger contribution guidance.
- Added `make demo-check` for pre-evaluation verification.
- Restored richer Python package metadata and project links.
- Hardened CI with dependency checks, timeouts, run concurrency, manual dispatch, pip caching, and retained benchmark artifacts.

### Changed

- Version bumped to 2.2.1. Protocol behavior and wire format are unchanged.

## 2.2.0 — LAN, reports, and matrix experiments

- Added two-host LAN sender mode.
- Added generated remote-receiver command for ACK impairment.
- Added downloadable per-run Markdown reports.
- Added Matrix Lab for window, loss, corruption, and reordering sweeps.
- Added downloadable matrix reports.
- Added LAN and matrix integration tests and documentation.

## 2.1.0 — Professional dashboard

- Added presets, filtered telemetry, comparison and export workflow, and backend hardening.

## 2.0.0 — RDTX VisualLab

- Added Flask dashboard over the real reliable-UDP engine.

## 1.x

- Built and hardened the Selective Repeat reliable UDP protocol engine.
