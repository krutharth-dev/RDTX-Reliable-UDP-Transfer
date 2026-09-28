# RDTX — Reliable Data Transfer over UDP

[![CI](https://github.com/krutharth-dev/RDTX-Reliable-UDP-Transfer/actions/workflows/tests.yml/badge.svg)](https://github.com/krutharth-dev/RDTX-Reliable-UDP-Transfer/actions/workflows/tests.yml)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Project](https://img.shields.io/badge/Computer%20Networks-Mini%20Project-orange)

**RDTX** is an educational reliable file-transfer protocol implemented on top of UDP. It demonstrates how reliability can be built when the underlying transport does not guarantee delivery, ordering, duplicate suppression, or retransmission.

The project exposes the networking concepts directly instead of hiding them behind TCP: **Selective Repeat, sliding windows, sequence numbers, ACKs, retransmission timers, CRC32, out-of-order buffering, duplicate handling, impairment simulation, and end-to-end SHA-256 verification**.

## Project objectives

- Implement reliable file transfer using UDP sockets.
- Demonstrate Selective Repeat ARQ with a configurable sliding window.
- Recover from DATA-packet and ACK loss.
- Detect corrupted datagrams and trigger recovery.
- Handle out-of-order and duplicate packets safely.
- Verify the reconstructed file end-to-end.
- Generate reproducible measurements for mini-project analysis.

## Key features

| Area | Implementation |
|---|---|
| Reliability | Textbook Selective Repeat sender window with per-packet ACK/retransmission |
| Integrity | CRC32 per datagram + SHA-256 for the completed file |
| Windowing | Configurable sender window bounded by `base + window_size` |
| Failure simulation | DATA/ACK loss, corruption and delay |
| Observability | Live packet trace mode and transfer summaries |
| Experiments | JSON statistics export + automated CSV benchmark |
| Validation | HELLO metadata, sequence range and chunk-length checks |
| Quality | Unit/integration tests and GitHub Actions for Python 3.10–3.13 |
| Dependencies | Python standard library only |

## Architecture

~~~text
          +-------------------- RDTX SENDER --------------------+
File ---> | Chunking -> Sliding Window -> Seq/CRC32 -> UDP TX  |
          +------------------------------------------------------+
                                  |
                         unreliable datagrams
                        loss / corrupt / delay
                                  |
          +------------------- RDTX RECEIVER --------------------+
File <--- | SHA-256 <- Reassembly <- Buffer <- CRC32/Seq check  |
          +------------------------------------------------------+
                                  |
                         per-packet ACKs
~~~

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full component and protocol design.

## Repository structure

~~~text
RDTX-Reliable-UDP-Transfer/
├── rdtx/
│   ├── __main__.py       # python -m rdtx entry point
│   ├── cli.py            # unified send/receive command
│   ├── config.py         # defaults and CLI validation
│   ├── protocol.py       # packet format and CRC32
│   ├── sender.py         # Selective Repeat sender
│   ├── receiver.py       # ACK, buffering and reassembly
│   ├── simulator.py      # loss/corruption/delay simulator
│   └── reporting.py      # JSON experiment statistics
├── experiments/
│   └── benchmark.py      # repeatable localhost benchmark
├── tests/
│   ├── test_cli.py
│   ├── test_integration.py
│   ├── test_protocol.py
│   └── test_validation.py
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DEMO_GUIDE.md
│   ├── EXPERIMENTS.md
│   ├── MINI_PROJECT_REPORT.md
│   ├── PROTOCOL.md
│   └── VIVA_GUIDE.md
├── .github/workflows/tests.yml
├── Makefile
├── CHANGELOG.md
├── CONTRIBUTING.md
├── demo.txt
└── pyproject.toml
~~~

## Requirements

- Python 3.10 or newer
- macOS, Linux or Windows
- No third-party runtime packages

## Quick start

Clone the project:

~~~bash
git clone https://github.com/krutharth-dev/RDTX-Reliable-UDP-Transfer.git
cd RDTX-Reliable-UDP-Transfer
~~~

Run the tests first:

~~~bash
python3 -m unittest discover -s tests -v
~~~

### Terminal 1 — receiver

~~~bash
python3 -m rdtx receive --port 9000 --output-dir received
~~~

### Terminal 2 — sender

~~~bash
python3 -m rdtx send demo.txt --host 127.0.0.1 --port 9000
~~~

The reconstructed file is written to received/demo.txt.

## Live classroom demo

Trace every important protocol event:

**Terminal 1**

~~~bash
python3 -m rdtx receive --port 9000 --ack-loss 0.10 --seed 20 --trace
~~~

**Terminal 2**

~~~bash
python3 -m rdtx send demo.txt --host 127.0.0.1 --loss 0.25 --seed 10 --trace
~~~

The trace makes dropped packets, received ACKs and retransmissions visible while the final file still passes SHA-256 verification.

## Simulating network problems

Sender-side examples:

~~~bash
# 20% DATA loss
python3 -m rdtx send demo.txt --loss 0.20 --seed 10

# 5% corruption
python3 -m rdtx send demo.txt --corrupt 0.05 --seed 42

# Random delay up to 80 ms
python3 -m rdtx send demo.txt --delay-ms 80 --seed 42
~~~

Receiver-side ACK impairment:

~~~bash
python3 -m rdtx receive --ack-loss 0.15 --ack-corrupt 0.03 --ack-delay-ms 50 --seed 20
~~~

## Experiment results

Generate a repeatable benchmark:

~~~bash
python3 -m experiments.benchmark
~~~

or:

~~~bash
make benchmark
~~~

This writes results/benchmark.csv with throughput, retransmissions, drops, corruption events, duplicates, checksum errors and integrity status for several scenarios.

For an individual run, export JSON:

~~~bash
python3 -m rdtx receive --stats-json results/receiver.json
python3 -m rdtx send demo.txt --loss 0.20 --seed 10 --stats-json results/sender.json
~~~

See [docs/EXPERIMENTS.md](docs/EXPERIMENTS.md) for the recommended experiment matrix and interpretation.

## Packet flow

~~~text
Sender                                      Receiver
  |                                             |
  |---------------- HELLO --------------------->|
  |<------------- HELLO_ACK --------------------|
  |                                             |
  |---- DATA(0), DATA(1), ... DATA(W-1) ------>|
  |<------ ACK(0), ACK(2), ACK(1), ... --------|
  |                                             |
  |  timeout(seq=n) -> retransmit DATA(n)       |
  |                                             |
  |----------------- FIN ---------------------->|
  |<-------------- FIN_ACK ---------------------|
~~~

Only unacknowledged timed-out packets are retransmitted.

## Packet header

Every datagram carries a fixed 26-byte RDTX header containing:

- Magic value and protocol version
- Packet type
- Session ID
- Sequence number
- ACK number
- Payload length
- CRC32

The exact binary layout is documented in [docs/PROTOCOL.md](docs/PROTOCOL.md).

## Development commands

~~~bash
make check
make test
make benchmark
make demo-receive
make demo-send
make demo-lossy
~~~

The package can also be installed in editable mode:

~~~bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
rdtx --help
~~~

## Documentation for submission

- **Algorithms:** [docs/ALGORITHMS.md](docs/ALGORITHMS.md)\n- **Architecture:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Demo/evaluation guide:** [docs/DEMO_GUIDE.md](docs/DEMO_GUIDE.md)
- **Protocol specification:** [docs/PROTOCOL.md](docs/PROTOCOL.md)
- **Experiment methodology:** [docs/EXPERIMENTS.md](docs/EXPERIMENTS.md)
- **Mini-project report draft:** [docs/MINI_PROJECT_REPORT.md](docs/MINI_PROJECT_REPORT.md)
- **Viva preparation:** [docs/VIVA_GUIDE.md](docs/VIVA_GUIDE.md)

## Testing

The automated suite covers packet serialization, CRC corruption detection, malformed datagrams, metadata validation, filename sanitization, CLI behavior, statistics export, strict Selective Repeat window movement, peer-endpoint filtering, empty-file transfer, ordinary localhost transfer, and deterministic lossy/corruption recovery.

GitHub Actions executes compile checks, tests and package installation on Python 3.10, 3.11, 3.12 and 3.13.

## Scope and limitations

RDTX is intentionally an educational protocol rather than a replacement for TCP or QUIC. It currently handles one transfer per receiver process, uses a fixed retransmission timeout, keeps the transfer in memory, uses IPv4 sockets, and does not implement congestion control, authentication or encryption.

These boundaries keep the core Computer Networks mechanisms visible and suitable for a mini-project demonstration.

## License

MIT — see [LICENSE](LICENSE).
