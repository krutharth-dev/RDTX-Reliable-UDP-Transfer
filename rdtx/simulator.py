"""Network impairment simulator used by RDTX demos and tests."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from socket import socket
from typing import Any


@dataclass(slots=True)
class SendResult:
    sent: bool
    corrupted: bool = False
    delayed_ms: float = 0.0


class LossSimulator:
    """Apply packet loss, corruption and delay before UDP sendto()."""

    def __init__(
        self,
        drop_rate: float = 0.0,
        corrupt_rate: float = 0.0,
        max_delay_ms: float = 0.0,
        seed: int | None = None,
    ) -> None:
        for name, value in (("drop_rate", drop_rate), ("corrupt_rate", corrupt_rate)):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
        if max_delay_ms < 0:
            raise ValueError("max_delay_ms must be non-negative")

        self.drop_rate = drop_rate
        self.corrupt_rate = corrupt_rate
        self.max_delay_ms = max_delay_ms
        self._rng = random.Random(seed)

    def sendto(self, sock: socket, data: bytes, address: Any) -> SendResult:
        if self._rng.random() < self.drop_rate:
            return SendResult(sent=False)

        outgoing = data
        corrupted = False
        if data and self._rng.random() < self.corrupt_rate:
            damaged = bytearray(data)
            index = self._rng.randrange(len(damaged))
            damaged[index] ^= 1 << self._rng.randrange(8)
            outgoing = bytes(damaged)
            corrupted = True

        delayed_ms = 0.0
        if self.max_delay_ms > 0:
            delayed_ms = self._rng.uniform(0.0, self.max_delay_ms)
            time.sleep(delayed_ms / 1000.0)

        sock.sendto(outgoing, address)
        return SendResult(sent=True, corrupted=corrupted, delayed_ms=delayed_ms)
