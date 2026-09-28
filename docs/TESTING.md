# Testing and Verification

Run `make test` for the automated suite, `make benchmark` for measured scenarios, or `make verify` for both.

| Area | Verification |
|---|---|
| Packet format | Encode/decode and malformed datagrams |
| CRC32 | Bit corruption detection |
| Selective Repeat | Strict base/window movement |
| ACK handling | Out-of-order and duplicate ACK behavior |
| Peer validation | Unexpected UDP endpoints ignored |
| Metadata | Chunk count, SHA-256 and filename checks |
| File transfer | Binary and empty files |
| Loss recovery | Deterministic DATA/ACK loss |
| Reordering | Reversed adjacent DATA pairs reconstruct correctly |
| CLI | Help, version, benchmark, graceful errors |
| Reporting | JSON, CSV and Markdown output |

GitHub Actions validates Python 3.10–3.13. Python 3.12 additionally performs a real benchmark smoke test and verifies both result files.

Historical failed CI runs remain immutable in GitHub. Submission status should be judged from the latest `main` run.
