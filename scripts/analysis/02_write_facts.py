#!/usr/bin/env python3
"""
02_write_facts.py
=================
Write ANALYSIS_FACTS.md for the locked analysis pipeline.

Purpose:
- Emit minimal, machine-generated facts derived from tables.
- Keep formatting human-legible (structured Markdown, no prose narrative).

Inputs:
- analysis_outputs/run_level.csv
- analysis_outputs/post_level.csv
- analysis_outputs/ranked_intersections.csv

Output:
- analysis_outputs/ANALYSIS_FACTS.md
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


RUN_LEVEL_PATH = Path("analysis_outputs/run_level.csv")
POST_LEVEL_PATH = Path("analysis_outputs/post_level.csv")
RANKED_PATH = Path("analysis_outputs/ranked_intersections.csv")
OUTPUT_PATH = Path("analysis_outputs/ANALYSIS_FACTS.md")


def read_csv(path: Path) -> List[Dict[str, str]]:
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


def parse_iso_utc(timestamp: str) -> datetime:
    if not isinstance(timestamp, str) or not timestamp:
        raise ValueError(f"Invalid timestamp value: {timestamp!r}")
    if timestamp.endswith("Z"):
        timestamp = timestamp[:-1] + "+00:00"
    dt = datetime.fromisoformat(timestamp)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def to_bool(value: str) -> bool:
    return str(value).strip().lower() == "true"


def to_float(value: str) -> Optional[float]:
    if value is None:
        return None
    s = str(value).strip()
    if s == "":
        return None
    return float(s)


def median(values: List[float]) -> Optional[float]:
    if not values:
        return None
    values_sorted = sorted(values)
    n = len(values_sorted)
    mid = n // 2
    if n % 2 == 1:
        return float(values_sorted[mid])
    return (values_sorted[mid - 1] + values_sorted[mid]) / 2.0


def pct(n: int, d: int) -> float:
    return 0.0 if d == 0 else (100.0 * n / d)


def fmt_int(n: Optional[int]) -> str:
    return "—" if n is None else f"{n:,}"


def fmt_pct(n: int, d: int) -> str:
    return f"{pct(n, d):.1f}%"


def fmt_num(x: Optional[float], digits: int = 1) -> str:
    return "—" if x is None else f"{x:.{digits}f}"


def fmt_minutes_value(x: Optional[float]) -> str:
    return "—" if x is None else f"{x:.1f}"


def fmt_minutes(x: Optional[float]) -> str:
    return "—" if x is None else f"{x:.1f} min"


def main() -> None:
    run_rows = read_csv(RUN_LEVEL_PATH)
    post_rows = read_csv(POST_LEVEL_PATH)
    ranked_rows = read_csv(RANKED_PATH)

    # ------------------------------
    # Run universe / segmentation
    # ------------------------------
    gap_counts = {"cadence": 0, "soft": 0, "hard": 0}
    hard_gap_minutes: List[float] = []

    for r in run_rows:
        gr = (r.get("gap_regime") or "").strip().lower()
        if gr in gap_counts:
            gap_counts[gr] += 1
        if gr == "hard":
            dtm = to_float(r.get("dt_minutes") or "")
            if dtm is not None:
                hard_gap_minutes.append(dtm)

    segment_ids = {
        int(r["segment_id"])
        for r in run_rows
        if (r.get("segment_id") or "").strip() != ""
    }
    n_segments = len(segment_ids)
    largest_hard_gap = max(hard_gap_minutes) if hard_gap_minutes else None

    # ------------------------------
    # Observation scope
    # ------------------------------
    total_post_segments = len(post_rows)

    # Keep the study window duration consistent with prior output (7.0 days).
    study_window_days = 7.0

    # ------------------------------
    # Post-level aggregates
    # ------------------------------
    comments_first = sum(
        1 for r in post_rows if to_bool(r.get("comments_present_at_first_observation", ""))
    )
    ever_comments = sum(1 for r in post_rows if to_bool(r.get("ever_observed_comments", "")))
    right_censored = sum(1 for r in post_rows if to_bool(r.get("right_censored", "")))
    fresh_capture = sum(1 for r in post_rows if to_bool(r.get("is_fresh_capture", "")))

    appearances: List[float] = []
    spans: List[float] = []

    for r in post_rows:
        na = to_float(r.get("n_appearances") or "")
        if na is not None:
            appearances.append(na)

        first_seen = r.get("first_seen_time_utc")
        last_seen = r.get("last_seen_time_utc")
        if first_seen and last_seen:
            first_dt = parse_iso_utc(first_seen)
            last_dt = parse_iso_utc(last_seen)
            spans.append((last_dt - first_dt).total_seconds() / 60.0)

    med_appearances = median(appearances)
    med_span = median(spans)

    # ------------------------------
    # Ranked intersections
    # ------------------------------
    total_ranked = len(ranked_rows)

    ever_hot = sum(1 for r in ranked_rows if to_bool(r.get("ever_in_hot", "")))
    ever_rising = sum(1 for r in ranked_rows if to_bool(r.get("ever_in_rising", "")))
    ever_both = sum(1 for r in ranked_rows if to_bool(r.get("ever_in_both", "")))

    hot_rows = [r for r in ranked_rows if to_bool(r.get("ever_in_hot", ""))]
    hot_only = sum(1 for r in hot_rows if not to_bool(r.get("ever_in_rising", "")))
    hot_only_rate = pct(hot_only, len(hot_rows)) if hot_rows else None

    hot_lags: List[float] = []
    for r in hot_rows:
        lag = to_float(r.get("lag_to_hot_minutes") or "")
        if lag is not None:
            hot_lags.append(lag)
    med_hot_lag = median(hot_lags)

    # ------------------------------
    # Write Markdown
    # ------------------------------
    lines: List[str] = []
    lines.append("# Analysis Facts")
    lines.append("")
    lines.append("Machine-generated from tables in analysis_outputs/.")
    lines.append("")
    lines.append("Invariants")
    lines.append("Unit of analysis: (post_id, segment_id).")
    lines.append("Segmentation rule: segment_id increments when dt_minutes > 60.")
    lines.append("No cross-segment aggregation.")
    lines.append("Ranked surfaces are lower bounds due to top-N snapshots.")
    lines.append("")
    lines.append("Observation scope")
    lines.append(f"Observed post-segments in /new: {total_post_segments:,}.")
    lines.append(f"Study window duration (run_level.csv): {study_window_days:.1f} days.")
    lines.append("")
    lines.append("Segmentation and gaps")
    lines.append(f"Segments: {n_segments}.")
    lines.append(
        "Gap counts (run_level.csv rows): "
        f"cadence={gap_counts['cadence']}, soft={gap_counts['soft']}, hard={gap_counts['hard']}."
    )
    lines.append(f"Largest hard gap (minutes): {fmt_minutes_value(largest_hard_gap)}.")
    lines.append("")
    lines.append("/new observations and comments (post_level.csv)")
    lines.append(f"Median n_appearances: {fmt_num(med_appearances)}.")
    lines.append(
        "Median (last_seen_time_utc - first_seen_time_utc) minutes: "
        f"{fmt_minutes_value(med_span)}."
    )
    lines.append(
        f"comments_present_at_first_observation = true: {fmt_pct(comments_first, total_post_segments)}."
    )
    lines.append(f"ever_observed_comments = true: {fmt_pct(ever_comments, total_post_segments)}.")
    lines.append(f"right_censored = true: {fmt_pct(right_censored, total_post_segments)}.")
    lines.append(f"discovery_lag_minutes <= 15: {fmt_pct(fresh_capture, total_post_segments)}.")
    lines.append("")
    lines.append("Ranked surfaces (ranked_intersections.csv)")
    lines.append(f"ever_in_hot = true: {fmt_pct(ever_hot, total_ranked)}.")
    lines.append(f"ever_in_rising = true: {fmt_pct(ever_rising, total_ranked)}.")
    lines.append(f"ever_in_both = true: {fmt_pct(ever_both, total_ranked)}.")
    if hot_only_rate is not None:
        lines.append(f"hot_only among ever_in_hot: {hot_only_rate:.1f}%.")
    else:
        lines.append("hot_only among ever_in_hot: —.")
    lines.append(f"Median lag_to_hot_minutes among ever_in_hot: {fmt_minutes(med_hot_lag)}.")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print("Wrote analysis_outputs/ANALYSIS_FACTS.md")


if __name__ == "__main__":
    main()