# Testing and Verification

RDTX is verified at protocol, state-machine, integration, CLI, packaging and experiment levels.

## Local verification

Run the full unit/integration suite:

~~~bash
make test
~~~

Run the repeatable benchmark:

~~~bash
make benchmark
~~~

Run both in sequence:

~~~bash
make verify
~~~

## Automated test coverage

| Test area | What is checked |
|---|---|
| Packet format | Encode/decode round trip and malformed datagram rejection |
| CRC32 | Bit corruption is detected |
| Selective Repeat | Window cannot slide past a missing base packet |
| ACK handling | Out-of-order, duplicate and unsent ACK behavior |
| Peer validation | Sender ignores datagrams from the wrong UDP endpoint |
| Metadata | Chunk count, SHA-256 format and filename sanitization |
| File transfer | Binary localhost transfer and empty-file transfer |
| Loss recovery | Deterministic DATA loss and ACK loss |
| CLI | Help, version and professional command options |
| Reporting | Structured JSON experiment output |
| Benchmark | CI smoke test writes a valid CSV after real UDP transfers |

## Continuous integration

GitHub Actions runs on Python 3.10, 3.11, 3.12 and 3.13. Each matrix job:

1. checks out the repository;
2. compiles rdtx, tests and experiments;
3. runs the complete unittest suite;
4. installs the package with no runtime dependencies.

Python 3.12 additionally runs a benchmark smoke test.

## Interpreting failures

A historical failed run remains visible on GitHub because commits and CI results are immutable records. The important state is the latest commit/PR check. A correction creates a new passing run; it does not rewrite an earlier failed run.

For submission, verify that the latest main-branch CI run is green and that make verify succeeds on the demonstration laptop.
