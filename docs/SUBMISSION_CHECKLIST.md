# Mini-Project Submission Checklist

Use this before the final demonstration or repository submission.

## Repository

- [ ] Latest `main` branch is pulled on the demo laptop.
- [ ] GitHub Actions badge is green.
- [ ] `python3 -m rdtx --version` reports the expected release.
- [ ] `make test` finishes with `OK`.
- [ ] `make benchmark` creates `results/benchmark.csv`.

## Report

- [ ] Title and problem statement match the implemented project.
- [ ] Architecture and packet-flow diagrams are included.
- [ ] Selective Repeat is described using the sender base/window rule.
- [ ] Packet header fields are documented.
- [ ] Test methodology is included.
- [ ] Benchmark results are generated on the actual project laptop.
- [ ] Limitations and future scope are stated.
- [ ] No fabricated benchmark values are used.

## Demo

- [ ] Normal transfer works.
- [ ] Loss demo works using fixed seeds.
- [ ] Trace mode visibly shows ACKs, retransmissions and window movement.
- [ ] Received file SHA-256 verification succeeds.
- [ ] A backup port such as 9100 is ready if port 9000 is occupied.

## Viva

Be ready to explain:

- why UDP was chosen;
- Selective Repeat vs Stop-and-Wait vs Go-Back-N;
- the role of sequence numbers and ACKs;
- why a lost ACK causes a harmless duplicate;
- CRC32 vs SHA-256;
- retransmission timeout behavior;
- how the sender window base advances;
- current limitations and realistic future enhancements.
