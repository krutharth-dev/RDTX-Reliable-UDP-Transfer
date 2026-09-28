# RDTX VisualLab: Web-Based Reliable File Transfer and Selective Repeat Analysis over Unreliable UDP

## Abstract

RDTX VisualLab is a Computer Networks mini-project that implements reliable file transfer over UDP and exposes the protocol through a local web dashboard. The networking core uses Selective Repeat ARQ with sequence numbers, individual acknowledgements, a strict sender window, timeout-based retransmission, CRC32 datagram validation, out-of-order buffering, duplicate handling and SHA-256 end-to-end integrity verification. The VisualLab layer allows a user to upload a file, inject controlled DATA/ACK loss, corruption, delay and packet reordering, and observe live protocol events and performance metrics while the transfer executes through real localhost UDP sockets.

## 1. Problem Statement

UDP provides connectionless datagram transport without delivery, ordering or retransmission guarantees. Reliable transfer therefore requires additional logic for sequencing, acknowledgement, recovery and integrity.

A second practical problem is observability: students can study Selective Repeat theoretically, simulate it visually, or inspect packets with general-purpose tools, but these workflows are often separated. The project addresses this by connecting a real reliable-UDP implementation to an experiment dashboard.

## 2. Research Gap Addressed

The project does not claim a new transport protocol. Its contribution is an integrated educational workflow.

- Browser ARQ tools commonly visualize protocol logic as a simulation.
- Wireshark analyzes captured traffic in detail but is not a dedicated Selective Repeat experiment controller.
- ns-3 and Mininet are powerful general-purpose simulation/emulation environments but broader than the needs of a compact mini-project.

RDTX VisualLab combines **real UDP execution + controlled impairment + live protocol-specific visualization + experiment history** in one local application.

Detailed positioning and references are in [RESEARCH_GAP.md](RESEARCH_GAP.md).

## 3. Objectives

1. Implement reliable file transfer over UDP.
2. Implement strict Selective Repeat sender-window semantics.
3. Recover from DATA and ACK loss through individual retransmission.
4. Detect damaged RDTX datagrams with CRC32.
5. Buffer out-of-order DATA and suppress duplicate writes.
6. Verify the completed file end-to-end using SHA-256.
7. Provide repeatable loss, corruption, delay and reordering controls.
8. Visualize real transfer events through a browser dashboard.
9. Store experiment configurations and results for comparison.
10. Keep the protocol accessible through automated tests and the CLI.

## 4. System Architecture

~~~text
Browser
  |
  | HTTP / Server-Sent Events
  v
Flask VisualLab
  |
  | starts/observes
  v
RDTX Sender ------ real localhost UDP ------> RDTX Receiver
  |                                             |
Selective Repeat                            seq buffer
timeouts/retries                            CRC32 validation
  |                                             |
  +------------ live protocol events -----------+
                                                |
                                            SHA-256
                                                |
                                           output file
~~~

The web interface is not the transport mechanism. It configures and observes the existing UDP sender/receiver.

## 5. Protocol Operation

### Session establishment

The sender transmits HELLO metadata containing filename, file size, chunk size, chunk count, sender window and SHA-256. The receiver validates the metadata and replies with HELLO_ACK.

### DATA transfer

The sender permits new sequence numbers only inside:

~~~text
[base, base + window_size)
~~~

ACKs can arrive out of order. The base advances only across a contiguous acknowledged prefix. Each outstanding packet maintains its own timeout; expiration retransmits only that sequence number.

### Receiver behavior

The receiver validates CRC32, session ID, peer address, sequence range and chunk length. Valid out-of-order chunks are buffered by sequence number. Duplicate packets are ACKed again but not written twice.

### Completion

After all DATA packets are acknowledged, FIN/FIN_ACK completes the session. The receiver reconstructs the file and verifies byte count and SHA-256 before accepting the transfer.

## 6. VisualLab Operation

A user uploads a file and chooses:

- Selective Repeat window size
- chunk size
- retransmission timeout
- DATA loss
- ACK loss
- corruption
- delay
- explicit reordering
- deterministic random seed

The backend launches a receiver and sender using real UDP sockets on localhost. Sender/receiver trace events are converted into Server-Sent Events and streamed to the browser. Recent runs are stored in SQLite.

## 7. Implementation Technologies

| Component | Technology |
|---|---|
| Reliable transfer engine | Python sockets |
| Web backend | Flask |
| Live event stream | Server-Sent Events |
| Front end | HTML, CSS, vanilla JavaScript |
| Experiment persistence | SQLite |
| Integrity | CRC32 + SHA-256 |
| Testing | Python unittest |
| CI | GitHub Actions |

## 8. Experiments

Recommended demonstrations:

1. baseline transfer;
2. 20% DATA loss;
3. combined DATA + ACK loss;
4. corruption;
5. 100% adjacent-pair reordering;
6. window-size comparison.

Metrics include elapsed time, throughput, retransmissions, drops, corruption count, reordered pairs, duplicates and integrity.

## 9. Testing

The repository tests:

- packet encode/decode;
- CRC corruption detection;
- malformed packet rejection;
- Selective Repeat window movement;
- duplicate/out-of-window ACK handling;
- peer endpoint validation;
- empty-file transfer;
- deterministic loss recovery;
- explicit reordering;
- CLI behavior;
- statistics/benchmark output;
- VisualLab page loading;
- an end-to-end UDP experiment started through the web backend.

## 10. Advantages

- Keeps the networking mechanisms visible rather than hiding them behind TCP.
- Demonstrates actual file transfer, not only protocol animation.
- Makes Selective Repeat window movement easy to explain.
- Supports repeatable impairment using fixed seeds.
- Requires only a laptop for demonstration.
- Produces comparable experiment history.

## 11. Limitations

- The dashboard currently runs sender and receiver on the same machine.
- One receiver is created per experiment.
- The receiver buffers the full transfer in memory.
- Retransmission timeout is fixed rather than RTT-adaptive.
- The protocol does not implement congestion control, encryption or authentication.
- The current transport implementation uses IPv4.

## 12. Future Scope

- Run sender and receiver on separate LAN machines from the dashboard.
- Add adaptive RTT/RTO estimation.
- Add streaming for large files.
- Add Go-Back-N and Stop-and-Wait comparison modes using the same UI.
- Add optional PCAP export/Wireshark integration.
- Add graphical throughput and retransmission charts.
- Add authenticated encryption for secure experiments.

## 13. Conclusion

RDTX VisualLab demonstrates how reliability can be constructed over UDP using sequence numbers, acknowledgements, sliding windows, timers, retransmission, buffering and integrity checks. Its main contribution is making a real Selective Repeat transfer observable and experimentally controllable through one web interface while preserving the protocol implementation as the core of the project.
