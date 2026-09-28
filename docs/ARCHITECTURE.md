# RDTX System Architecture

RDTX separates command handling, reliability logic, packet encoding, impairment simulation and UDP transport.

~~~text
CLI
 |
 v
File -> Chunker -> SelectiveRepeatWindow -> Packet/CRC32 -> UDP
                         |                         |
                         |              loss/corruption/delay
                         |                explicit reordering
                         v                         v
                    ACK tracking <----------- Receiver
                                              |
                                   sequence buffer -> SHA-256 -> File
~~~

## Main modules

| Module | Responsibility |
|---|---|
| `rdtx/cli.py` | Unified send/receive/benchmark command surface and clean error handling |
| `rdtx/window.py` | Strict Selective Repeat sender-window state |
| `rdtx/sender.py` | Chunking, transmission, ACK handling, retransmission and explicit reordering |
| `rdtx/receiver.py` | Metadata validation, buffering, duplicate handling, reassembly and final verification |
| `rdtx/protocol.py` | Binary header, packet types and CRC32 |
| `rdtx/simulator.py` | Loss, corruption and delay |
| `rdtx/reporting.py` | Structured JSON transfer statistics |
| `experiments/benchmark.py` | Reproducible scenarios and CSV/Markdown result generation |

Explicit reordering is applied only to DATA packets by transmitting adjacent pairs in reverse order, so control handshakes cannot be accidentally held or deadlocked.
