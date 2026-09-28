# RDTX: Reliable Data Transfer over Unreliable UDP

## Abstract

RDTX is a Computer Networks mini-project that implements reliable file transfer over UDP. It adds Selective Repeat sequencing, individual acknowledgements, a strict sliding window, timeout-based retransmission, CRC32 datagram validation, out-of-order buffering, duplicate handling and SHA-256 end-to-end verification. Controlled loss, corruption, delay, ACK loss and explicit packet reordering allow repeatable demonstrations and measurements.

## Problem Statement

Reliable file transfer must remain correct when datagrams are lost, delayed, duplicated, corrupted or delivered out of order. RDTX demonstrates how those reliability properties can be built above UDP.

## Objectives

- Build sender and receiver applications using UDP sockets.
- Implement a custom packet header with sequence and acknowledgement fields.
- Implement Selective Repeat ARQ.
- Recover from DATA and ACK loss.
- Detect corruption with CRC32.
- Buffer and reassemble out-of-order chunks.
- Verify the completed file with SHA-256.
- Simulate network impairments reproducibly.
- Measure retransmissions, reordered pairs, errors and throughput.

## Methodology

The sender divides a file into numbered chunks and permits new DATA only inside `[base, base + window_size)`. ACKs may arrive out of order, but the base advances only across a contiguous acknowledged prefix. Per-packet timers cause targeted retransmission. The receiver verifies CRC32, validates sequence and payload length, buffers chunks by sequence number, re-ACKs duplicates, and performs SHA-256 verification before accepting the file.

## Testing

Automated tests cover packet serialization, corruption, malformed datagrams, metadata, CLI behavior, statistics, strict window movement, peer validation, empty files, explicit reordering, normal transfer and deterministic packet/ACK loss. CI runs on Python 3.10–3.13.

## Experimental Evaluation

Run:

~~~bash
python3 -m rdtx benchmark
~~~

Use `results/benchmark.md` in the report. It contains baseline, loss, combined DATA/ACK loss, corruption and explicit reordering scenarios.

## Advantages

- Core transport concepts are visible in code and trace output.
- Pipelining and targeted retransmission are demonstrable.
- Both per-packet and final-file integrity are checked.
- Experiments are deterministic with fixed seeds.
- No third-party runtime dependencies are required.

## Limitations

- One active receiver session per process.
- Complete transfer buffered in memory.
- Fixed retransmission timeout.
- IPv4 only.
- No congestion control, encryption or authentication.

## Future Scope

Adaptive RTT/RTO, streaming large files, multiple concurrent sessions, IPv6, flow/congestion control, and optional authenticated encryption.

## Conclusion

RDTX demonstrates that reliable delivery can be constructed over an unreliable datagram service using sequencing, acknowledgements, windows, timers, retransmission, buffering and integrity checks.
