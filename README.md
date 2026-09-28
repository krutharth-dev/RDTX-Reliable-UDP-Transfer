# RDTX — Reliable UDP Transfer

RDTX is a **reliable file-transfer protocol built on top of UDP** that demonstrates how transport-layer reliability can be created when the underlying channel may lose, corrupt, delay, duplicate, or reorder datagrams.

Instead of hiding reliability inside TCP, this project exposes the mechanisms directly: **sequence numbers, Selective Repeat acknowledgements, retransmission timers, CRC32 packet validation, out-of-order buffering, duplicate detection, and final SHA-256 verification**.

## Why this is a Computer Networks project

UDP provides datagrams but does not guarantee delivery, ordering, duplicate suppression, or recovery from corruption. RDTX adds those properties at the application layer so every reliability mechanism can be observed during a CN demonstration.

### Reliability features

- Sliding window with **Selective Repeat** behavior
- Per-packet sequence numbers and ACKs
- Per-packet timeout and retransmission
- CRC32 integrity checking on every RDTX datagram
- Receiver-side out-of-order buffering
- Duplicate packet detection and re-ACKing
- Reliable HELLO and FIN control exchanges
- SHA-256 verification of the reconstructed file
- Built-in packet loss, corruption, and delay simulation
- Transfer statistics for retransmissions, drops, throughput, duplicates, and checksum failures

## Architecture

```text
                    RDTX over UDP

 +------------------+                  +------------------+
 |      Sender      |                  |     Receiver     |
 |------------------|                  |------------------|
 | Read file        |                  | Validate packet  |
 | Split into chunks|                  | CRC32 check      |
 | Sliding window   |   UDP network    | Buffer by seq    |
 | Seq + CRC32      | ---------------> | ACK each packet  |
 | Timeout/retry    | <--------------- | Reassemble file  |
 | Track ACKs       |                  | SHA-256 verify    |
 +------------------+                  +------------------+
           |                                    |
           +------ Loss / corruption simulator--+
```

The detailed packet format and state machine are in [docs/PROTOCOL.md](docs/PROTOCOL.md).

## Requirements

- Python **3.10+**
- macOS, Linux, or Windows
- No third-party runtime dependencies

## Quick start on macOS

Clone the repository:

```bash
git clone https://github.com/krutharth-dev/RDTX-Reliable-UDP-Transfer.git
cd RDTX-Reliable-UDP-Transfer
```

### Terminal 1 — start the receiver

```bash
python3 -m rdtx.receiver --port 9000 --output-dir received
```

### Terminal 2 — send a file

```bash
python3 -m rdtx.sender demo.txt --host 127.0.0.1 --port 9000
```

The reconstructed file will appear as `received/demo.txt`.

## Demo packet loss

This is the best classroom demonstration. Start the receiver with simulated ACK loss:

```bash
python3 -m rdtx.receiver --port 9000 --ack-loss 0.15 --seed 20
```

Then send with 25% outgoing packet loss:

```bash
python3 -m rdtx.sender demo.txt --host 127.0.0.1 --loss 0.25 --seed 10
```

You should see retransmissions, while the final SHA-256 verification still succeeds and the received file remains identical.

You can also simulate corruption and delay:

```bash
python3 -m rdtx.sender demo.txt --corrupt 0.05 --delay-ms 80 --seed 42
```

## Useful sender options

```text
--chunk-size 1024   bytes carried in each DATA packet
--window 8          maximum unacknowledged packets in flight
--timeout 0.35      retransmission timeout in seconds
--max-retries 40    retry limit
--loss 0.20         outgoing packet loss probability
--corrupt 0.05      outgoing corruption probability
--delay-ms 50       random delay between 0 and this value
--seed 42           reproducible network simulation
```

Receiver equivalents are `--ack-loss`, `--ack-corrupt`, and `--ack-delay-ms`.

## Run the tests

```bash
python3 -m unittest discover -s tests -v
```

The test suite covers:

1. Packet encode/decode correctness
2. CRC32 corruption detection
3. Malformed packet rejection
4. End-to-end localhost file transfer
5. End-to-end transfer with deterministic packet and ACK loss

## Optional command installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Then you can use:

```bash
rdtx-receive --port 9000
rdtx-send demo.txt --host 127.0.0.1
```

## Packet flow

```text
1. HELLO      -> filename, size, chunk count, SHA-256
2. HELLO_ACK  <- receiver accepts the session
3. DATA(n)    -> chunk with sequence number n
4. ACK(n)     <- independent acknowledgement for n
5. timeout    -> only missing/unacknowledged packets are retransmitted
6. FIN        -> sender declares transfer complete
7. FIN_ACK    <- receiver confirms final integrity check
```

## Project structure

```text
RDTX-Reliable-UDP-Transfer/
├── rdtx/
│   ├── protocol.py      # packet header, CRC32, packet types
│   ├── simulator.py     # loss/corruption/delay simulation
│   ├── sender.py        # Selective Repeat sender
│   └── receiver.py      # buffering, ACKs, reassembly, verification
├── tests/
│   ├── test_protocol.py
│   └── test_integration.py
├── docs/
│   └── PROTOCOL.md
├── .github/workflows/
│   └── tests.yml
├── demo.txt
├── pyproject.toml
└── README.md
```

## Scope and limitations

RDTX is intentionally an **educational protocol**. It demonstrates reliability but does not try to replace TCP or QUIC. It does not provide congestion control, encryption/authentication, NAT traversal, or production-grade flow control.

That limited scope is useful for a CN mini-project because each reliability mechanism is small enough to inspect, modify, explain, and demonstrate live.

## License

MIT
