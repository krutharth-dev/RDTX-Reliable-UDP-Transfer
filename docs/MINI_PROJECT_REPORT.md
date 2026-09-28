# RDTX VisualLab: Web-Based Reliable File Transfer and Selective Repeat Analysis over Unreliable UDP

## Abstract

RDTX VisualLab implements reliable file transfer over UDP using Selective Repeat ARQ and exposes the protocol through a web experimentation interface. The protocol uses sequence numbers, individual ACKs, a strict sender window, per-packet retransmission timers, CRC32 validation, out-of-order buffering, duplicate handling, and SHA-256 final verification. VisualLab adds controlled impairment, live telemetry, two-host LAN transfer, automatic parameter sweeps, and report generation while preserving real UDP execution as the core.

## Problem statement

UDP does not guarantee delivery, ordering, duplicate suppression, or retransmission. RDTX implements those mechanisms explicitly. VisualLab addresses a second educational problem: making the real protocol observable and experimentally comparable without replacing it with a browser-only simulation.

## Key contributions

1. Real file transfer over UDP with strict Selective Repeat semantics.
2. Browser visualization of real sender and receiver events.
3. Repeatable DATA and ACK loss, corruption, delay, and reordering controls.
4. Two-host LAN transfer between real machines.
5. Matrix experiments for controlled parameter sweeps.
6. Per-run and matrix report generation from measured data.
7. SQLite history, JSON and CSV exports, and reconstructed-file download.

## LAN experiment

In LAN mode, VisualLab sends to an RDTX receiver running on another laptop. The remote receiver only returns FIN_ACK after file-size and SHA-256 validation, providing protocol-level confirmation of final integrity.

## Matrix methodology

Matrix runs execute sequentially while keeping the file, random seed, and non-swept parameters constant. This reduces confounding from concurrent local experiments. Results are interpreted as measurements from that machine and run, not universal performance rankings.

## Limitations

The web server remains a local educational application. LAN mode requires manual receiver startup and appropriate firewall permissions. The protocol uses a fixed RTO, buffers the complete file, uses IPv4, and does not implement congestion control, authentication, or encryption.

## Future scope

Remote receiver telemetry, adaptive RTT and RTO estimation, large-file streaming, IPv6, optional PCAP export, and protocol comparison modes.
