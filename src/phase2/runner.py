"""
single-run snapshot collector

- fetches listing snapshots once per run
- writes raw jsonl outputs and logs
- appends manifest record
"""

from __future__ import annotations

import json
import logging
import random
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from src.phase2.constants import (
    SUBREDDIT,
    SURFACES_ORDERED,
    NEW_LIMIT,
    RANKED_LIMIT,
    RAW_DIR,
    LOG_DIR,
    MANIFEST_PATH,
    LOCK_PATH,
    PHASE2_START_PATH,
    NEW_ROW_FLOOR,
    RANKED_ROW_FLOOR,
    SURFACE_PAUSE_SECONDS_RANGE,
    COHORT_ENABLED,
    COHORT_DIR,
    COHORT_STATE_PATH,
)
from src.phase2.lock import try_acquire_lock, release_lock
from src.phase2.manifest import RunManifestRecord, append_manifest_record
from src.phase2.praw_client_phase2 import get_reddit_client_with_counter
from src.phase2.start_marker import ensure_phase2_start_marker, read_phase2_start_marker


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def utc_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")


def ensure_dirs() -> None:
    Path(RAW_DIR).mkdir(parents=True, exist_ok=True)
    Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
    Path(COHORT_DIR).mkdir(parents=True, exist_ok=True)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, default=str, ensure_ascii=False) + "\n")


def count_jsonl_rows(path: Path) -> int:
    n = 0
    with path.open("r", encoding="utf-8") as f:
        for n, _ in enumerate(f, 1):
            pass
    return n


def surface_limit(surface: str) -> int:
    return NEW_LIMIT if surface == "new" else RANKED_LIMIT


def surface_row_floor(surface: str) -> int:
    return NEW_ROW_FLOOR if surface == "new" else RANKED_ROW_FLOOR


@dataclass
class CoreSurfaceResult:
    surface: str
    out_path: Path
    row_count: int
    ok: bool
    reason: Optional[str]


def fetch_surface(subreddit, surface: str, run_id: str, captured_utc: str) -> list[dict[str, Any]]:
    limit = surface_limit(surface)

    if surface == "new":
        listing = subreddit.new(limit=limit)
    elif surface == "hot":
        listing = subreddit.hot(limit=limit)
    elif surface == "rising":
        listing = subreddit.rising(limit=limit)
    elif surface == "controversial":
        listing = subreddit.controversial(limit=limit)
    else:
        raise ValueError(f"Unknown surface: {surface}")

    rows: list[dict[str, Any]] = []
    for rank, submission in enumerate(listing, start=1):
        _ = submission.id
        row = vars(submission).copy()
        row["captured_utc"] = captured_utc
        row["surface"] = surface
        row["surface_rank"] = None if surface == "new" else rank
        row["listing_run_id"] = run_id
        rows.append(row)
    return rows


def evaluate_surface_success(surface: str, out_path: Path) -> CoreSurfaceResult:
    if not out_path.exists():
        return CoreSurfaceResult(surface, out_path, 0, False, "file_missing")

    if out_path.stat().st_size == 0:
        return CoreSurfaceResult(surface, out_path, 0, False, "file_empty")

    row_count = count_jsonl_rows(out_path)
    floor = surface_row_floor(surface)
    if row_count < floor:
        return CoreSurfaceResult(surface, out_path, row_count, False, f"row_count_below_floor:{row_count}<{floor}")

    return CoreSurfaceResult(surface, out_path, row_count, True, None)


def setup_run_logger(run_id: str) -> logging.Logger:
    logger = logging.getLogger(f"phase2.{run_id}")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if logger.handlers:
        return logger

    log_path = Path(LOG_DIR) / f"{run_id}_phase2.log"
    fh = logging.FileHandler(log_path, encoding="utf-8")
    sh = logging.StreamHandler()

    fmt = logging.Formatter("%(message)s")
    fh.setFormatter(fmt)
    sh.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger


def main() -> None:
    ensure_dirs()
    run_id = utc_run_id()
    run_started_utc = utc_now_iso()
    run_started_dt = datetime.now(timezone.utc)

    logger = setup_run_logger(run_id)

    lock = try_acquire_lock(LOCK_PATH)
    if not lock.acquired:
        # Overlap skip: explicit skip fields; not a success.
        rec = RunManifestRecord(
            run_id_utc=run_id,
            run_started_utc=run_started_utc,
            run_finished_utc=None,
            duration_seconds=None,
            run_skipped_flag=True,
            run_skip_reason="overlap_lock_present",
            core_http_calls_this_run=0,
            core_http_calls_total=_read_previous_totals(MANIFEST_PATH)[0],
            cohort_http_calls_this_run=0,
            cohort_http_calls_total=_read_previous_totals(MANIFEST_PATH)[1],
            http_calls_this_run_total=0,
            http_calls_total=sum(_read_previous_totals(MANIFEST_PATH)),
            cohort_pct_this_run=None,
            cohort_pct_total=None,
            core_row_count_new=None,
            core_row_count_hot=None,
            core_row_count_rising=None,
            core_row_count_controversial=None,
            new_row_floor_used=NEW_ROW_FLOOR,
            core_miss_flag=False,
            core_miss_reason=None,
            due_cohort_queue_size_before=None,
            due_cohort_queue_size_after=None,
            cohort_dedup_skips_this_run=None,
            errors_this_run=["overlap_skip"],
        )
        append_manifest_record(MANIFEST_PATH, rec)

        logger.info("PHASE2 RUN START")
        logger.info(f"run_id_utc={run_id}")
        logger.info(f"run_started_utc={run_started_utc}")
        logger.info("CORE SURFACES")
        logger.info("new_rows_written=None")
        logger.info("hot_rows_written=None")
        logger.info("rising_rows_written=None")
        logger.info("controversial_rows_written=None")
        logger.info("CORE SUCCESS EVAL")
        logger.info(f"new_row_floor_used={NEW_ROW_FLOOR}")
        logger.info("core_miss_flag=false")
        logger.info("COHORT")
        logger.info(f"cohort_enabled={str(COHORT_ENABLED).lower()}")
        logger.info("HTTP ACCOUNTING")
        logger.info("core_http_calls_this_run=0")
        logger.info("cohort_http_calls_this_run=0")
        logger.info("http_calls_this_run_total=0")
        logger.info("PHASE2 RUN END")
        return

    # Start marker must be written at the beginning of the first real run.
    ensure_phase2_start_marker(PHASE2_START_PATH, run_started_utc)

    core_http_calls_this_run = 0
    cohort_http_calls_this_run = 0
    errors_this_run: list[str] = []

    core_results: dict[str, CoreSurfaceResult] = {}

    try:
        logger.info("PHASE2 RUN START")
        logger.info(f"run_id_utc={run_id}")
        logger.info(f"run_started_utc={run_started_utc}")

        reddit, requestor = get_reddit_client_with_counter()
        subreddit = reddit.subreddit(SUBREDDIT)

        captured_utc = utc_now_iso()

        logger.info("CORE SURFACES")
        for i, surface in enumerate(SURFACES_ORDERED):
            limit = surface_limit(surface)
            out_path = Path(RAW_DIR) / f"{run_id}_{surface}_limit{limit}.jsonl"

            try:
                rows = fetch_surface(subreddit, surface, run_id, captured_utc)
                write_jsonl(out_path, rows)
            except Exception as e:
                errors_this_run.append(f"surface_fetch_error:{surface}:{type(e).__name__}")
                write_jsonl(out_path, [])
                logger.info(f"error surface={surface} err={type(e).__name__}")

            if i < len(SURFACES_ORDERED) - 1:
                lo, hi = SURFACE_PAUSE_SECONDS_RANGE
                time.sleep(random.uniform(lo, hi))

            res = evaluate_surface_success(surface, out_path)
            core_results[surface] = res
            logger.info(f"{surface}_rows_written={res.row_count}")

        core_miss_flag = any(not r.ok for r in core_results.values())
        core_miss_reason = None
        if core_miss_flag:
            for s in SURFACES_ORDERED:
                r = core_results[s]
                if not r.ok:
                    core_miss_reason = f"{s}:{r.reason}"
                    break

        logger.info("CORE SUCCESS EVAL")
        logger.info(f"new_row_floor_used={NEW_ROW_FLOOR}")
        logger.info(f"core_miss_flag={str(core_miss_flag).lower()}")
        if core_miss_flag and core_miss_reason:
            logger.info(f"core_miss_reason={core_miss_reason}")

        # Cohort (always log section)
        due_before = None
        due_after = None
        dedup_skips = None
        cohort_miss_flag = False
        cohort_miss_reason = None
        cohort_fetched_count = 0

        logger.info("COHORT")
        logger.info(f"cohort_enabled={str(COHORT_ENABLED).lower()}")

        if COHORT_ENABLED:
            from src.phase2.cohort import CohortManager

            seen_ids: set[str] = set()
            for s in SURFACES_ORDERED:
                limit = surface_limit(s)
                p = Path(RAW_DIR) / f"{run_id}_{s}_limit{limit}.jsonl"
                if not p.exists() or p.stat().st_size == 0:
                    continue
                with p.open("r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            obj = json.loads(line)
                            pid = obj.get("id")
                            if isinstance(pid, str):
                                seen_ids.add(pid)
                        except Exception:
                            continue

            mgr = CohortManager(
                cohort_state_path=COHORT_STATE_PATH,
                phase2_start_path=PHASE2_START_PATH,
            )

            mgr.ingest_listing_observations(
                run_started_utc=run_started_utc,
                listing_rows_by_surface_paths={
                    s: str(Path(RAW_DIR) / f"{run_id}_{s}_limit{surface_limit(s)}.jsonl")
                    for s in SURFACES_ORDERED
                },
            )

            due_before, due_after, dedup_skips, cohort_fetched_count, cohort_miss_flag, cohort_miss_reason = mgr.process_due_queue(
                reddit=reddit,
                run_started_utc=run_started_utc,
                seen_ids=seen_ids,
            )
            cohort_http_calls_this_run = mgr.cohort_http_calls_this_run

        logger.info(f"due_cohort_queue_size_before={due_before}")
        logger.info(f"cohort_fetched_count={cohort_fetched_count}")
        logger.info(f"cohort_dedup_skips_this_run={dedup_skips}")
        logger.info(f"due_cohort_queue_size_after={due_after}")
        logger.info(f"cohort_miss_flag={str(cohort_miss_flag).lower()}")
        if cohort_miss_flag and cohort_miss_reason:
            logger.info(f"cohort_miss_reason={cohort_miss_reason}")

        total_http_calls_this_run = int(getattr(requestor, "request_count", 0))
        core_http_calls_this_run = max(total_http_calls_this_run - cohort_http_calls_this_run, 0)

        core_total_prev, cohort_total_prev = _read_previous_totals(MANIFEST_PATH)
        core_http_calls_total = core_total_prev + core_http_calls_this_run
        cohort_http_calls_total = cohort_total_prev + cohort_http_calls_this_run

        http_calls_total = core_http_calls_total + cohort_http_calls_total
        http_calls_this_run_total = core_http_calls_this_run + cohort_http_calls_this_run

        cohort_pct_this_run = None
        if http_calls_this_run_total > 0:
            cohort_pct_this_run = (cohort_http_calls_this_run / http_calls_this_run_total) * 100.0

        cohort_pct_total = None
        if http_calls_total > 0:
            cohort_pct_total = (cohort_http_calls_total / http_calls_total) * 100.0

        logger.info("HTTP ACCOUNTING")
        logger.info(f"core_http_calls_this_run={core_http_calls_this_run}")
        logger.info(f"cohort_http_calls_this_run={cohort_http_calls_this_run}")
        logger.info(f"http_calls_this_run_total={http_calls_this_run_total}")
        logger.info(f"core_http_calls_total={core_http_calls_total}")
        logger.info(f"cohort_http_calls_total={cohort_http_calls_total}")
        logger.info(f"http_calls_total={http_calls_total}")
        logger.info(f"cohort_pct_this_run={cohort_pct_this_run}")
        logger.info(f"cohort_pct_total={cohort_pct_total}")

        run_finished_utc = utc_now_iso()
        duration_seconds = (datetime.now(timezone.utc) - run_started_dt).total_seconds()

        logger.info("PHASE2 RUN END")
        logger.info(f"run_finished_utc={run_finished_utc}")
        logger.info(f"duration_seconds={duration_seconds}")

        rec = RunManifestRecord(
            run_id_utc=run_id,
            run_started_utc=run_started_utc,
            run_finished_utc=run_finished_utc,
            duration_seconds=duration_seconds,
            run_skipped_flag=False,
            run_skip_reason=None,
            core_http_calls_this_run=core_http_calls_this_run,
            core_http_calls_total=core_http_calls_total,
            cohort_http_calls_this_run=cohort_http_calls_this_run,
            cohort_http_calls_total=cohort_http_calls_total,
            http_calls_this_run_total=http_calls_this_run_total,
            http_calls_total=http_calls_total,
            cohort_pct_this_run=cohort_pct_this_run,
            cohort_pct_total=cohort_pct_total,
            core_row_count_new=core_results.get("new").row_count if "new" in core_results else None,
            core_row_count_hot=core_results.get("hot").row_count if "hot" in core_results else None,
            core_row_count_rising=core_results.get("rising").row_count if "rising" in core_results else None,
            core_row_count_controversial=core_results.get("controversial").row_count if "controversial" in core_results else None,
            new_row_floor_used=NEW_ROW_FLOOR,
            core_miss_flag=core_miss_flag,
            core_miss_reason=core_miss_reason,
            due_cohort_queue_size_before=due_before,
            due_cohort_queue_size_after=due_after,
            cohort_dedup_skips_this_run=dedup_skips,
            errors_this_run=(errors_this_run if errors_this_run else None),
        )
        append_manifest_record(MANIFEST_PATH, rec)

    finally:
        release_lock(LOCK_PATH)


def _read_previous_totals(manifest_path: str) -> tuple[int, int]:
    p = Path(manifest_path)
    if not p.exists():
        return 0, 0

    last_non_empty = None
    try:
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    last_non_empty = line.strip()
        if not last_non_empty:
            return 0, 0
        obj = json.loads(last_non_empty)
        core_total = int(obj.get("core_http_calls_total", 0) or 0)
        cohort_total = int(obj.get("cohort_http_calls_total", 0) or 0)
        return core_total, cohort_total
    except Exception:
        return 0, 0


if __name__ == "__main__":
    main()