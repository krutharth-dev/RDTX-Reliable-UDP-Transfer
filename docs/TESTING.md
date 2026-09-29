# Testing and Verification

RDTX VisualLab is tested at packet, state-machine, transfer, CLI, web API, LAN, matrix, packaging, and benchmark levels.

## Local commands

Compile the project:

~~~bash
make check
~~~

Run automated tests:

~~~bash
make test
~~~

Run tests plus the standard benchmark:

~~~bash
make verify
~~~

Run the pre-evaluation readiness sequence:

~~~bash
make demo-check
~~~

## Coverage areas

| Area | Verification |
|---|---|
| Packet format | Encode/decode and malformed datagram rejection |
| CRC32 | Corrupted packet detection |
| Selective Repeat | Strict base/window movement |
| ACK handling | Out-of-order and duplicate ACK behavior |
| Peer validation | Unexpected UDP endpoints ignored |
| Metadata | File/chunk/hash consistency |
| Local transfer | Binary and empty-file transfers |
| Loss recovery | Deterministic DATA and ACK loss |
| Reordering | Reversed DATA pairs reconstruct correctly |
| Web API | Validation, health, exports, downloads |
| LAN mode | Sender communicates with a separately started receiver |
| Matrix Lab | Multiple real UDP runs execute sequentially |
| Reporting | JSON, CSV, per-run Markdown, matrix Markdown |
| Packaging | Installed CLI/web entry points |
| Benchmark | Real localhost transfers produce CSV and Markdown evidence |

## Continuous integration

GitHub Actions runs the suite on Python 3.10, 3.11, 3.12, and 3.13.

The workflow also:

- runs `pip check` after installation;
- applies a 10-minute job timeout;
- cancels superseded runs on the same branch/ref;
- runs the real benchmark smoke test on Python 3.12;
- retains Python 3.12 benchmark CSV/Markdown as a CI artifact for 14 days.

Historical failed runs remain visible in GitHub. The relevant submission state is the latest successful run associated with the current `main` commit.
