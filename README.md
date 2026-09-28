# RDTX — Reliable Data Transfer over UDP

[![CI](https://github.com/krutharth-dev/RDTX-Reliable-UDP-Transfer/actions/workflows/tests.yml/badge.svg)](https://github.com/krutharth-dev/RDTX-Reliable-UDP-Transfer/actions/workflows/tests.yml)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Version](https://img.shields.io/badge/RDTX-1.3.0-blueviolet)
![License](https://img.shields.io/badge/License-MIT-green)
![Project](https://img.shields.io/badge/Computer%20Networks-Mini%20Project-orange)

**RDTX** is an educational reliable file-transfer protocol built over UDP. It makes transport-layer reliability visible by implementing the mechanisms explicitly instead of relying on TCP.

The DATA phase uses **Selective Repeat ARQ** with a strict sender window, individual ACKs, timeout-based retransmission, CRC32 packet validation, out-of-order buffering, duplicate handling, and SHA-256 end-to-end verification.

## Why this is more than a UDP file-transfer script

| Networking concept | RDTX implementation |
|---|---|
| Reliable delivery | Per-packet ACKs and retransmission timers |
| Sliding window | New DATA stays inside `[base, base + window_size)` |
| Selective Repeat | Only missing/unacknowledged packets are retransmitted |
| Packet corruption | CRC32 rejects damaged RDTX datagrams |
| Out-of-order delivery | Receiver buffers chunks by sequence number |
| Duplicate delivery | Duplicate DATA is re-ACKed but stored only once |
| End-to-end integrity | SHA-256 verifies the reconstructed file |
| Unreliable network | Loss, corruption, delay, ACK loss and explicit reordering |
| Measurement | JSON stats plus CSV and Markdown benchmark reports |

## Architecture

~~~text
          +-------------------- RDTX SENDER --------------------+
File ---> | Chunker -> SR Window -> Seq/CRC32 -> UDP TX        |
          +------------------------------------------------------+
                                  |
                    loss / corruption / delay
                       explicit reordering
                                  |
          +------------------- RDTX RECEIVER --------------------+
File <--- | SHA-256 <- Reassembly <- Seq Buffer <- CRC32 check  |
          +------------------------------------------------------+
                                  |
                         individual ACKs
~~~

## Quick start

~~~bash
git clone https://github.com/krutharth-dev/RDTX-Reliable-UDP-Transfer.git
cd RDTX-Reliable-UDP-Transfer
python3 -m unittest discover -s tests -v
~~~

Terminal 1:

~~~bash
python3 -m rdtx receive --port 9000 --output-dir received
~~~

Terminal 2:

~~~bash
python3 -m rdtx send demo.txt --host 127.0.0.1 --port 9000
~~~

The verified file appears at `received/demo.txt`.

## Best classroom demos

### Loss + retransmission

~~~bash
python3 -m rdtx receive --ack-loss 0.10 --seed 20 --trace
python3 -m rdtx send demo.txt --loss 0.25 --seed 10 --trace
~~~

### Explicit out-of-order delivery

~~~bash
python3 -m rdtx receive --trace
python3 -m rdtx send demo.txt --reorder 1.0 --seed 10 --trace
~~~

The sender intentionally transmits adjacent DATA pairs in reverse order. The receiver still reconstructs the original file from sequence numbers.

### Corruption recovery

~~~bash
python3 -m rdtx send demo.txt --corrupt 0.10 --seed 42 --trace
~~~

## Unified command line

~~~text
python3 -m rdtx send ...
python3 -m rdtx receive ...
python3 -m rdtx benchmark ...
~~~

Useful sender controls include `--window`, `--timeout`, `--loss`, `--corrupt`, `--delay-ms`, `--reorder`, `--seed`, `--trace`, and `--stats-json`.

## Benchmark and report results

~~~bash
python3 -m rdtx benchmark
~~~

This creates:

~~~text
results/benchmark.csv
results/benchmark.md
~~~

The Markdown file is report-ready and records environment details, impairment settings, retransmissions, reordered pairs, throughput and integrity status.

## One-command verification

~~~bash
make verify
~~~

## Repository structure

~~~text
RDTX-Reliable-UDP-Transfer/
├── rdtx/
│   ├── cli.py
│   ├── config.py
│   ├── protocol.py
│   ├── receiver.py
│   ├── reporting.py
│   ├── sender.py
│   ├── simulator.py
│   └── window.py
├── experiments/
│   └── benchmark.py
├── tests/
│   ├── test_benchmark.py
│   ├── test_cli.py
│   ├── test_integration.py
│   ├── test_peer_validation.py
│   ├── test_protocol.py
│   ├── test_validation.py
│   └── test_window.py
├── docs/
│   ├── ALGORITHMS.md
│   ├── ARCHITECTURE.md
│   ├── DEMO_GUIDE.md
│   ├── EXPERIMENTS.md
│   ├── MINI_PROJECT_REPORT.md
│   ├── PROTOCOL.md
│   ├── SUBMISSION_CHECKLIST.md
│   ├── TESTING.md
│   └── VIVA_GUIDE.md
├── .github/workflows/tests.yml
├── Makefile
├── CHANGELOG.md
├── CONTRIBUTING.md
├── demo.txt
└── pyproject.toml
~~~

## Documentation

- [Algorithms / pseudocode](docs/ALGORITHMS.md)
- [System architecture](docs/ARCHITECTURE.md)
- [Protocol specification](docs/PROTOCOL.md)
- [Experiment methodology](docs/EXPERIMENTS.md)
- [Testing strategy](docs/TESTING.md)
- [Demo/evaluation guide](docs/DEMO_GUIDE.md)
- [Mini-project report draft](docs/MINI_PROJECT_REPORT.md)
- [Viva preparation](docs/VIVA_GUIDE.md)
- [Submission checklist](docs/SUBMISSION_CHECKLIST.md)

## Quality

GitHub Actions verifies Python 3.10–3.13. The Python 3.12 job additionally runs a real localhost benchmark and verifies both generated result files. Expected runtime failures are presented as concise `RDTX error: ...` messages through the unified CLI rather than classroom-unfriendly tracebacks.

## Scope and limitations

RDTX is an educational protocol, not a TCP/QUIC replacement. It handles one active transfer per receiver process, uses a fixed retransmission timeout, buffers the complete transfer in memory, uses IPv4 sockets, and does not implement congestion control, authentication or encryption.

## License

MIT — see [LICENSE](LICENSE).
