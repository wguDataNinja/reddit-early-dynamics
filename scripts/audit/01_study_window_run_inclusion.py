"""
Study window run inclusion audit.

Purpose:
- Define a 7-day study window using a parameterized anchor.
- List in-window runs in a compact roster.
- Report mechanical gaps within the window.

Inputs:
- local/logs/phase2_run_manifest.jsonl
- local/raw_jsonl/

Outputs (analysis_outputs/audit/):
- study_window_summary.json
- study_window_gaps.csv
- study_window_runs_compact.csv

Non-goals:
- No debug outputs.
- No incident attribution.
- No data fixing or backfills.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


MANIFEST_PATH = Path("local/logs/phase2_run_manifest.jsonl")
RAW_DIR = Path("local/raw_jsonl")
OUTPUT_DIR = Path("analysis_outputs/audit")

SURFACES = ["new", "hot", "rising", "controversial"]


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Declare study window and list in-window runs with file checks."
    )
    parser.add_argument(
        "--anchor",
        choices=["earliest_manifest_run", "first_sustained_15min_cadence", "explicit_iso"],
        default="first_sustained_15min_cadence",
        help="Window anchor mode.",
    )
    parser.add_argument(
        "--explicit-start-utc",
        default=None,
        help="Explicit ISO UTC start timestamp (required for anchor=explicit_iso).",
    )
    parser.add_argument(
        "--cadence-min",
        type=float,
        default=13.0,
        help="Minimum gap minutes for cadence streak (default: 13).",
    )
    parser.add_argument(
        "--cadence-max",
        type=float,
        default=17.0,
        help="Maximum gap minutes for cadence streak (default: 17).",
    )
    parser.add_argument(
        "--streak-length",
        type=int,
        default=3,
        help="Minimum consecutive run count for cadence streak (default: 3).",
    )
    return parser.parse_args()


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


def read_manifest(path: Path) -> List[Dict[str, Any]]:
    """Read JSONL manifest records from disk."""
    if not path.exists():
        raise FileNotFoundError(f"Manifest file missing: {path}")
    records: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                obj = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number}") from exc
            if not isinstance(obj, dict):
                raise ValueError(f"Manifest line {line_number} is not a JSON object")
            records.append(obj)
    if not records:
        raise ValueError("Manifest is empty; no records to process")
    return records


def classify_run(record: Dict[str, Any]) -> str:
    """Classify a run as skipped, partial, or success."""
    if record.get("run_skipped_flag") is True:
        return "skipped"
    if record.get("core_miss_flag") is True:
        return "partial"
    return "success"


def build_run_list(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Attach parsed run_started_utc datetimes and return sorted run list."""
    runs: List[Dict[str, Any]] = []
    for record in records:
        ts = record.get("run_started_utc")
        if ts is None:
            continue
        dt = parse_iso_utc(ts)
        record_copy = dict(record)
        record_copy["_run_started_dt"] = dt
        runs.append(record_copy)
    if not runs:
        raise ValueError("No manifest records with run_started_utc")
    runs.sort(key=lambda r: r["_run_started_dt"])
    return runs


def find_window_start(
    runs: List[Dict[str, Any]],
    anchor: str,
    explicit_start: Optional[str],
    cadence_min: float,
    cadence_max: float,
    streak_length: int,
) -> Tuple[datetime, Dict[str, Any]]:
    """Determine window start based on anchor policy."""
    if anchor == "earliest_manifest_run":
        return runs[0]["_run_started_dt"], {"anchor": anchor}

    if anchor == "explicit_iso":
        if not explicit_start:
            raise ValueError("--explicit-start-utc is required when anchor=explicit_iso")
        start_dt = parse_iso_utc(explicit_start)
        return start_dt, {"anchor": anchor, "explicit_start_utc": explicit_start}

    if anchor == "first_sustained_15min_cadence":
        if streak_length < 2:
            raise ValueError("streak-length must be >= 2")
        required_gaps = streak_length - 1
        for i in range(required_gaps, len(runs)):
            ok = True
            for j in range(required_gaps):
                dt_prev = runs[i - required_gaps + j]["_run_started_dt"]
                dt_cur = runs[i - required_gaps + j + 1]["_run_started_dt"]
                gap_minutes = (dt_cur - dt_prev).total_seconds() / 60.0
                if not (cadence_min <= gap_minutes <= cadence_max):
                    ok = False
                    break
            if ok:
                start_dt = runs[i - required_gaps]["_run_started_dt"]
                meta = {
                    "anchor": anchor,
                    "cadence_min": cadence_min,
                    "cadence_max": cadence_max,
                    "streak_length": streak_length,
                }
                return start_dt, meta
        raise ValueError("No sustained cadence streak found for given parameters")

    raise ValueError(f"Unknown anchor: {anchor}")


def raw_files_present(run_id: str) -> Dict[str, bool]:
    """Check raw JSONL file presence by exact expected filenames for each surface."""
    results = {surface: False for surface in SURFACES}
    if not run_id or not RAW_DIR.exists():
        return results

    for surface in SURFACES:
        expected = RAW_DIR / f"{run_id}_{surface}_limit100.jsonl"
        results[surface] = expected.exists()
    return results


def build_gaps(runs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build gaps between consecutive runs by run_started_utc."""
    gaps: List[Dict[str, Any]] = []
    for i in range(1, len(runs)):
        prev_dt = runs[i - 1]["_run_started_dt"]
        cur_dt = runs[i]["_run_started_dt"]
        gap_minutes = (cur_dt - prev_dt).total_seconds() / 60.0
        gaps.append(
            {
                "prev_run_started_utc": runs[i - 1]["run_started_utc"],
                "next_run_started_utc": runs[i]["run_started_utc"],
                "gap_minutes": round(gap_minutes, 6),
                "gt30m": str(gap_minutes > 30.0).lower(),
                "gt60m": str(gap_minutes > 60.0).lower(),
            }
        )
    return gaps


def write_gaps_csv(path: Path, gaps: List[Dict[str, Any]]) -> None:
    """Write gaps CSV."""
    fieldnames = [
        "prev_run_started_utc",
        "next_run_started_utc",
        "gap_minutes",
        "gt30m",
        "gt60m",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in gaps:
            writer.writerow(row)


def gap_stats(gaps: List[Dict[str, Any]]) -> Dict[str, Optional[float]]:
    """Compute min/median/p95 gap minutes from gap list."""
    if not gaps:
        return {"min": None, "median": None, "p95": None}
    values = [row["gap_minutes"] for row in gaps]
    values_sorted = sorted(values)
    min_val = values_sorted[0]
    median_val = statistics.median(values_sorted)
    idx = int(round(0.95 * (len(values_sorted) - 1)))
    p95_val = values_sorted[idx]
    return {
        "min": round(min_val, 6),
        "median": round(median_val, 6),
        "p95": round(p95_val, 6),
    }


def write_runs_compact_csv(path: Path, runs: List[Dict[str, Any]]) -> None:
    """Write in-window runs to CSV (compact schema)."""
    fieldnames = [
        "run_id_utc",
        "run_started_utc",
        "classification",
        "run_skip_reason",
        "core_row_count_new",
        "raw_files_present_all",
        "missing_surfaces",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in runs:
            run_id = record.get("run_id_utc")
            presence = raw_files_present(run_id)
            missing = [s for s, ok in presence.items() if not ok]
            writer.writerow(
                {
                    "run_id_utc": run_id,
                    "run_started_utc": record.get("run_started_utc"),
                    "classification": classify_run(record),
                    "run_skip_reason": record.get("run_skip_reason"),
                    "core_row_count_new": record.get("core_row_count_new"),
                    "raw_files_present_all": str(all(presence.values())).lower(),
                    "missing_surfaces": ",".join(missing),
                }
            )


def main() -> None:
    """Run the study window inclusion audit."""
    args = parse_args()

    records = read_manifest(MANIFEST_PATH)
    runs = build_run_list(records)

    window_start_dt, anchor_meta = find_window_start(
        runs,
        anchor=args.anchor,
        explicit_start=args.explicit_start_utc,
        cadence_min=args.cadence_min,
        cadence_max=args.cadence_max,
        streak_length=args.streak_length,
    )
    window_end_dt = window_start_dt + timedelta(days=7)

    in_window = [
        r for r in runs if window_start_dt <= r["_run_started_dt"] < window_end_dt
    ]

    in_window_sorted = sorted(in_window, key=lambda r: r["_run_started_dt"])

    gaps = build_gaps(in_window_sorted)
    stats = gap_stats(gaps)

    in_window_success = sum(1 for r in in_window_sorted if classify_run(r) == "success")
    in_window_partial = sum(1 for r in in_window_sorted if classify_run(r) == "partial")
    in_window_skipped = sum(1 for r in in_window_sorted if classify_run(r) == "skipped")

    hard_gaps_gt30 = sum(1 for g in gaps if g["gt30m"] == "true")
    hard_gaps_gt60 = sum(1 for g in gaps if g["gt60m"] == "true")

    summary = {
        "window_start_utc": window_start_dt.isoformat().replace("+00:00", "Z"),
        "window_end_utc": window_end_dt.isoformat().replace("+00:00", "Z"),
        "anchor": anchor_meta,
        "manifest_total_with_run_started_utc": len(runs),
        "in_window_total": len(in_window_sorted),
        "in_window_success": in_window_success,
        "in_window_partial": in_window_partial,
        "in_window_skipped": in_window_skipped,
        "in_window_hard_gaps_gt30m": hard_gaps_gt30,
        "in_window_hard_gaps_gt60m": hard_gaps_gt60,
        "in_window_gap_minutes_min": stats["min"],
        "in_window_gap_minutes_median": stats["median"],
        "in_window_gap_minutes_p95": stats["p95"],
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    (OUTPUT_DIR / "study_window_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_gaps_csv(OUTPUT_DIR / "study_window_gaps.csv", gaps)
    write_runs_compact_csv(
        OUTPUT_DIR / "study_window_runs_compact.csv", in_window_sorted
    )

    print(f"Wrote study window outputs to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
