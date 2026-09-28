"""Unified command-line entry point for RDTX."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from experiments import benchmark

from . import __version__
from . import receiver, sender


def _top_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rdtx",
        description="RDTX — reliable file transfer and network experiments over UDP.",
        epilog=(
            "Examples:\n"
            "  python -m rdtx receive --port 9000\n"
            "  python -m rdtx send demo.txt --loss 0.20\n"
            "  python -m rdtx send demo.txt --reorder 1.0 --trace\n"
            "  python -m rdtx benchmark --size-kib 64"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"RDTX {__version__}")
    parser.add_argument(
        "command",
        nargs="?",
        choices=("send", "receive", "benchmark"),
        help="operation to perform",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = list(argv) if argv is not None else sys.argv[1:]
    parser = _top_parser()

    if not args or args[0] in {"-h", "--help"}:
        parser.print_help()
        return 0
    if args[0] == "--version":
        parser.parse_args(args)
        return 0

    command, command_args = args[0], args[1:]
    try:
        if command == "send":
            sender.main(command_args)
            return 0
        if command == "receive":
            receiver.main(command_args)
            return 0
        if command == "benchmark":
            benchmark.main(command_args)
            return 0
    except KeyboardInterrupt:
        print("\nRDTX interrupted by user.", file=sys.stderr)
        return 130
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"RDTX error: {exc}", file=sys.stderr)
        return 1

    parser.error(f"unknown command: {command}")
    return 2


def send_main() -> int:
    return main(["send", *sys.argv[1:]])


def receive_main() -> int:
    return main(["receive", *sys.argv[1:]])


def benchmark_main() -> int:
    return main(["benchmark", *sys.argv[1:]])
