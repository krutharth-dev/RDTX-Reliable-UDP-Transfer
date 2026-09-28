# RDTX VisualLab Demonstration Guide

## Before evaluation

~~~bash
git pull origin main
source .venv/bin/activate
python3 -m pip install -e .
make test
~~~

Start the dashboard:

~~~bash
rdtx-web
~~~

Open:

~~~text
http://127.0.0.1:5000
~~~

## Demo 1 — Baseline

Upload `demo.txt`.

Use:

- Window: 8
- DATA loss: 0%
- ACK loss: 0%
- Corruption: 0%
- Reordering: 0%

Start the experiment and point out DATA/ACK events, sender-window movement and PASS integrity.

## Demo 2 — Loss recovery

Use:

- DATA loss: 20%
- ACK loss: 10%
- Seed: 2026

Point out dropped packets, timeout-triggered retransmissions and duplicates caused by lost ACKs.

## Demo 3 — Out-of-order delivery

Set reordering to 100%.

Point out sender REORDER events and show that integrity still finishes as PASS because the receiver buffers by sequence number.

## Demo 4 — Corruption

Set corruption to 10%.

Explain that corrupted RDTX datagrams fail CRC32 validation and are recovered because missing ACKs cause retransmission.

## Demo 5 — Window behavior

Repeat the same file with window 1, 4, 8 and 16. Explain the difference between Stop-and-Wait-like behavior and pipelined Selective Repeat.

## What to say in two minutes

> RDTX VisualLab does not simulate the transport in JavaScript. The browser configures a real Python UDP sender and receiver. The sender implements Selective Repeat with a strict sliding window and individual packet timers. The receiver validates CRC32, buffers out-of-order chunks and acknowledges each valid sequence number. The dashboard streams those real protocol events live and stores experiment results for comparison. Final SHA-256 verification proves that the received file is identical.

## If something goes wrong

- If port 5000 is occupied: `rdtx-web --port 5050`.
- If dependencies are missing: `python3 -m pip install -e .`.
- If the browser does not open automatically, manually open the printed localhost URL.
