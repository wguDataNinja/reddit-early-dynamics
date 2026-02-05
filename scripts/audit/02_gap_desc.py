"""
Gap ranking audit for study window.

Purpose:
- Sort study window gaps by duration (descending).
- Emit a compact, human-readable CSV for inspection.

Inputs:
- analysis_outputs/audit/study_window_gaps.csv

Outputs (analysis_outputs/audit/):
- study_window_gaps_desc.csv

Non-goals:
- No attribution or cause analysis.
- No external log parsing.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List


GAPS_PATH = Path("analysis_outputs/audit/study_window_gaps.csv")
OUTPUT_DIR = Path("analysis_outputs/audit")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Rank study window gaps by duration.")
    parser.add_argument(
        "--top-n",
        type=int,
        default=50,
        help="Number of top gaps to print to console (default: 50).",
    )
    return parser.parse_args()


def load_gaps(path: Path) -> List[Dict[str, str]]:
    """Load gaps from CSV."""
    if not path.exists():
        raise FileNotFoundError(f"Missing gaps file: {path}")
    rows: List[Dict[str, str]] = []
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(row)
    if not rows:
        raise ValueError("Gaps file is empty")
    return rows


def main() -> None:
    """Run the gap ranking and write outputs."""
    args = parse_args()

    gaps = load_gaps(GAPS_PATH)
    gap_rows = []
    for row in gaps:
        try:
            gap_minutes = float(row["gap_minutes"])
        except Exception as exc:
            raise ValueError(f"Invalid gap_minutes: {row.get('gap_minutes')}") from exc
        gap_rows.append(
            {
                "gap_minutes": gap_minutes,
                "prev_run_started_utc": row["prev_run_started_utc"],
                "next_run_started_utc": row["next_run_started_utc"],
            }
        )

    gap_rows.sort(key=lambda r: r["gap_minutes"], reverse=True)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = OUTPUT_DIR / "study_window_gaps_desc.csv"
    with out_csv.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = [
            "rank",
            "gap_minutes",
            "prev_run_started_utc",
            "next_run_started_utc",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for rank, row in enumerate(gap_rows, start=1):
            writer.writerow(
                {
                    "rank": str(rank),
                    "gap_minutes": f"{row['gap_minutes']:.6f}",
                    "prev_run_started_utc": row["prev_run_started_utc"],
                    "next_run_started_utc": row["next_run_started_utc"],
                }
            )

    print("rank,gap_minutes,prev_run_started_utc,next_run_started_utc")
    for rank, row in enumerate(gap_rows[: max(0, args.top_n)], start=1):
        print(
            f"{rank},"
            f"{row['gap_minutes']:.6f},"
            f"{row['prev_run_started_utc']},"
            f"{row['next_run_started_utc']}"
        )


if __name__ == "__main__":
    main()
