"""
filesystem overlap lock for collection runs

- prevents overlapping executions
- uses exclusive-create lock files
- never waits or retries
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LockResult:
    """
    result of attempting to acquire the run overlap lock

    - acquired indicates success or skip
    - reason is logged verbatim in the manifest
    """
    acquired: bool
    reason: str  # "acquired" or "overlap_lock_present"


def try_acquire_lock(lock_path: str) -> LockResult:
    """
    attempt to acquire the overlap lock

    - creates the lock file atomically
    - returns acquired false if the lock already exists
    """
    p = Path(lock_path)
    p.parent.mkdir(parents=True, exist_ok=True)

    try:
        fd = os.open(str(p), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(fd)
        return LockResult(acquired=True, reason="acquired")
    except FileExistsError:
        return LockResult(acquired=False, reason="overlap_lock_present")


def release_lock(lock_path: str) -> None:
    """
    release the overlap lock

    - best-effort cleanup
    - missing lock file means nothing to release
    """
    p = Path(lock_path)
    try:
        p.unlink()
    except FileNotFoundError:
        return