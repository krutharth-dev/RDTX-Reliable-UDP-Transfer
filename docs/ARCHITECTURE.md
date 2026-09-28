# RDTX System Architecture

## 1. Overview

RDTX is an educational reliable-data-transfer protocol implemented above UDP. The project deliberately uses UDP so that reliability mechanisms are visible in application code instead of being hidden inside TCP.

The system has four logical layers:

1. **CLI layer** — accepts transfer and simulation parameters.
2. **Reliability layer** — Selective Repeat window, ACK tracking, timers and retransmissions.
3. **Protocol layer** — binary header, packet types, sequence numbers and CRC32.
4. **UDP layer** — actual datagram transmission.

## 2. Component diagram

~~~text
+------------------------- SENDER --------------------------+
| CLI -> File Reader -> Chunker -> Selective Repeat Window |
|                              -> Packet Encoder + CRC32    |
+-----------------------------------------------------------+
                             |
                             | UDP datagrams
                             v
                  +-----------------------+
                  | Impairment Simulator  |
                  | loss/corrupt/delay    |
                  +-----------------------+
                             |
                             v
+------------------------ RECEIVER -------------------------+
| Packet Decoder + CRC32 -> Sequence Validation -> Buffer   |
|                         -> Per-packet ACK -> Reassembly    |
|                         -> SHA-256 Final Verification      |
+-----------------------------------------------------------+
~~~

## 3. Module responsibilities

| Module | Responsibility |
|---|---|
| rdtx/protocol.py | Defines packet types, binary header, encoding/decoding and CRC32 validation |
| rdtx/sender.py | Splits files, maintains the Selective Repeat window, tracks ACKs and retransmits timed-out packets |
| rdtx/receiver.py | Validates metadata and chunks, buffers out-of-order data, handles duplicates and reconstructs the file |
| rdtx/simulator.py | Injects controlled packet loss, corruption and delay |
| rdtx/reporting.py | Exports experiment statistics as JSON |
| rdtx/config.py | Stores shared defaults and CLI validation helpers |
| rdtx/cli.py | Provides the unified rdtx send/receive command surface |

## 4. Protocol phases

### Phase A — Session establishment

The sender transmits a HELLO packet containing filename, file size, chunk size, chunk count, window size and SHA-256. The receiver validates those fields before returning HELLO_ACK.

### Phase B — Reliable data transfer

The sender may keep up to W DATA packets outstanding. Every DATA packet has an independent sequence number. The receiver accepts valid packets even when they arrive out of order and immediately ACKs the corresponding sequence number.

If the sender does not receive an ACK before the per-packet timer expires, only that unacknowledged packet is retransmitted. This is the defining behavior of Selective Repeat.

### Phase C — Completion

After every DATA packet has been acknowledged, the sender transmits FIN. The receiver verifies the final size and SHA-256, writes the reconstructed file and sends FIN_ACK. A short linger period lets the receiver answer a retransmitted FIN if the first FIN_ACK was lost.

## 5. Reliability invariants

- A DATA packet is stored at most once for a sequence number.
- A duplicate valid DATA packet is ACKed again but not written twice.
- A corrupted datagram is discarded because its CRC32 check fails.
- A file is accepted only if its final byte count and SHA-256 match the HELLO metadata.
- Invalid sequence numbers and inconsistent chunk lengths are discarded.
- Transfer completion occurs only after all sequence numbers are present.

## 6. Design choice: Selective Repeat vs Stop-and-Wait

Stop-and-Wait is simpler but permits only one outstanding packet, which underutilizes the network. Go-Back-N allows a window but retransmits multiple packets after one loss. RDTX uses Selective Repeat so the demo can show both pipelining and targeted retransmission.

## 7. Scope

RDTX demonstrates reliability, not full production transport behavior. Congestion control, encryption, authentication, multi-client concurrency, NAT traversal and adaptive RTT estimation are outside the mini-project scope.
