# Mini-Project Submission Checklist

## Repository

- [ ] Pull latest `main`.
- [ ] CI badge is green.
- [ ] `python3 -m rdtx --version` reports RDTX 1.3.0.
- [ ] `make test` returns OK.
- [ ] `python3 -m rdtx benchmark` creates CSV and Markdown results.

## Report

- [ ] Explain strict Selective Repeat window semantics.
- [ ] Include packet header and architecture.
- [ ] Include loss, ACK-loss, corruption and reordering measurements.
- [ ] Use benchmark values from the actual demo laptop.
- [ ] State limitations and future scope.

## Demo

- [ ] Normal transfer.
- [ ] Loss/retransmission trace.
- [ ] `--reorder 1.0 --trace` demo.
- [ ] Corruption demo.
- [ ] SHA-256 success.
- [ ] Backup UDP port ready.

## Viva

Be ready to explain UDP vs TCP, Stop-and-Wait vs Go-Back-N vs Selective Repeat, sequence numbers, ACK loss, CRC32 vs SHA-256, reordering, sender-window movement and retransmission timeout.
