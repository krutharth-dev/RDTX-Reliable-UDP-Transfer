# RDTX Protocol Specification

Every RDTX datagram begins with a fixed 26-byte network-byte-order header.

| Field | Size | Purpose |
|---|---:|---|
| Magic | 4 B | Identifies RDTX traffic |
| Version | 1 B | Wire version |
| Type | 1 B | HELLO, HELLO_ACK, DATA, ACK, FIN, FIN_ACK or ERROR |
| Flags | 2 B | Reserved |
| Session ID | 4 B | Transfer identifier |
| Sequence | 4 B | DATA sequence number |
| ACK | 4 B | Acknowledged sequence number |
| Payload length | 2 B | Payload bytes |
| CRC32 | 4 B | Datagram integrity check |

## Transfer

1. HELLO advertises filename, size, SHA-256, chunk size, chunk count and window size.
2. HELLO_ACK accepts the session.
3. DATA packets are sent within the Selective Repeat range `[base, base + window_size)`.
4. ACK(n) confirms one sequence number.
5. Per-packet timeout retransmits only the missing DATA packet.
6. FIN requests completion.
7. The receiver verifies all chunks, file size and SHA-256 before FIN_ACK.

## Out-of-order and duplicate handling

The receiver stores valid DATA by sequence number rather than arrival order. Duplicate DATA is not stored twice but is ACKed again. The `--reorder` demonstration option intentionally reverses adjacent DATA-packet transmit order without changing the wire format.

## Error model

RDTX can simulate outgoing loss, corruption, delay and DATA reordering. ACK/control loss, corruption and delay can also be applied on the receiver side. Fixed seeds make demonstrations repeatable.

RDTX is educational and deliberately omits congestion control, adaptive RTO, encryption, authentication and multi-session production transport behavior.
