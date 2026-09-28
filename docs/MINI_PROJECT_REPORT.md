# RDTX: Reliable Data Transfer over Unreliable UDP

## Abstract

RDTX is a computer networks mini-project that implements reliable file transfer over UDP. UDP offers low-overhead datagram delivery but does not guarantee that packets arrive, arrive in order, or arrive only once. RDTX introduces application-layer reliability using sequence numbers, Selective Repeat acknowledgements, sliding-window transmission, timeout-based retransmission, CRC32 corruption detection, out-of-order buffering, duplicate handling, and SHA-256 end-to-end verification. A configurable network impairment simulator introduces controlled packet loss, corruption and delay, allowing the protocol to be evaluated under repeatable conditions.

## 1. Problem Statement

File transfer requires correctness even when individual network datagrams are lost, delayed, duplicated, reordered or corrupted. The problem addressed by this project is to design and demonstrate a reliable transfer mechanism while intentionally using UDP as the underlying transport service.

## 2. Objectives

- Build sender and receiver applications using UDP sockets.
- Design a compact custom packet format.
- Implement sequence numbers and acknowledgements.
- Implement Selective Repeat sliding-window transfer.
- Recover from packet and ACK loss through retransmission.
- Detect corrupted packets using CRC32.
- Reassemble out-of-order chunks correctly.
- Verify final file integrity using SHA-256.
- Simulate unreliable network conditions reproducibly.
- Measure retransmissions, errors and throughput.

## 3. Requirements

### Software

- Python 3.10 or later
- Standard Python library only
- macOS, Linux or Windows
- Git for version control

### Hardware

Two separate machines may be used over a LAN, but one laptop with two terminal windows is sufficient for demonstration because sender and receiver communicate through UDP sockets.

## 4. Methodology

The input file is divided into fixed-size chunks. Each chunk is placed in a DATA packet with a sequence number and CRC32. The sender maintains a configurable window of unacknowledged packets. The receiver independently acknowledges valid sequence numbers and buffers packets that arrive out of order. A timer is associated with each outstanding packet; expiration causes only that packet to be retransmitted.

Before data transfer, HELLO/HELLO_ACK establishes transfer metadata. After all DATA packets have been acknowledged, FIN/FIN_ACK completes the session. The receiver then validates the reconstructed file against the advertised byte count and SHA-256 digest.

## 5. Packet Structure

The fixed RDTX header contains magic bytes, protocol version, packet type, flags, session ID, sequence number, acknowledgement number, payload length and CRC32. Detailed field sizes are documented in PROTOCOL.md.

## 6. Algorithms

### Sender

1. Read the file and calculate SHA-256.
2. Split it into chunks.
3. Send HELLO and wait for HELLO_ACK.
4. Fill the sliding window with DATA packets.
5. Remove packets from the outstanding set as ACKs arrive.
6. Retransmit individual timed-out packets.
7. Send FIN after every DATA sequence number is acknowledged.
8. Finish after FIN_ACK.

### Receiver

1. Validate HELLO metadata.
2. Accept DATA packets belonging to the active session.
3. Verify CRC32 before protocol processing.
4. Validate sequence number and expected chunk length.
5. Buffer each new sequence number once.
6. ACK every valid DATA packet, including duplicates.
7. On FIN, verify that all chunks exist.
8. Reassemble the file, verify size and SHA-256, write it to disk and send FIN_ACK.

## 7. Testing

The repository includes automated tests for packet serialization, corruption detection, malformed packets, metadata consistency, CLI behavior, statistics export, ordinary end-to-end transfer and transfer with deterministic packet/ACK loss. GitHub Actions runs the suite on Python 3.10–3.13.

## 8. Experimental Evaluation

Run experiments/benchmark.py to generate measurements on the actual demonstration machine. Report at least the baseline, DATA-loss, ACK-loss and corruption scenarios. Relevant metrics are elapsed time, throughput, retransmissions, drops, duplicates and checksum errors.

### Results table

| Scenario | Loss/Corruption | Retransmissions | Throughput | Integrity |
|---|---|---:|---:|---|
| Baseline | Record measured values | | | PASS |
| DATA loss | Record measured values | | | PASS |
| DATA + ACK loss | Record measured values | | | PASS |
| Corruption | Record measured values | | | PASS |

Populate this table using results generated on the project laptop rather than invented values.

## 9. Advantages

- Makes transport reliability mechanisms visible and testable.
- Demonstrates pipelining through a sliding window.
- Recovers from both DATA and ACK loss.
- Supports reproducible impairment simulation.
- Uses no third-party runtime libraries.
- Includes automatic integrity verification and test automation.

## 10. Limitations

- One transfer/session is handled by a receiver process at a time.
- The complete file/chunk set is held in memory.
- Retransmission timeout is fixed rather than adaptive.
- Congestion control and production-grade flow control are not implemented.
- The protocol is not encrypted or authenticated.
- IPv4 is used by the current socket implementation.

## 11. Future Scope

- Adaptive RTT/RTO calculation.
- Receiver-advertised flow control.
- Congestion-control experiments.
- Streaming large files without buffering the full transfer.
- Multiple simultaneous sessions.
- IPv6 support.
- Authentication/encryption for secure transfer.
- GUI visualization of window movement and packet loss.

## 12. Conclusion

RDTX demonstrates that reliable delivery can be constructed over an unreliable datagram service by combining sequencing, acknowledgements, timers, retransmission, buffering and integrity checks. Because the implementation exposes each mechanism directly, it provides a practical demonstration of concepts normally studied in the transport-layer portion of Computer Networks.

## References

- J. F. Kurose and K. W. Ross, Computer Networking: A Top-Down Approach.
- RFC 768, User Datagram Protocol.
- Python documentation: socket module.
