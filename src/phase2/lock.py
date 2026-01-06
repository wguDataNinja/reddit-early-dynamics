from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LockResult:
    acquired: bool
    reason: str  # "acquired" or "overlap_lock_present"


def try_acquire_lock(lock_path: str) -> LockResult:
    p = Path(lock_path)
    p.parent.mkdir(parents=True, exist_ok=True)

    try:
        fd = os.open(str(p), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(fd)
        return LockResult(acquired=True, reason="acquired")
    except FileExistsError:
        return LockResult(acquired=False, reason="overlap_lock_present")


def release_lock(lock_path: str) -> None:
    p = Path(lock_path)
    try:
        p.unlink()
    except FileNotFoundError:
        return