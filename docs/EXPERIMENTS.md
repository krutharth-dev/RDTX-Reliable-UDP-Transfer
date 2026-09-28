# RDTX Experiments and Results Guide

A networking mini-project is stronger when reliability is demonstrated with measurements rather than only source code. RDTX therefore includes repeatable impairment simulation and statistics export.

## Automated benchmark

Run:

~~~bash
python3 experiments/benchmark.py
~~~

or:

~~~bash
make benchmark
~~~

The benchmark transfers a deterministic 64 KiB file across localhost under multiple conditions and writes:

~~~text
results/benchmark.csv
~~~

The scenarios include a baseline, 10% DATA loss, combined DATA/ACK loss, and 5% corruption. Every scenario verifies the reconstructed file byte-for-byte.

## Manual experiment matrix

| Experiment | DATA loss | ACK loss | Corruption | Window | What to observe |
|---|---:|---:|---:|---:|---|
| Baseline | 0% | 0% | 0% | 8 | Near-zero retransmissions |
| Moderate loss | 10% | 0% | 0% | 8 | Retransmissions increase |
| Bidirectional loss | 20% | 10% | 0% | 8 | DATA and ACK recovery |
| Corruption | 0% | 0% | 5% | 8 | CRC failures followed by recovery |
| Stop-and-Wait-like | 0% | 0% | 0% | 1 | Lower pipeline concurrency |
| Wider window | 0% | 0% | 0% | 16 | More outstanding packets |

## Exporting a single run

Receiver:

~~~bash
python3 -m rdtx receive --stats-json results/receiver.json
~~~

Sender:

~~~bash
python3 -m rdtx send demo.txt --loss 0.20 --seed 10 --stats-json results/sender.json
~~~

The JSON captures configuration and measured counters. Keep the seed fixed when comparing parameter changes so the experiment is reproducible.

## Suggested result columns

- Loss probability
- Window size
- File size
- Elapsed transfer time
- Throughput
- Retransmissions
- Simulated drops
- Corruption events
- Duplicate packets
- Receiver checksum errors
- Final integrity status

## Interpretation

Expected trends should be stated as observations, not guaranteed numeric values:

- Higher loss normally produces more retransmissions and lower useful throughput.
- Lost ACKs can create duplicates because the sender retransmits a packet that the receiver already stored.
- Corruption is detected by CRC32 and recovered through retransmission.
- A larger window permits more pipelining, though localhost measurements can be dominated by CPU and timer overhead.
- SHA-256 should continue to pass in successful transfers regardless of impairment level.

Do not copy benchmark values from another machine into the report. Generate results on the laptop used for the project demo and include those measured values.
