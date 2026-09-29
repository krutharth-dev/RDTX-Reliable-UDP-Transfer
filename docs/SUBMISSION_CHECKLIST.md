# Mini-Project Submission Checklist

Use this against the exact laptop and repository state that will be used during evaluation.

## Repository readiness

- [ ] `git status` is clean.
- [ ] `git pull origin main` reports that the local branch is current.
- [ ] `python3 -m rdtx --version` reports **RDTX 2.2.1**.
- [ ] Latest GitHub Actions run on `main` is green.
- [ ] `make demo-check` ends with **RDTX demo readiness: PASS**.
- [ ] No generated `visual_lab_data/`, `results/`, or received files are accidentally committed.

## Local web demo

- [ ] `rdtx-web` starts successfully.
- [ ] Dashboard loads at `http://127.0.0.1:5000`.
- [ ] Baseline transfer finishes with integrity PASS.
- [ ] 20% DATA loss + 10% ACK loss produces visible recovery activity.
- [ ] 100% reordering still completes successfully.
- [ ] Run JSON/report downloads work.
- [ ] Matrix Lab completes at least one sweep.

## Two-host LAN demo

- [ ] Both laptops have the same current project version.
- [ ] Both laptops are on the same LAN/Wi-Fi.
- [ ] Receiver laptop's IPv4 address is known.
- [ ] Receiver starts with `--host 0.0.0.0` and the selected UDP port.
- [ ] Firewall permission has been tested before evaluation.
- [ ] A small file has been transferred successfully between the two laptops.
- [ ] A localhost fallback demo is ready in case the classroom network blocks peer traffic.

## Report

- [ ] Problem statement explains why reliability must be added above UDP.
- [ ] Packet header and control/data packet types are documented.
- [ ] Strict Selective Repeat window semantics are explained.
- [ ] CRC32 and SHA-256 are distinguished correctly.
- [ ] Research-gap wording claims integration/observability, not protocol invention.
- [ ] Results are measured on the actual machine/network.
- [ ] Matrix comparisons keep file and random seed fixed.
- [ ] Limitations and future scope are included.

## Viva

Be ready to explain:

- UDP vs TCP;
- Stop-and-Wait vs Go-Back-N vs Selective Repeat;
- sender base and window movement;
- DATA loss vs ACK loss;
- duplicates and out-of-order buffering;
- timeout/retransmission behavior;
- CRC32 vs SHA-256;
- localhost vs LAN mode;
- why matrix experiments run sequentially;
- what the project does **not** claim.
