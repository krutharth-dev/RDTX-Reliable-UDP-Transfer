# RDTX Demonstration Guide

This guide is designed for a short Computer Networks mini-project evaluation.

## Before the demo

From the repository root:

~~~bash
python3 --version
python3 -m unittest discover -s tests -v
~~~

The test suite should finish with OK.

Use two terminal windows and keep both terminals visible if possible.

## Demo 1 — Normal reliable transfer

### Terminal 1

~~~bash
python3 -m rdtx receive --port 9000 --output-dir received
~~~

### Terminal 2

~~~bash
python3 -m rdtx send demo.txt --host 127.0.0.1 --port 9000
~~~

Point out:

- HELLO/HELLO_ACK establishes the transfer.
- The sender reports the file size, chunk count and window.
- The receiver writes received/demo.txt.
- SHA-256 is printed after successful reconstruction.

## Demo 2 — Reliability under packet loss

Restart the receiver.

### Terminal 1

~~~bash
python3 -m rdtx receive --port 9000 --ack-loss 0.10 --seed 20 --trace
~~~

### Terminal 2

~~~bash
python3 -m rdtx send demo.txt --host 127.0.0.1 --loss 0.25 --seed 10 --trace
~~~

Point out trace lines showing:

1. DATA packets with sequence numbers.
2. Simulated drops.
3. ACKs arriving independently.
4. A timeout causing a targeted retransmission.
5. Duplicate handling if an ACK was lost.
6. Successful SHA-256 verification at the end.

The important observation is that loss changes the number of transmissions, not the final file contents.

## Demo 3 — Corruption detection

### Terminal 1

~~~bash
python3 -m rdtx receive --port 9000 --trace
~~~

### Terminal 2

~~~bash
python3 -m rdtx send demo.txt --corrupt 0.10 --seed 42 --trace
~~~

Explain that the sender intentionally damages some outgoing datagrams. The receiver's CRC32 validation rejects corrupted packets, so missing ACKs cause retransmission.

## Demo 4 — Generate experiment data

~~~bash
python3 -m experiments.benchmark
~~~

Then inspect:

~~~text
results/benchmark.csv
~~~

Explain the columns: loss/corruption settings, elapsed time, throughput, retransmissions, drops, duplicates, checksum errors and final integrity status.

## Suggested two-minute explanation

> RDTX uses UDP as the base transport so reliability is not provided automatically. The sender divides a file into numbered chunks and uses a Selective Repeat window, allowing several packets to be outstanding. The receiver validates each datagram using CRC32, buffers valid chunks by sequence number, and acknowledges them independently. If an ACK does not arrive before timeout, only that packet is retransmitted. After every chunk is acknowledged, the receiver reconstructs the file and verifies its SHA-256 digest before confirming completion.

## Common demo problems

### Address already in use

Another receiver may still be running. Stop it with Ctrl+C or choose another port in both terminals:

~~~bash
python3 -m rdtx receive --port 9100
python3 -m rdtx send demo.txt --port 9100
~~~

### Sender keeps retrying HELLO

The receiver is not running, the ports do not match, or a firewall is blocking UDP.

### Very high loss causes timeout

For a predictable classroom demo, use the documented fixed seeds and 10–25% loss. Extreme loss probabilities can intentionally exceed the retry limit.

### received/demo.txt already exists

RDTX overwrites the existing output file after the new transfer passes integrity verification. Delete the received directory before the demo if you want a clean view.

## Best evaluation order

1. Explain the problem.
2. Show the architecture.
3. Run the no-loss transfer.
4. Run the lossy trace.
5. Point to the protocol source briefly.
6. Show the benchmark CSV.
7. Finish with limitations and future scope.

This sequence demonstrates both implementation and understanding without spending the entire evaluation reading code.
