# RDTX VisualLab — Reliable UDP Transfer & Selective Repeat Analyzer

**RDTX VisualLab** is a local-first Computer Networks experimentation app built around a real reliable file-transfer protocol over UDP.

The networking core implements strict **Selective Repeat ARQ**: sequence numbers, per-packet ACKs, a bounded sender window, timeout-based retransmission, CRC32 validation, out-of-order buffering, duplicate handling, and SHA-256 end-to-end verification. The web application configures and observes those real UDP transfers—it does not replace them with a browser-only simulation.

## Final project title

**RDTX VisualLab: Web-Based Reliable File Transfer and Selective Repeat Analysis over Unreliable UDP**

## Professional dashboard features

- Drag/select a real file and transfer it through localhost UDP sockets.
- Scenario presets for baseline, lossy link, corruption, and reordering.
- Configure window size, chunk size, timeout, deterministic seed, DATA/ACK loss, corruption, delay, and reordering.
- Live Selective Repeat window movement driven by actual ACK events.
- Filterable protocol timeline for DATA, ACK, retransmission, drop, and reorder events.
- Live throughput, elapsed time, drop, ACK, and retransmission counters.
- End-to-end result inspector with duplicate/ACK-drop metrics.
- Download the reconstructed received file directly from the browser.
- Export an individual experiment as JSON.
- Export the complete recent experiment history as CSV.
- Compare recent runs visually by throughput and retransmissions.
- SQLite-backed experiment history.
- Health/concurrency endpoint and upload limits for safer local operation.

## Run on macOS

~~~bash
git pull origin main
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
rdtx-web
~~~

Open:

~~~text
http://127.0.0.1:5000
~~~

If port 5000 is busy:

~~~bash
rdtx-web --port 5050
~~~

## Recommended evaluation sequence

1. **Baseline** — zero impairment; demonstrate normal window progression and PASS integrity.
2. **Lossy link** — 20% DATA loss + 10% ACK loss; demonstrate timeout/retransmission and duplicates.
3. **Reordering** — 100% adjacent-pair reordering; demonstrate out-of-order buffering.
4. **Corruption** — show CRC32 rejection followed by retransmission.
5. **Compare** — label runs and compare throughput/retransmissions in the dashboard.
6. **Evidence** — download the received file, export the run JSON, and export history CSV.

## API surface

| Endpoint | Purpose |
|---|---|
| `GET /api/health` | Engine/version/concurrency status |
| `POST /api/runs` | Start a real UDP experiment |
| `GET /api/runs/<id>` | Run state and results |
| `GET /api/runs/<id>/events` | Live Server-Sent Events stream |
| `GET /api/runs/<id>/download` | Download reconstructed file |
| `GET /api/runs/<id>/export` | Export run JSON |
| `GET /api/history` | Recent experiment history |
| `GET /api/history.csv` | Export history CSV |

## Verification

~~~bash
make test
make verify
~~~

CI installs the complete application and runs protocol, CLI, benchmark, and web integration tests on Python 3.10–3.13.

See:
- [Research gap](docs/RESEARCH_GAP.md)
- [Mini-project report](docs/MINI_PROJECT_REPORT.md)
- [Demo guide](docs/DEMO_GUIDE.md)
- [Viva guide](docs/VIVA_GUIDE.md)
- [Web architecture](docs/WEB_ARCHITECTURE.md)
