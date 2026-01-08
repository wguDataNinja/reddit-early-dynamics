"""
collection start marker utilities

- a single utc start timestamp
- anchors day indexing and cohort selection seeds
"""

from __future__ import annotations

import os
from pathlib import Path


def ensure_phase2_start_marker(path: str, run_started_utc: str) -> None:
    """
    write the collection start marker once

    - creates the file atomically
    - does nothing if it already exists
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    try:
        fd = os.open(str(p), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(run_started_utc.strip() + "\n")
    except FileExistsError:
        return


def read_phase2_start_marker(path: str) -> str | None:
    """
    read the stored collection start marker

    - returns none if missing or unreadable
    """
    p = Path(path)
    if not p.exists():
        return None
    try:
        txt = p.read_text(encoding="utf-8").strip()
        return txt if txt else None
    except Exception:
        return None