# RDTX Demonstration Guide

## 1. Normal transfer

~~~bash
python3 -m rdtx receive
python3 -m rdtx send demo.txt
~~~

## 2. Loss and retransmission

~~~bash
python3 -m rdtx receive --ack-loss 0.10 --seed 20 --trace
python3 -m rdtx send demo.txt --loss 0.25 --seed 10 --trace
~~~

Point out sequence numbers, independent ACKs, window-base movement, drops and targeted retransmissions.

## 3. Explicit packet reordering

~~~bash
python3 -m rdtx receive --trace
python3 -m rdtx send demo.txt --reorder 1.0 --seed 10 --trace
~~~

Look for `REORDER pair`. Explain that DATA pairs are intentionally sent in reverse order while the receiver buffers by sequence number.

## 4. Corruption recovery

~~~bash
python3 -m rdtx send demo.txt --corrupt 0.10 --seed 42 --trace
~~~

CRC32 rejects damaged RDTX datagrams; missing ACKs trigger recovery.

## 5. Results

~~~bash
python3 -m rdtx benchmark
~~~

Open `results/benchmark.md` and explain the measured scenarios.

Use the unified `python3 -m rdtx ...` commands during evaluation because expected runtime failures are shown as concise errors rather than Python tracebacks.
