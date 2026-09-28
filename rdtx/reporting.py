"""Utilities for exporting reproducible RDTX experiment results."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import __version__


def save_stats(path: str | Path, role: str, stats: Any, **context: Any) -> Path:
    """Write transfer statistics as a structured JSON report."""
    if not is_dataclass(stats):
        raise TypeError("stats must be a dataclass instance")

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "project": "RDTX",
        "version": __version__,
        "role": role,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "context": context,
        "stats": asdict(stats),
    }
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target
