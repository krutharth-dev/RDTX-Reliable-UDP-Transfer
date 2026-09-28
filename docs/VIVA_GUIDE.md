# RDTX Viva Guide

## What problem does RDTX solve?

UDP does not guarantee delivery, ordering, duplicate suppression or retransmission. RDTX adds these reliability mechanisms at the application layer so their behavior can be studied directly.

## Why use UDP instead of TCP?

Using TCP would hide the main learning objective because TCP already performs sequencing, acknowledgements and retransmissions. UDP gives a minimal datagram service on which RDTX can implement those mechanisms explicitly.

## Which ARQ technique is used?

RDTX uses Selective Repeat ARQ. Multiple packets may be outstanding, the receiver ACKs individual sequence numbers, and the sender retransmits only packets whose ACKs are missing after timeout. The sender window is strictly bounded by `[base, base + window_size)`.

## What makes the implementation Selective Repeat rather than only "multiple packets in flight"?

The sender keeps a base sequence number. New packets can enter only while their sequence number is below `base + window_size`. ACKs may arrive out of order, but the base cannot advance past a missing lower sequence number. Retransmission is per packet rather than retransmitting the entire later range.

## Why is a sliding window required?

A window allows multiple packets to be in flight at the same time. This provides pipelining and demonstrates a key difference from Stop-and-Wait.

## What happens if DATA packet 4 is lost but packets 5 and 6 arrive?

The receiver buffers 5 and 6 and ACKs them. Packet 4 remains unacknowledged. When its timer expires, the sender retransmits only packet 4.

## What happens if an ACK is lost?

The sender eventually times out and retransmits that DATA packet. The receiver recognizes it as a duplicate, does not store it twice, and sends the ACK again.

## Why use CRC32 and SHA-256?

CRC32 performs packet-level corruption detection for each datagram. SHA-256 performs an end-to-end integrity check on the fully reconstructed file. They operate at different scopes.

## Does UDP itself corrupt packets?

IP/UDP includes checksum mechanisms, and real networks can discard damaged packets. The project injects corruption deliberately so the application-level CRC/recovery behavior can be demonstrated consistently.

## Why is the timeout fixed?

A fixed timeout keeps the mini-project understandable and repeatable. Production protocols normally estimate round-trip time dynamically; adaptive RTT/RTO calculation is a valid future enhancement.

## Is this a replacement for TCP?

No. RDTX intentionally focuses on reliability concepts. It does not implement congestion control, security, production flow control, connection multiplexing, or the many optimizations present in mature transport protocols.

## Why call it Selective Repeat-style rather than claiming full TCP-like reliability?

Selective Repeat describes the ARQ behavior used for the DATA phase. RDTX is a custom educational protocol with a simpler control model, so describing exactly what is implemented is more accurate than calling it TCP-like.

## What should be shown in the live demo?

1. Transfer demo.txt with no loss.
2. Repeat with trace mode and 20–25% simulated packet loss.
3. Point out a dropped sequence number, timeout and targeted retransmission.
4. Show TRANSFER COMPLETE and matching SHA-256.
5. Run the benchmark and open results/benchmark.csv if time permits.
