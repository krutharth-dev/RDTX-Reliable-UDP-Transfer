# Contributing to RDTX

RDTX is an educational Computer Networks mini-project. Changes should keep the protocol easy to inspect and explain.

## Development workflow

1. Create a branch from main.
2. Keep changes focused and use descriptive commit messages.
3. Run make test before opening a pull request.
4. Update documentation when packet behavior or CLI options change.
5. Do not add third-party runtime dependencies unless there is a clear educational need.

## Code style

- Python 3.10+.
- Prefer small functions and explicit protocol state.
- Keep wire-format changes documented in docs/PROTOCOL.md.
- Add or update tests for behavioral changes.
- Avoid hiding networking logic behind frameworks; the project is meant to demonstrate sockets and reliability mechanisms directly.

## Testing

    make test

The integration tests use localhost UDP sockets and include deterministic packet-loss scenarios.
