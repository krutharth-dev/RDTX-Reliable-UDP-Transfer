# Contributing to RDTX VisualLab

RDTX VisualLab is an educational Computer Networks project. Contributions should improve reliability, observability, reproducibility, or documentation without hiding the networking mechanisms the project is intended to demonstrate.

## Workflow

1. Create a branch from `main`.
2. Keep one pull request focused on one logical change.
3. Add or update tests for behavior changes.
4. Update protocol/web documentation when interfaces or packet behavior change.
5. Run `make test` before opening the pull request.
6. For demo-sensitive changes, run `make demo-check`.

## Design principles

- Keep UDP socket and ARQ behavior explicit.
- Do not move transport reliability into browser JavaScript.
- Prefer standard-library networking components.
- Avoid dependencies that do not add clear educational value.
- Keep localhost operation as the reliable fallback.
- Treat LAN mode as a controlled/private-network experiment.
- Preserve deterministic seeds for impairment experiments.

## Areas and tests

| Change | Expected verification |
|---|---|
| Packet/wire format | Protocol tests + docs/PROTOCOL.md |
| Sender window/ACK logic | Window tests + integration test |
| Receiver validation | Receiver/integration tests |
| Web API/UI | Web integration tests |
| LAN behavior | LAN-mode integration test |
| Matrix behavior | Matrix integration test |
| Reports/exports | Web/report assertions |
| Packaging/CLI | CLI tests + CI installed-command check |

## Pull requests

Use the repository pull-request template and describe:

- what changed;
- why it matters to the CN project;
- how it was tested;
- whether protocol semantics changed.
