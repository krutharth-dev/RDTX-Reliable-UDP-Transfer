# RDTX VisualLab Viva Guide

## Is this a website project or a Computer Networks project?

It is a Computer Networks project with a web visualization layer. The actual file transfer uses Python UDP sockets. Flask only configures the experiment and streams protocol events to the browser.

## Why UDP?

UDP does not provide retransmission, ordering or duplicate suppression. That makes the reliability mechanisms explicit and demonstrable.

## Which ARQ protocol is used?

Selective Repeat. The sender keeps multiple packets in flight, ACKs are per sequence number, the receiver buffers valid out-of-order packets, and only timed-out packets are retransmitted.

## What is the exact sender-window rule?

New sequence numbers can enter only inside `[base, base + window_size)`. Out-of-order ACKs are remembered, but the base cannot advance past a missing lower sequence number.

## What happens if packet 4 is lost and 5/6 arrive?

The receiver stores and ACKs 5 and 6. The sender still waits for 4. When 4 times out, only 4 is retransmitted.

## What happens if an ACK is lost?

The sender times out and retransmits that DATA. The receiver recognizes the duplicate, does not store it twice, and sends the ACK again.

## Why CRC32 and SHA-256?

CRC32 checks each RDTX datagram for corruption. SHA-256 verifies the final reconstructed file end-to-end.

## How is reordering demonstrated?

The sender can intentionally send adjacent DATA pairs in reverse order. This produces real out-of-order UDP sends while preserving the same packet format.

## What does the web app add technically?

It adds experiment configuration, live Server-Sent Events, Selective Repeat visualization, metrics and SQLite history while reusing the real protocol engine.

## What research gap are you claiming?

Not protocol novelty. The claimed gap is integrated educational observability: real UDP transfer, controlled impairment, live ARQ-specific visualization and stored experiments in one lightweight local tool.

## Why not just use Wireshark?

Wireshark is excellent for packet analysis, but it is a general analyzer. VisualLab provides controls and interpretations specific to this protocol experiment. Wireshark can be complementary.

## Why not ns-3 or Mininet?

They are broader simulation/emulation environments. This project intentionally provides a narrow, easy-to-demo environment for one transport reliability problem.

## Limitations?

Single-machine experiments by default, fixed retransmission timeout, full-file buffering, IPv4, no congestion control, and no encryption/authentication.
