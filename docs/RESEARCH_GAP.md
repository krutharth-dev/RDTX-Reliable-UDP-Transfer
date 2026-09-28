# Research Gap and Project Positioning

## Project title

**RDTX VisualLab: Web-Based Reliable File Transfer and Selective Repeat Analysis over Unreliable UDP**

## The gap this project addresses

The project does **not** claim that Selective Repeat, UDP file transfer, packet analyzers, or network simulators are new. The gap is the way these ideas are combined for a compact Computer Networks learning and experimentation workflow.

### 1. Browser ARQ tools often visualize a model rather than execute a real UDP transfer

The open-source ARQ Simulator by Farhan Alam is an interactive web teaching tool for Stop-and-Wait, Go-Back-N and Selective Repeat, implemented in JavaScript with animated simulation controls and statistics.

Reference: https://github.com/FarhanAlam-Official/ARQ-Simulator

**Gap addressed by RDTX VisualLab:** the dashboard drives the project's existing Python UDP sockets. Packet loss, ACK loss, corruption, reordering, retransmission and final integrity belong to an actual localhost file transfer rather than only a browser state-machine animation.

### 2. Packet analyzers expose traffic in detail but are not a purpose-built ARQ experiment workflow

Wireshark is a general network packet analyzer designed to capture and inspect live or recorded traffic in detail. It is excellent for protocol analysis but does not provide a dedicated workflow for configuring a custom Selective Repeat sender, injecting controlled impairment, transferring a chosen file, and comparing experiment results in one screen.

References:
- https://www.wireshark.org/docs/man-pages/wireshark
- https://www.wireshark.org/docs/wsug_html/

**Gap addressed:** RDTX VisualLab presents protocol-specific events—window movement, DATA, ACK, drops, reordering, retransmissions and integrity—directly in the experiment UI.

### 3. General-purpose simulators/emulators are powerful but broader than the mini-project need

ns-3 is a discrete-event network simulator for internet systems, while Mininet creates virtual hosts, switches, controllers and links using real kernel/application code.

References:
- https://www.nsnam.org/documentation/
- https://mininet.org/

**Gap addressed:** RDTX VisualLab is intentionally narrow and lightweight: one application, one reliability problem, real localhost UDP sockets, reproducible impairment controls, and report-ready experiment history.

## Resulting contribution

RDTX VisualLab contributes an **integrated observability layer** over a real educational reliable-UDP implementation:

1. real file bytes travel through UDP sockets;
2. Selective Repeat sender-window behavior is visible live;
3. DATA/ACK loss, corruption, delay and reordering are configurable;
4. final integrity is checked byte-for-byte and with the RDTX SHA-256 path;
5. experiment configurations and outcomes are stored for comparison;
6. the same engine remains accessible through the CLI and automated tests.

This is a defensible mini-project contribution because it fills an educational tooling/observability gap without making an unsupported claim of protocol novelty.
