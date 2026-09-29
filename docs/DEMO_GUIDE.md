# RDTX VisualLab Demo Guide

## Before entering the evaluation

Run:

~~~bash
git pull origin main
source .venv/bin/activate
python3 -m pip install -e .
make demo-check
~~~

Then start:

~~~bash
rdtx-web
~~~

Keep [Troubleshooting](TROUBLESHOOTING.md) available.

## 1. Establish the core idea

Start with a baseline local transfer.

Explain:

> UDP itself does not recover lost or out-of-order data. RDTX implements Selective Repeat above UDP. The browser is observing the actual protocol rather than simulating the transport.

Show window movement and final integrity PASS.

## 2. Demonstrate reliability

Use:

~~~text
DATA loss: 20%
ACK loss: 10%
Window: 8
Seed: 2026
~~~

Filter the timeline to **Drop** and **Retry**.

Explain the difference between:

- a DATA packet being lost;
- an ACK being lost;
- the receiver seeing a duplicate after retransmission.

## 3. Demonstrate ordering independence

Set reordering to 100%.

Show REORDER events and explain that the receiver stores chunks by sequence number rather than arrival order.

## 4. Demonstrate two-host operation

On Laptop B:

~~~bash
rdtx receive --host 0.0.0.0 --port 9000 --output-dir received --trace
~~~

On Laptop A choose **LAN / two-host**, enter Laptop B's LAN IPv4 address, and transfer a small file.

Point out that successful FIN_ACK means the remote receiver completed final size and SHA-256 checks.

If the classroom network isolates devices, immediately switch to Local lab rather than debugging the network during the evaluation.

## 5. Demonstrate experimental analysis

Run Matrix Lab:

~~~text
Sweep: Window size
Values: 1,4,8,16
~~~

Download the matrix report.

Explain that rows are sequential and keep the file/seed/base configuration fixed.

## 6. Show evidence

Finish by showing:

- generated run report;
- JSON export;
- CSV history;
- reconstructed local file;
- Matrix report;
- green GitHub Actions status.

## Suggested closing statement

> RDTX VisualLab demonstrates reliable file transfer over unreliable UDP using Selective Repeat, then makes the protocol observable and experimentally reproducible through local/LAN execution, controlled impairment, live telemetry, and reportable measurements.
