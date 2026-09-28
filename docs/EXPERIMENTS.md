# RDTX Experiments and Results Guide

Run the reproducible benchmark with:

~~~bash
python3 -m rdtx benchmark
~~~

It generates `results/benchmark.csv` and a report-ready `results/benchmark.md`.

| Scenario | DATA loss | ACK loss | Corruption | Reorder | Purpose |
|---|---:|---:|---:|---:|---|
| Baseline | 0% | 0% | 0% | 0% | Normal transfer |
| DATA loss | 10% | 0% | 0% | 0% | Retransmission recovery |
| DATA + ACK loss | 20% | 10% | 0% | 0% | Duplicate handling |
| Corruption | 0% | 0% | 5% | 0% | CRC32 recovery |
| Reordering | 0% | 0% | 0% | 100% | Out-of-order buffering |

The reordering scenario deliberately transmits adjacent DATA pairs in reverse sequence order. It is an explicit demonstration mechanism; it does not claim the localhost UDP stack itself reordered packets.

Useful manual experiments:

~~~bash
python3 -m rdtx send demo.txt --window 1
python3 -m rdtx send demo.txt --window 16
python3 -m rdtx send demo.txt --reorder 1.0 --trace
python3 -m rdtx send demo.txt --loss 0.10 --corrupt 0.03 --reorder 0.5 --seed 42
~~~

Successful runs must preserve byte-for-byte file equality and final SHA-256 integrity. Generate final report numbers on the actual demonstration laptop.
