# Demo Guide

## 1. Local baseline

Start rdtx-web, upload demo.txt, choose Baseline, and show window movement plus PASS integrity.

## 2. Loss recovery

Use 20 percent DATA loss plus 10 percent ACK loss. Filter the timeline to Drop and Retry.

## 3. Reordering

Use 100 percent reordering and show out-of-order DATA while final integrity remains PASS.

## 4. Two-host LAN

On Laptop B:

~~~bash
rdtx receive --host 0.0.0.0 --port 9000 --output-dir received --trace
~~~

On Laptop A choose LAN mode, enter Laptop B's IP, and transfer the file. Show that the remote terminal receives the file and VisualLab completes only after verified FIN_ACK.

## 5. Matrix Lab

Sweep window size with 1,4,8,16. Show the generated table and download the matrix report.

## 6. Evidence

Download a run report, JSON export, history CSV, and, for local mode, the reconstructed received file.
