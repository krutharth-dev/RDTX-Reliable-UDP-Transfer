"""Unified command-line entry point for RDTX."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from . import __version__
from . import receiver, sender


def _top_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rdtx",
        description="RDTX — reliable file transfer over UDP.",
        epilog=(
            "Examples:\n"
            "  python -m rdtx receive --port 9000\n"
            "  python -m rdtx send demo.txt --host 127.0.0.1 --loss 0.20\n"
            "  python -m rdtx send --help"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"RDTX {__version__}")
    parser.add_argument("command", nargs="?", choices=("send", "receive"), help="operation to perform")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = list(argv) if argv is not None else None
    parser = _top_parser()

    if args is None:
        import sys
        args = sys.argv[1:]

    if not args or args[0] in {"-h", "--help"}:
        parser.print_help()
        return 0
    if args[0] == "--version":
        parser.parse_args(args)
        return 0

    command, command_args = args[0], args[1:]
    if command == "send":
        sender.main(command_args)
        return 0
    if command == "receive":
        receiver.main(command_args)
        return 0

    parser.error(f"unknown command: {command}")
    return 2
