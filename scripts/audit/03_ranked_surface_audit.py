"""
Ranked surface audit (hot, rising, controversial).

Purpose:
- Within the declared 7-day study window, audit raw JSONL snapshots
  for ranked surfaces only.
- Verify file presence and row-count sanity.

Inputs:
- analysis_outputs/audit/study_window_runs_compact.csv (authoritative inclusion list)
- local/raw_jsonl/ (raw JSONL files)

Outputs (analysis_outputs/audit/):
- ranked_surface_audit_summary.json
- ranked_surface_missing_files.csv

Non-goals:
- No overlap, timing, or attribution analysis.
- No gap-based exclusions.
"""

from __future__ import annotations

import csv
import json
import statistics
from pathlib import Path
from typing import Dict, List, Tuple


RUNS_PATH = Path("analysis_outputs/audit/study_window_runs_compact.csv")
RAW_DIR = Path("local/raw_jsonl")
OUTPUT_DIR = Path("analysis_outputs/audit")

SURFACES = ["hot", "rising", "controversial"]
EXPECTED_LIMIT = 100


def read_success_runs(path: Path) -> List[str]:
    """Read study window runs and return run_id_utc for success runs."""
    if not path.exists():
        raise FileNotFoundError(f"Missing runs file: {path}")
    run_ids: List[str] = []
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row.get("classification") == "success":
                run_id = row.get("run_id_utc")
                if run_id:
                    run_ids.append(run_id)
    if not run_ids:
        raise ValueError("No success runs found in study_window_runs_compact.csv")
    return run_ids


def count_lines(path: Path) -> int:
    """Count lines in a text file."""
    count = 0
    with path.open("r", encoding="utf-8") as handle:
        for _ in handle:
            count += 1
    return count


def main() -> None:
    """Run ranked surface audit and write outputs."""
    run_ids = read_success_runs(RUNS_PATH)

    missing_rows: List[Dict[str, str]] = []

    per_surface_counts: Dict[str, List[int]] = {s: [] for s in SURFACES}
    per_surface_missing: Dict[str, int] = {s: 0 for s in SURFACES}
    per_surface_zero: Dict[str, int] = {s: 0 for s in SURFACES}
    per_surface_underfilled: Dict[str, int] = {s: 0 for s in SURFACES}

    for run_id in run_ids:
        for surface in SURFACES:
            expected_path = RAW_DIR / f"{run_id}_{surface}_limit{EXPECTED_LIMIT}.jsonl"
            if not expected_path.exists():
                missing_rows.append(
                    {
                        "run_id_utc": run_id,
                        "surface": surface,
                        "expected_filename": expected_path.name,
                    }
                )
                per_surface_missing[surface] += 1
                continue

            row_count = 0
            if expected_path.stat().st_size > 0:
                row_count = count_lines(expected_path)
            else:
                row_count = 0

            per_surface_counts[surface].append(row_count)

            if row_count == 0:
                per_surface_zero[surface] += 1
            if row_count < EXPECTED_LIMIT:
                per_surface_underfilled[surface] += 1

    summary: Dict[str, Dict[str, float | int | None]] = {}
    for surface in SURFACES:
        counts = per_surface_counts[surface]
        runs_expected = len(run_ids)
        files_present = len(counts)
        files_missing = per_surface_missing[surface]

        if counts:
            row_min = min(counts)
            row_max = max(counts)
            row_median = statistics.median(counts)
        else:
            row_min = None
            row_max = None
            row_median = None

        summary[surface] = {
            "runs_expected": runs_expected,
            "files_present": files_present,
            "files_missing": files_missing,
            "row_count_min": row_min,
            "row_count_median": row_median,
            "row_count_max": row_max,
            "zero_row_files": per_surface_zero[surface],
            "underfilled_files": per_surface_underfilled[surface],
        }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    (OUTPUT_DIR / "ranked_surface_audit_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with (OUTPUT_DIR / "ranked_surface_missing_files.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        fieldnames = ["run_id_utc", "surface", "expected_filename"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in missing_rows:
            writer.writerow(row)

    # Console output
    print("Ranked surface audit summary")
    for surface in SURFACES:
        s = summary[surface]
        print(
            f"- {surface}: expected={s['runs_expected']} present={s['files_present']} "
            f"missing={s['files_missing']} min={s['row_count_min']} "
            f"median={s['row_count_median']} max={s['row_count_max']} "
            f"zero={s['zero_row_files']} underfilled={s['underfilled_files']}"
        )

    print(f"Missing files count: {len(missing_rows)}")


if __name__ == "__main__":
    main()
