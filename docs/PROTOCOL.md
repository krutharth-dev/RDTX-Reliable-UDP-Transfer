# RDTX Protocol Specification

RDTX is a compact application-layer reliable-data-transfer protocol implemented above UDP for education and experimentation.

## 1. Wire header

Every RDTX datagram begins with a fixed **26-byte** header encoded in network byte order.

| Field | Size | Description |
|---|---:|---|
| Magic | 4 B | ASCII RDTX; rejects unrelated UDP datagrams |
| Version | 1 B | Wire-protocol version |
| Type | 1 B | Packet type |
| Flags | 2 B | Reserved for future protocol extensions |
| Session ID | 4 B | Identifies a transfer |
| Sequence | 4 B | DATA sequence number |
| ACK | 4 B | Acknowledged DATA sequence number |
| Payload length | 2 B | Payload size in bytes |
| CRC32 | 4 B | CRC32 over zeroed-CRC header plus payload |

The maximum RDTX payload is 60,000 bytes, leaving room under the UDP datagram size limit.

## 2. Packet types

| Type | Direction | Purpose |
|---|---|---|
| HELLO | Sender -> Receiver | Advertise transfer metadata |
| HELLO_ACK | Receiver -> Sender | Accept the session |
| DATA | Sender -> Receiver | Carry one numbered file chunk |
| ACK | Receiver -> Sender | Acknowledge one DATA sequence number |
| FIN | Sender -> Receiver | Declare DATA phase complete |
| FIN_ACK | Receiver -> Sender | Confirm reassembly and integrity |
| ERROR | Receiver -> Sender | Report protocol-level rejection |

## 3. HELLO metadata

HELLO uses a JSON payload containing:

- filename
- size
- sha256
- chunk_size
- total_chunks
- window_size

The receiver validates field types/ranges, SHA-256 syntax and consistency between file size, chunk size and total chunk count before accepting the session. The filename is reduced to its basename so directory traversal components are not used.

## 4. Transfer state machine

~~~text
Sender                                  Receiver
  |                                        |
  |------------- HELLO ------------------->|
  |<---------- HELLO_ACK ------------------|
  |                                        |
  |--- DATA(0) DATA(1) ... DATA(W-1) ----->|
  |<---- ACK(0), ACK(2), ACK(1), ... ------|
  |                                        |
  | timeout for n -> retransmit DATA(n)     |
  |                                        |
  |--------------- FIN ------------------->|
  |<------------- FIN_ACK -----------------|
~~~

## 5. Selective Repeat behavior

The sender keeps up to window_size DATA packets in flight. Each outstanding sequence number has its own send timestamp and retry count.

When ACK(n) arrives:

1. n is removed from the outstanding set.
2. n is marked acknowledged.
3. A new DATA packet may enter the window.

When the timeout for n expires, only DATA(n) is retransmitted.

The receiver stores valid sequence numbers independently. Therefore, if DATA(4) is lost but DATA(5) and DATA(6) arrive, 5 and 6 remain buffered and acknowledged while only 4 is recovered.

## 6. Validation and integrity

### Datagram-level integrity

Packet.encode calculates CRC32 over the complete header with the CRC field set to zero plus the payload. Packet.decode recomputes the value and rejects mismatches.

### DATA validation

Before buffering a DATA packet, the receiver verifies:

- session ID and peer address
- sequence number is within the transfer
- payload length matches the expected chunk length
- sequence number has not already been stored

Duplicates are not stored twice, but they are ACKed again.

### File-level integrity

At FIN, the receiver checks:

1. FIN metadata matches HELLO metadata.
2. Every expected chunk is present.
3. Reassembled byte length equals the advertised file size.
4. SHA-256 equals the advertised digest.

Only then is FIN_ACK sent.

## 7. Control reliability

HELLO and FIN use timeout/retry exchanges. After successful reconstruction the receiver remains available for a short linger period, allowing it to retransmit FIN_ACK when a duplicate FIN arrives.

## 8. Error model

The built-in simulator can independently apply:

- packet drop probability
- corruption probability
- random delay up to a configured maximum

A deterministic random seed makes experiments repeatable.

## 9. Deliberate scope

RDTX does not implement congestion control, adaptive RTT/RTO, encryption, authentication, multi-client concurrency or production-grade flow control. These are documented as future enhancements rather than being hidden behind external libraries.
