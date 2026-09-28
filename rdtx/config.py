"""Shared defaults and validation helpers for RDTX."""

from __future__ import annotations

import argparse

DEFAULT_PORT = 9000
DEFAULT_CHUNK_SIZE = 1024
DEFAULT_WINDOW_SIZE = 8
DEFAULT_TIMEOUT = 0.35
DEFAULT_MAX_RETRIES = 40
DEFAULT_LINGER = 1.5
MAX_UDP_DATAGRAM = 65_535


def port_number(value: str) -> int:
    number = int(value)
    if not 1 <= number <= 65_535:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return number


def probability(value: str) -> float:
    number = float(value)
    if not 0.0 <= number <= 1.0:
        raise argparse.ArgumentTypeError("probability must be between 0.0 and 1.0")
    return number


def positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("value must be >= 1")
    return number


def positive_float(value: str) -> float:
    number = float(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("value must be > 0")
    return number


def non_negative_float(value: str) -> float:
    number = float(value)
    if number < 0:
        raise argparse.ArgumentTypeError("value must be >= 0")
    return number
