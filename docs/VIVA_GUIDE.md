# RDTX Viva Guide

## What problem does RDTX solve?

UDP does not guarantee reliable delivery, ordering, duplicate suppression or retransmission. RDTX adds those mechanisms at the application layer.

## Which ARQ technique is used?

Selective Repeat. New packets stay within `[base, base + window_size)`, individual packets are ACKed, out-of-order ACKs are remembered, and only timed-out missing packets are retransmitted.

## What if DATA 4 is lost but 5 and 6 arrive?

The receiver buffers and ACKs 5 and 6. The sender base cannot slide past 4. When 4 times out, only DATA 4 is retransmitted.

## What if an ACK is lost?

The sender retransmits that DATA after timeout. The receiver detects a duplicate, does not store it twice, and ACKs it again.

## How do you demonstrate out-of-order delivery?

Use `--reorder 1.0`. RDTX intentionally sends adjacent DATA pairs in reverse sequence order. The receiver reconstructs the file using sequence numbers rather than arrival order.

## Why CRC32 and SHA-256?

CRC32 detects corruption at the individual RDTX datagram level. SHA-256 verifies end-to-end integrity of the complete reconstructed file.

## Why UDP instead of TCP?

TCP would hide the reliability mechanisms the project is intended to demonstrate.

## Why is the timeout fixed?

A fixed timeout keeps the mini-project deterministic and explainable. Adaptive RTT/RTO estimation is a realistic future enhancement.

## Is RDTX the same as TCP?

No. RDTX demonstrates Selective Repeat reliability but does not implement TCP stream semantics, congestion control, adaptive timers, connection multiplexing or TCP's full state machine.

## Best live demo

Show a normal transfer, a lossy transfer, explicit reordering, and finally `results/benchmark.md`.
