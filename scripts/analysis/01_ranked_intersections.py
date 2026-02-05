#!/usr/bin/env python3
"""
01_ranked_intersections.py
==========================
Build ranked_intersections.csv for hot/rising intersections.

Purpose:
- Join /new post-level records to ranked surface observations within segments.
- Report observed intersections and lags (lower bounds only).

Inputs:
- analysis_outputs/run_level.csv
- analysis_outputs/post_level.csv
- local/logs/phase2_run_manifest.jsonl (for skipped runs)
- local/raw_jsonl/{run_id}_hot_limit100.jsonl
- local/raw_jsonl/{run_id}_rising_limit100.jsonl

Output:
- analysis_outputs/ranked_intersections.csv

Non-goals:
- No controversial surface.
- No attribution or timing claims beyond observed lags.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set


RUN_LEVEL_PATH = Path("analysis_outputs/run_level.csv")
POST_LEVEL_PATH = Path("analysis_outputs/post_level.csv")
MANIFEST_PATH = Path("local/logs/phase2_run_manifest.jsonl")
RAW_DIR = Path("local/raw_jsonl")
OUTPUT_PATH = Path("analysis_outputs/ranked_intersections.csv")

SURFACES = ["hot", "rising"]
RANKED_TOP_N = 100


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


def read_csv(path: Path) -> List[Dict[str, str]]:
    """Read CSV into list of dicts."""
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    rows: List[Dict[str, str]] = []
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(row)
    if not rows:
        raise ValueError(f"Empty CSV: {path}")
    return rows


def read_manifest_skips(path: Path) -> Dict[str, bool]:
    """Read run_skipped_flag per run_id from the manifest."""
    if not path.exists():
        raise FileNotFoundError(f"Missing manifest: {path}")
    skips: Dict[str, bool] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            run_id = obj.get("run_id_utc")
            if run_id:
                skips[run_id] = bool(obj.get("run_skipped_flag"))
    return skips


def build_run_meta(run_rows: List[Dict[str, str]]) -> Dict[str, Tuple[int, str]]:
    """Map run_id -> (segment_id, run_time_utc)."""
    meta: Dict[str, Tuple[int, str]] = {}
    for row in run_rows:
        run_id = row.get("run_id")
        run_time = row.get("run_time_utc")
        seg_id = row.get("segment_id")
        if not run_id or not run_time or seg_id is None:
            raise ValueError("run_level.csv missing required fields")
        meta[run_id] = (int(seg_id), run_time)
    return meta


def load_ranked_observations(
    run_meta: Dict[str, Tuple[int, str]],
    skipped: Dict[str, bool],
) -> Dict[Tuple[str, int, str], datetime]:
    """Load first observed time on ranked surfaces per (post_id, segment_id, surface)."""
    first_seen: Dict[Tuple[str, int, str], datetime] = {}

    for run_id in sorted(run_meta.keys()):
        seg_id, run_time = run_meta[run_id]
        run_dt = parse_iso_utc(run_time)
        is_skipped = skipped.get(run_id, False)
        for surface in SURFACES:
            path = RAW_DIR / f"{run_id}_{surface}_limit{RANKED_TOP_N}.jsonl"
            if not path.exists():
                if is_skipped:
                    continue
                raise FileNotFoundError(f"Missing ranked raw file for run_id={run_id} surface={surface}")
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    obj = json.loads(line)
                    post_id = obj.get("id")
                    if post_id is None:
                        continue
                    key = (str(post_id), seg_id, surface)
                    if key not in first_seen or run_dt < first_seen[key]:
                        first_seen[key] = run_dt

    return first_seen


def main() -> None:
    post_rows = read_csv(POST_LEVEL_PATH)
    run_rows = read_csv(RUN_LEVEL_PATH)
    skipped = read_manifest_skips(MANIFEST_PATH)

    run_meta = build_run_meta(run_rows)
    ranked_first = load_ranked_observations(run_meta, skipped)

    output_rows: List[Dict[str, str]] = []
    for row in post_rows:
        post_id = row["post_id"]
        seg_id = int(row["segment_id"])
        first_seen_new = parse_iso_utc(row["first_seen_time_utc"])

        def surface_info(surface: str) -> Tuple[str, str, str]:
            key = (post_id, seg_id, surface)
            if key in ranked_first:
                first_in = ranked_first[key]
                lag_minutes = (first_in - first_seen_new).total_seconds() / 60.0
                return (
                    "true",
                    first_in.isoformat().replace("+00:00", "Z"),
                    f"{lag_minutes:.6f}",
                )
            return ("false", "", "")

        ever_hot, first_hot, lag_hot = surface_info("hot")
        ever_rising, first_rising, lag_rising = surface_info("rising")
        ever_in_both = str(ever_hot == "true" and ever_rising == "true").lower()

        output_rows.append({
            "post_id": post_id,
            "segment_id": str(seg_id),
            "ever_in_hot": ever_hot,
            "ever_in_rising": ever_rising,
            "first_in_hot": first_hot,
            "first_in_rising": first_rising,
            "lag_to_hot_minutes": lag_hot,
            "lag_to_rising_minutes": lag_rising,
            "ever_in_both": ever_in_both,
            "ranked_top_n": str(RANKED_TOP_N),
        })

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = [
            "post_id",
            "segment_id",
            "ever_in_hot",
            "ever_in_rising",
            "first_in_hot",
            "first_in_rising",
            "lag_to_hot_minutes",
            "lag_to_rising_minutes",
            "ever_in_both",
            "ranked_top_n",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in output_rows:
            writer.writerow(row)

    print("Wrote analysis_outputs/ranked_intersections.csv")


if __name__ == "__main__":
    main()
