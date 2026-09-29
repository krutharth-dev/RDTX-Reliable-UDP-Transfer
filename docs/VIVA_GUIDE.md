# RDTX VisualLab Viva Guide

## What is the actual CN topic?

Reliable data transfer over unreliable UDP using Selective Repeat ARQ.

## Is the website the networking mechanism?

No. Flask and the browser are the experiment-control/visualization layer. File bytes are transferred by the Python RDTX sender and receiver through UDP sockets.

## Why UDP?

UDP does not provide the delivery, retransmission, ordering, or duplicate-handling guarantees that the project is intended to implement explicitly.

## What is the strict sender-window rule?

New DATA can enter only in:

~~~text
[base, base + window_size)
~~~

ACKs may arrive out of order, but the sender base advances only across a contiguous acknowledged prefix.

## What if DATA 4 is lost but DATA 5 and 6 arrive?

The receiver can buffer and ACK 5 and 6. The sender cannot slide its base past 4. When 4 times out, only the missing unacknowledged packet is retransmitted.

## What if an ACK is lost?

The sender may retransmit a packet the receiver already has. The receiver recognizes the duplicate, does not store it twice, and ACKs the sequence again.

## Why CRC32 and SHA-256?

CRC32 checks integrity of individual RDTX datagrams. SHA-256 verifies the final reconstructed file end-to-end.

## Is LAN mode a different protocol?

No. The same packet format and Selective Repeat behavior are used. Only the destination changes from a localhost receiver to a receiver on another host.

## How can the sender claim LAN integrity without reading the remote file?

Normal completion requires FIN_ACK. The receiver sends FIN_ACK only after validating expected chunks, final byte count, and SHA-256.

## Why run Matrix Lab sequentially?

Sequential execution avoids multiple experiments competing for local resources. It improves comparability while keeping the file, seed, and non-swept parameters unchanged.

## What is the research gap?

The project does not claim a new ARQ algorithm. Its contribution is integrating real reliable-UDP execution with controlled impairment, protocol-specific live observability, LAN operation, reproducible sweeps, and report-ready evidence in one lightweight tool.

## Is it a replacement for TCP?

No. RDTX does not implement TCP stream semantics, congestion control, adaptive RTO, authentication, encryption, or TCP's full state machine.

## Biggest limitations?

Fixed RTO, IPv4, full-file buffering, one receiver session per process, no congestion control, and no secure transport.

## Why is localhost still meaningful?

Localhost still uses real UDP sockets and the same RDTX wire protocol. It is a reliable fallback when classroom networks block peer-to-peer LAN traffic.
