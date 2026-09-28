"""Selective Repeat sender-window state for RDTX."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class SelectiveRepeatWindow:
    """Track the legal send range and acknowledgements for Selective Repeat.

    New sequence numbers may only be emitted while they are within
    [base, base + window_size). Acknowledgements can arrive out of order,
    but the base advances only across a contiguous acknowledged prefix.
    """

    total_packets: int
    window_size: int
    base: int = 0
    next_seq: int = 0
    acknowledged_count: int = 0
    _acked_out_of_order: set[int] = field(default_factory=set)

    def __post_init__(self) -> None:
        if self.total_packets < 0:
            raise ValueError("total_packets must be >= 0")
        if self.window_size < 1:
            raise ValueError("window_size must be >= 1")

    @property
    def upper_bound(self) -> int:
        """Exclusive upper bound of the current sender window."""
        return min(self.total_packets, self.base + self.window_size)

    @property
    def can_send(self) -> bool:
        """Whether another new DATA sequence number may enter the window."""
        return self.next_seq < self.upper_bound

    @property
    def complete(self) -> bool:
        """Whether every DATA sequence number has been acknowledged."""
        return self.acknowledged_count == self.total_packets

    def take_next(self) -> int:
        """Reserve and return the next legal sequence number."""
        if not self.can_send:
            raise RuntimeError("sender window is full")
        seq = self.next_seq
        self.next_seq += 1
        return seq

    def acknowledge(self, seq: int) -> bool:
        """Record an ACK and advance the base when possible.

        Returns True only for a newly accepted acknowledgement.
        ACKs below the current base are duplicates. ACKs outside the
        transmitted/current range are ignored.
        """
        if seq < self.base:
            return False
        if seq >= self.next_seq or seq >= self.total_packets:
            return False
        if seq in self._acked_out_of_order:
            return False

        self._acked_out_of_order.add(seq)
        self.acknowledged_count += 1

        while self.base in self._acked_out_of_order:
            self._acked_out_of_order.remove(self.base)
            self.base += 1

        return True
