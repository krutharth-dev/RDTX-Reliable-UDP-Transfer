# Research Gap and Project Positioning

## Project title

**RDTX VisualLab: Web-Based Reliable File Transfer and Selective Repeat Analysis over Unreliable UDP**

## Scope of the claim

RDTX VisualLab does **not** claim that Selective Repeat, UDP file transfer, packet capture, or network simulation are new inventions.

The project's contribution is an integrated educational/experimental workflow in which a real reliable-UDP implementation can be controlled, observed, impaired, compared, and documented from one lightweight application.

## Existing tool categories

### Browser ARQ simulators

Interactive ARQ teaching tools can animate Stop-and-Wait, Go-Back-N, and Selective Repeat behavior in the browser.

Reference:
- https://github.com/FarhanAlam-Official/ARQ-Simulator

RDTX VisualLab differs by using the browser only as the control/observability layer; actual file bytes are exchanged through Python UDP sockets.

### Packet analyzers

Wireshark is a general-purpose packet analyzer for capturing and inspecting live or recorded network traffic.

References:
- https://www.wireshark.org/docs/man-pages/wireshark
- https://www.wireshark.org/docs/wsug_html/

Wireshark provides much deeper packet inspection, while VisualLab provides a purpose-built experiment workflow for this custom protocol: impairment controls, sender-window telemetry, protocol-specific events, result persistence, and report generation.

### General network simulators/emulators

ns-3 is a discrete-event network simulator. Mininet provides virtual hosts, switches, controllers, and links.

References:
- https://www.nsnam.org/documentation/
- https://mininet.org/

These tools solve broader networking problems. RDTX VisualLab intentionally stays narrow enough to run, inspect, and explain on one or two ordinary laptops.

## Gap addressed by RDTX VisualLab

The project integrates:

1. real file bytes sent through UDP sockets;
2. strict Selective Repeat sender-window behavior;
3. controllable DATA/ACK loss, corruption, delay, and DATA reordering;
4. live protocol-specific telemetry;
5. local and two-host LAN execution;
6. final integrity verification;
7. persisted experiment history;
8. repeatable parameter-sweep matrices;
9. JSON/CSV/Markdown evidence generation.

The research/engineering gap is therefore **observability and experiment integration around a real educational reliable-UDP implementation**, not ARQ algorithm novelty.

## Why the LAN and matrix features matter

LAN mode shows that the protocol is not dependent on a sender and receiver sharing one process or one host.

Matrix Lab provides a controlled way to vary one selected parameter while keeping the file, seed, and other configuration constant. This supports evidence-based discussion of measured behavior without claiming that one local experiment establishes a universal performance law.

## Positioning statement for the report

A safe concise statement is:

> RDTX VisualLab integrates real Selective Repeat file transfer over UDP with controlled impairment, live protocol observability, two-host execution, reproducible parameter sweeps, and report-ready experiment evidence in a lightweight local application.

This wording is specific to what the repository actually implements and avoids unsupported claims of protocol novelty.
