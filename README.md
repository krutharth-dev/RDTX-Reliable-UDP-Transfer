# RDTX VisualLab — Reliable UDP Transfer & Selective Repeat Analyzer

RDTX VisualLab is a Computer Networks mini-project that combines a **real reliable file-transfer protocol over UDP** with a local web dashboard for live Selective Repeat analysis.

The networking core is still RDTX: sequence numbers, individual ACKs, a strict sliding window, timeout-based retransmission, CRC32 validation, out-of-order buffering, duplicate handling and SHA-256 end-to-end verification. The VisualLab adds a browser interface that lets you run and observe those mechanisms without replacing them with a JavaScript simulation.

## Final project title

**RDTX VisualLab: Web-Based Reliable File Transfer and Selective Repeat Analysis over Unreliable UDP**

## What the web app shows

- Upload any file and transfer it through real localhost UDP sockets.
- Configure sender window size and chunk size.
- Inject DATA loss and ACK loss.
- Inject corruption, delay and explicit packet reordering.
- Watch DATA, ACK, drops, reordering and retransmission events live.
- Watch the Selective Repeat sender window move as ACKs arrive.
- See throughput, retransmissions, drops and final integrity.
- Keep recent experiment history in SQLite for comparison.

## Why this is still a CN project

The browser is only the control/visualization layer. The transfer itself is performed by the existing Python RDTX sender and receiver over UDP. See [docs/RESEARCH_GAP.md](docs/RESEARCH_GAP.md) for the project positioning against ARQ simulators, Wireshark, ns-3 and Mininet.

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

The CLI remains available:

~~~bash
rdtx --version
rdtx send demo.txt --loss 0.20 --trace
rdtx benchmark
~~~

## Suggested HOD demo

1. Upload `demo.txt` with no impairment.
2. Run with 20% DATA loss and 10% ACK loss; point out retransmissions.
3. Run with 100% reordering; point out reversed DATA events and successful reconstruction.
4. Change the Selective Repeat window and compare behavior.
5. Open experiment history and compare retransmissions/throughput.
6. Explain that the browser observes a real UDP transfer, not a simulated-only ARQ animation.

## Verification

~~~bash
make test
make verify
~~~

GitHub Actions installs the web dependency, runs the full protocol/CLI/web suite on Python 3.10–3.13, and performs the existing benchmark smoke test.
