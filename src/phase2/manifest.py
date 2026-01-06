from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class RunManifestRecord:
    # Run timing
    run_id_utc: str
    run_started_utc: str
    run_finished_utc: Optional[str]
    duration_seconds: Optional[float]

    # Skip semantics (explicit)
    run_skipped_flag: bool
    run_skip_reason: Optional[str]

    # HTTP accounting
    core_http_calls_this_run: int
    core_http_calls_total: int
    cohort_http_calls_this_run: int
    cohort_http_calls_total: int
    http_calls_this_run_total: int
    http_calls_total: int
    cohort_pct_this_run: Optional[float]
    cohort_pct_total: Optional[float]

    # Core row counts
    core_row_count_new: Optional[int]
    core_row_count_hot: Optional[int]
    core_row_count_rising: Optional[int]
    core_row_count_controversial: Optional[int]

    # Core success eval
    new_row_floor_used: int
    core_miss_flag: bool
    core_miss_reason: Optional[str]

    # Cohort diagnostics
    due_cohort_queue_size_before: Optional[int]
    due_cohort_queue_size_after: Optional[int]
    cohort_dedup_skips_this_run: Optional[int]

    # Errors (stable type)
    errors_this_run: Optional[list[str]]


@dataclass(frozen=True)
class ManifestLockResult:
    acquired: bool
    reason: Optional[str] = None


def _try_acquire_atomic_lock(lock_path: str) -> ManifestLockResult:
    lp = Path(lock_path)
    lp.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(lp), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(fd)
        return ManifestLockResult(acquired=True, reason=None)
    except FileExistsError:
        return ManifestLockResult(acquired=False, reason="manifest_lock_present")
    except Exception as e:
        return ManifestLockResult(acquired=False, reason=f"manifest_lock_error:{type(e).__name__}")


def _release_lock(lock_path: str) -> None:
    try:
        Path(lock_path).unlink(missing_ok=True)
    except Exception:
        # Never raise from lock release
        pass


def append_manifest_record(path: str, rec: RunManifestRecord) -> None:
    """
    Append-only, single-writer semantics via a dedicated manifest lock.
    No waiting, no retries: if the lock is present, raise so the caller can log it.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    lock_path = str(p.parent / "phase2_manifest.lock")
    lock = _try_acquire_atomic_lock(lock_path)
    if not lock.acquired:
        raise RuntimeError(lock.reason or "manifest_lock_failed")

    try:
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(rec), ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
    finally:
        _release_lock(lock_path)