#!/usr/bin/env python3
"""
00_build_tables.py
==================
Build run_level.csv and post_level.csv for the locked portfolio pipeline.

Purpose:
- Use the audit roster to lock the run universe window.
- Build run-level segmentation from manifest run_started_utc.
- Build post-level aggregates from /new observations only.

Inputs:
- analysis_outputs/audit/study_window_runs_compact.csv (authoritative run roster)
- local/logs/phase2_run_manifest.jsonl
- local/raw_jsonl/{run_id}_new_limit1000.jsonl

Outputs:
- analysis_outputs/run_level.csv
- analysis_outputs/post_level.csv

Non-goals:
- No ranked surface work.
- No gap attribution beyond hard-gap segmentation.
- No observation-level outputs.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple


AUDIT_ROSTER_PATH = Path("analysis_outputs/audit/study_window_runs_compact.csv")
MANIFEST_PATH = Path("local/logs/phase2_run_manifest.jsonl")
RAW_DIR = Path("local/raw_jsonl")
OUTPUT_DIR = Path("analysis_outputs")

CADENCE_MAX_MINUTES = 20.0
SOFT_GAP_MAX_MINUTES = 60.0


def parse_iso_utc(timestamp: str) -> datetime:
    """Parse ISO UTC timestamp (ending in Z) to timezone-aware datetime."""
    if not isinstance(timestamp, str) or not timestamp:
        raise ValueError(f"Invalid timestamp value: {timestamp!r}")
    if timestamp.endswith("Z"):
        timestamp = timestamp[:-1] + "+00:00"
    dt = datetime.fromisoformat(timestamp)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def read_audit_roster(path: Path) -> List[str]:
    """Read the authoritative roster of allowed run_id_utc (success only)."""
    if not path.exists():
        raise FileNotFoundError(f"Missing audit roster: {path}")
    with path.open("r", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("Audit roster is empty")
    allowed = []
    for row in rows:
        run_id = row.get("run_id_utc")
        classification = (row.get("classification") or "").strip().lower()
        if not run_id:
            continue
        if classification != "success":
            continue
        allowed.append(run_id)
    if not allowed:
        raise ValueError("Audit roster has no success-classified runs")
    return allowed


def read_manifest(path: Path) -> List[Dict[str, str]]:
    """Read phase2_run_manifest.jsonl into a list of dicts."""
    if not path.exists():
        raise FileNotFoundError(f"Missing manifest: {path}")
    rows: List[Dict[str, str]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    if not rows:
        raise ValueError("Manifest is empty")
    return rows


def build_run_level(rows: List[Dict[str, str]], allowed_run_ids: List[str]) -> List[Dict[str, str]]:
    """Compute run-level table from manifest rows filtered by audit roster."""
    manifest_map: Dict[str, Dict[str, str]] = {}
    for r in rows:
        run_id = r.get("run_id_utc")
        run_time = r.get("run_started_utc")
        if not run_id or not run_time:
            continue
        manifest_map[run_id] = {
            "run_id": run_id,
            "run_time_utc": run_time,
        }

    runs: List[Dict[str, str]] = []
    for run_id in allowed_run_ids:
        if run_id not in manifest_map:
            raise ValueError(f"Run from roster missing in manifest: {run_id}")
        run_time = manifest_map[run_id]["run_time_utc"]
        run_dt = parse_iso_utc(run_time)
        runs.append({
            "run_id": run_id,
            "run_time_utc": run_time,
            "_dt": run_dt,
        })

    if not runs:
        raise ValueError("No runs in manifest for audit roster")

    runs.sort(key=lambda r: r["_dt"])

    # validate strictly increasing timestamps
    for i in range(1, len(runs)):
        if runs[i]["_dt"] <= runs[i - 1]["_dt"]:
            raise ValueError("run_time_utc is not strictly increasing")

    segment_id = 0
    prev_dt: Optional[datetime] = None
    run_index_in_segment = 0
    output: List[Dict[str, str]] = []

    for idx, run in enumerate(runs):
        dt_minutes: Optional[float] = None
        gap_regime = ""
        is_hard_gap = False

        if prev_dt is not None:
            dt_minutes = (run["_dt"] - prev_dt).total_seconds() / 60.0
            if dt_minutes > SOFT_GAP_MAX_MINUTES:
                gap_regime = "hard"
                is_hard_gap = True
            elif dt_minutes > CADENCE_MAX_MINUTES:
                gap_regime = "soft"
            else:
                gap_regime = "cadence"

        if is_hard_gap:
            segment_id += 1
            run_index_in_segment = 0
        elif idx == 0:
            run_index_in_segment = 0
        else:
            run_index_in_segment += 1

        output.append({
            "run_id": run["run_id"],
            "run_time_utc": run["run_time_utc"],
            "dt_minutes": f"{dt_minutes:.6f}" if dt_minutes is not None else "",
            "segment_id": str(segment_id),
            "run_index_in_segment": str(run_index_in_segment),
            "gap_regime": gap_regime,
        })

        prev_dt = run["_dt"]

    # validate contiguity
    last_seg = None
    expected_idx = 0
    for row in output:
        seg = int(row["segment_id"])
        idx = int(row["run_index_in_segment"])
        if last_seg is None or seg != last_seg:
            expected_idx = 0
        if idx != expected_idx:
            raise ValueError("run_index_in_segment is not contiguous")
        expected_idx += 1
        last_seg = seg

    return output


def load_new_observations(run_id: str, run_time_utc: str) -> List[Dict[str, str]]:
    """Load /new observations for a run_id and attach run_time_utc."""
    path = RAW_DIR / f"{run_id}_new_limit1000.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"Missing /new raw file for run_id={run_id}")

    rows: List[Dict[str, str]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            post_id = obj.get("id")
            created_utc = obj.get("created_utc")
            num_comments = obj.get("num_comments")
            score = obj.get("score")
            if post_id is None or created_utc is None or num_comments is None:
                continue
            rows.append({
                "post_id": str(post_id),
                "created_utc": float(created_utc),
                "num_comments": int(num_comments),
                "score": int(score) if score is not None else 0,
                "run_time_utc": run_time_utc,
            })
    return rows


def build_post_level(run_level_rows: List[Dict[str, str]], manifest_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Build post-level aggregates from /new observations within segments."""
    # map run_id -> (run_time_utc, segment_id, run_index_in_segment)
    run_meta: Dict[str, Tuple[str, int, int]] = {}
    segment_end: Dict[int, datetime] = {}

    for row in run_level_rows:
        run_id = row["run_id"]
        run_time = row["run_time_utc"]
        seg_id = int(row["segment_id"])
        run_idx = int(row["run_index_in_segment"])
        run_meta[run_id] = (run_time, seg_id, run_idx)

        run_dt = parse_iso_utc(run_time)
        if seg_id not in segment_end or run_dt > segment_end[seg_id]:
            segment_end[seg_id] = run_dt

    # map run_id -> skipped flag
    skipped_map = {r.get("run_id_utc"): bool(r.get("run_skipped_flag")) for r in manifest_rows if r.get("run_id_utc")}

    observations: List[Dict[str, str]] = []
    missing_new_files: List[str] = []

    for run_id, (run_time, seg_id, run_idx) in run_meta.items():
        skipped = skipped_map.get(run_id, False)
        path = RAW_DIR / f"{run_id}_new_limit1000.jsonl"
        if not path.exists():
            if skipped:
                missing_new_files.append(run_id)
                continue
            raise FileNotFoundError(f"Missing /new raw file for run_id={run_id}")
        new_rows = load_new_observations(run_id, run_time)
        for r in new_rows:
            r["segment_id"] = seg_id
            r["run_index_in_segment"] = run_idx
            observations.append(r)

    if not observations:
        raise ValueError("No /new observations loaded from raw JSONL")

    grouped: Dict[Tuple[str, int], List[Dict[str, str]]] = {}
    for obs in observations:
        key = (obs["post_id"], int(obs["segment_id"]))
        grouped.setdefault(key, []).append(obs)

    output: List[Dict[str, str]] = []
    for (post_id, seg_id), rows in grouped.items():
        rows.sort(key=lambda r: parse_iso_utc(r["run_time_utc"]))
        first = rows[0]
        last = rows[-1]

        first_seen = parse_iso_utc(first["run_time_utc"])
        last_seen = parse_iso_utc(last["run_time_utc"])

        created_time = datetime.fromtimestamp(float(first["created_utc"]), tz=timezone.utc)
        discovery_lag = (first_seen - created_time).total_seconds() / 60.0

        comments_at_first_obs = first["num_comments"] > 0
        ever_comment_nonzero = any(r["num_comments"] > 0 for r in rows)

        first_comment_obs_index: Optional[int] = None
        for idx, r in enumerate(rows):
            if r["num_comments"] > 0:
                first_comment_obs_index = idx
                break

        right_censored = last_seen == segment_end[seg_id]

        is_fresh_capture = discovery_lag <= 15.0

        output.append({
            "post_id": post_id,
            "segment_id": str(seg_id),
            "first_seen_time_utc": first["run_time_utc"],
            "last_seen_time_utc": last["run_time_utc"],
            "n_appearances": str(len(rows)),
            "created_time_utc": created_time.isoformat().replace("+00:00", "Z"),
            "discovery_lag_minutes": f"{discovery_lag:.6f}",
            "comments_present_at_first_observation": str(comments_at_first_obs).lower(),
            "ever_observed_comments": str(ever_comment_nonzero).lower(),
            "first_observed_nonzero_comments_obs_index": "" if first_comment_obs_index is None else str(first_comment_obs_index),
            "is_fresh_capture": str(is_fresh_capture).lower(),
            "right_censored": str(right_censored).lower(),
        })

    # validate uniqueness
    seen = set()
    for row in output:
        key = (row["post_id"], row["segment_id"])
        if key in seen:
            raise ValueError("Duplicate (post_id, segment_id) in post_level")
        seen.add(key)

    output.sort(key=lambda r: (int(r["segment_id"]), r["post_id"]))
    return output


def write_csv(path: Path, rows: List[Dict[str, str]], fieldnames: List[str]) -> None:
    """Write rows to CSV with fixed column order."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    allowed_run_ids = read_audit_roster(AUDIT_ROSTER_PATH)
    manifest_rows = read_manifest(MANIFEST_PATH)
    run_level_rows = build_run_level(manifest_rows, allowed_run_ids)

    # Write run_level.csv
    write_csv(
        OUTPUT_DIR / "run_level.csv",
        run_level_rows,
        [
            "run_id",
            "run_time_utc",
            "dt_minutes",
            "segment_id",
            "run_index_in_segment",
            "gap_regime",
        ],
    )

    post_level_rows = build_post_level(run_level_rows, manifest_rows)
    write_csv(
        OUTPUT_DIR / "post_level.csv",
        post_level_rows,
        [
            "post_id",
            "segment_id",
            "first_seen_time_utc",
            "last_seen_time_utc",
            "n_appearances",
            "created_time_utc",
            "discovery_lag_minutes",
            "comments_present_at_first_observation",
            "ever_observed_comments",
            "first_observed_nonzero_comments_obs_index",
            "is_fresh_capture",
            "right_censored",
        ],
    )

    print("Wrote analysis_outputs/run_level.csv")
    print("Wrote analysis_outputs/post_level.csv")


if __name__ == "__main__":
    main()
