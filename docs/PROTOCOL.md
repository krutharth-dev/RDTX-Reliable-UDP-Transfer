# RDTX Protocol Notes

RDTX is a small application-layer reliability protocol built on top of UDP. Its goal is to make the reliability mechanisms normally associated with a transport protocol visible and easy to experiment with.

## Packet header

Every datagram starts with a fixed 26-byte network-byte-order header:

| Field | Size | Purpose |
|---|---:|---|
| Magic | 4 B | ASCII RDTX, rejects unrelated UDP traffic |
| Version | 1 B | Protocol version |
| Type | 1 B | HELLO, HELLO_ACK, DATA, ACK, FIN, FIN_ACK, ERROR |
| Flags | 2 B | Reserved for future use |
| Session ID | 4 B | Identifies one transfer |
| Sequence | 4 B | DATA sequence number |
| ACK | 4 B | Acknowledged DATA sequence number |
| Payload length | 2 B | Number of payload bytes |
| CRC32 | 4 B | Integrity check over header-with-zero-CRC + payload |

## Transfer state machine

```text
Sender                                  Receiver
  |                                        |
  |------------- HELLO ------------------->|
  |<---------- HELLO_ACK ------------------|
  |                                        |
  |--- DATA(0) DATA(1) ... DATA(W-1) ----->|
  |<---- ACK(0), ACK(2), ACK(1), ... ------|
  |       timeout -> retransmit missing     |
  |                                        |
  |--------------- FIN ------------------->|
  |<------------- FIN_ACK -----------------|
```

The sender keeps up to window_size DATA packets in flight. Each packet has its own retransmission timer. ACKed packets leave the window immediately, so a lost packet does not force already-delivered packets to be sent again. The receiver accepts valid out-of-order DATA packets and ACKs each sequence number independently. This is Selective Repeat behavior.

## Reliability mechanisms

- **Sequence numbers** identify DATA chunks and duplicates.
- **ACKs** confirm individual chunks.
- **Timeouts** trigger retransmission when an ACK does not arrive.
- **CRC32** detects damaged datagrams; corrupted packets are silently discarded and later retransmitted.
- **Out-of-order buffering** lets later packets be retained while an earlier packet is missing.
- **Duplicate handling** re-ACKs repeated DATA without storing it twice.
- **SHA-256 final verification** confirms that the reassembled file is byte-for-byte identical.
- **FIN retransmission support** keeps the receiver alive briefly after completion so a lost FIN_ACK can be recovered.

## Deliberate scope

RDTX is an educational protocol, not a replacement for TCP or QUIC. It does not implement congestion control, encryption, authentication, path migration, NAT traversal, or production-grade flow control. The project isolates the core reliability concepts so they are easy to inspect during a CN demonstration.
