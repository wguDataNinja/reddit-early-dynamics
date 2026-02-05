#!/usr/bin/env python3
"""
Observation depth investigation (Figure 2 support only).

This script reproduces the retained observation-depth investigation artifacts from:
- analysis_outputs/audit/study_window_runs_compact.csv
- local/raw_jsonl/{run_id}_new_limit1000.jsonl
- analysis_outputs/post_level.csv

Outputs are written only to:
docs/analysis/observation_depth_investigation/
"""

from __future__ import annotations

import csv
import json
import random
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean, median


REPO_ROOT = Path(__file__).resolve().parents[2]
ROSTER_PATH = REPO_ROOT / "analysis_outputs" / "audit" / "study_window_runs_compact.csv"
POST_LEVEL_PATH = REPO_ROOT / "analysis_outputs" / "post_level.csv"
RAW_DIR = REPO_ROOT / "local" / "raw_jsonl"
OUTPUT_DIR = REPO_ROOT / "docs" / "analysis" / "observation_depth_investigation"

ALLOWED_OUTPUTS = {
    "00_recomputed_observation_depth_distribution.csv",
    "00_post_segment_diff.csv",
    "01_gaps_over_60m.csv",
    "01_segment_n1_contrib_gap_filtered.csv",
    "02_churn_pairs.csv",
    "02_churn_summary_dt_le_20.json",
    "03_age_hist_by_n.csv",
    "04_span_hist_nge2.csv",
    "05_rank_hist_compare.csv",
    "05_n1_rank_age_groups.csv",
    "06_deep_old_n1_by_segment.csv",
    "06_deep_old_n1_gap_attribution.json",
    "observation_depth_investigation.md",
}


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def summary_stats(values: list[float]) -> dict | None:
    if not values:
        return None
    ordered = sorted(values)

    def pct(p: float) -> float:
        return ordered[int(p * (len(ordered) - 1))]

    return {
        "count": len(ordered),
        "mean": mean(ordered),
        "median": pct(0.5),
        "p10": pct(0.1),
        "p90": pct(0.9),
        "min": ordered[0],
        "max": ordered[-1],
    }


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def ensure_output_dir_clean() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for entry in OUTPUT_DIR.iterdir():
        if entry.is_file() and entry.name not in ALLOWED_OUTPUTS:
            entry.unlink()


def load_runs() -> list[dict]:
    runs: list[dict] = []
    with ROSTER_PATH.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row.get("classification") != "success":
                continue
            run_id = row["run_id_utc"]
            run_started = row["run_started_utc"]
            new_path = RAW_DIR / f"{run_id}_new_limit1000.jsonl"
            if not new_path.exists():
                continue
            runs.append(
                {
                    "run_id": run_id,
                    "run_started_utc": run_started,
                    "new_path": new_path,
                }
            )

    runs.sort(key=lambda r: r["run_started_utc"])

    segment_id = 0
    prev_time: str | None = None
    for run in runs:
        if prev_time is None:
            run["dt_minutes"] = None
        else:
            dt = (parse_ts(run["run_started_utc"]) - parse_ts(prev_time)).total_seconds() / 60.0
            run["dt_minutes"] = dt
            if dt > 60:
                segment_id += 1
        run["segment_id"] = str(segment_id)
        prev_time = run["run_started_utc"]
    return runs


def load_snapshot_cache(runs: list[dict]) -> tuple[dict[str, set[str]], dict[str, dict[str, int]]]:
    ids_by_run: dict[str, set[str]] = {}
    rank_by_run: dict[str, dict[str, int]] = {}
    for run in runs:
        run_id = run["run_id"]
        ids_set: set[str] = set()
        rank_map: dict[str, int] = {}
        with run["new_path"].open("r", encoding="utf-8") as handle:
            rank = 1
            for line in handle:
                if not line.strip():
                    continue
                obj = json.loads(line)
                post_id = obj.get("id")
                if post_id is None:
                    rank += 1
                    continue
                ids_set.add(post_id)
                if post_id not in rank_map:
                    rank_map[post_id] = rank
                rank += 1
        ids_by_run[run_id] = ids_set
        rank_by_run[run_id] = rank_map
    return ids_by_run, rank_by_run


def build_raw_counts(runs: list[dict], ids_by_run: dict[str, set[str]]) -> dict[tuple[str, str], int]:
    counts: dict[tuple[str, str], int] = defaultdict(int)
    for run in runs:
        seg = run["segment_id"]
        for post_id in ids_by_run[run["run_id"]]:
            counts[(post_id, seg)] += 1
    return counts


def main() -> None:
    ensure_output_dir_clean()
    runs = load_runs()
    ids_by_run, rank_by_run = load_snapshot_cache(runs)
    raw_counts = build_raw_counts(runs, ids_by_run)

    # Step 0a: recomputed observation depth distribution
    depth_dist = Counter(raw_counts.values())
    dist_rows = [{"n_appearances": n, "count": depth_dist[n]} for n in sorted(depth_dist)]
    write_csv(
        OUTPUT_DIR / "00_recomputed_observation_depth_distribution.csv",
        ["n_appearances", "count"],
        dist_rows,
    )

    # Step 0b: post-segment diff vs post_level.csv
    post_level_rows: dict[tuple[str, str], dict] = {}
    with POST_LEVEL_PATH.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            key = (row["post_id"], row["segment_id"])
            post_level_rows[key] = row

    diff_rows: list[dict] = []
    for post_id, segment_id in sorted(set(raw_counts.keys()) | set(post_level_rows.keys())):
        raw_n = raw_counts.get((post_id, segment_id))
        post_row = post_level_rows.get((post_id, segment_id))
        post_n = int(float(post_row["n_appearances"])) if post_row else None
        status = "match"
        delta = None
        if raw_n is None:
            status = "missing_raw"
        elif post_n is None:
            status = "missing_post_level"
        else:
            delta = raw_n - post_n
            if delta != 0:
                status = "delta"
        diff_rows.append(
            {
                "post_id": post_id,
                "segment_id": segment_id,
                "n_appearances_raw": raw_n,
                "n_appearances_post_level": post_n,
                "delta_raw_minus_post": delta,
                "status": status,
            }
        )
    write_csv(
        OUTPUT_DIR / "00_post_segment_diff.csv",
        [
            "post_id",
            "segment_id",
            "n_appearances_raw",
            "n_appearances_post_level",
            "delta_raw_minus_post",
            "status",
        ],
        diff_rows,
    )

    # Step 1: gaps + gap-adjacent filtered segment n1 contribution
    gap_rows: list[dict] = []
    exclude_run_ids: set[str] = set()
    segments_started_after_gap: set[str] = set()
    for i in range(1, len(runs)):
        dt = runs[i]["dt_minutes"]
        if dt is not None and dt > 60:
            gap_rows.append(
                {
                    "gap_start_run_id": runs[i - 1]["run_id"],
                    "gap_start_time_utc": runs[i - 1]["run_started_utc"],
                    "gap_end_run_id": runs[i]["run_id"],
                    "gap_end_time_utc": runs[i]["run_started_utc"],
                    "gap_minutes": dt,
                    "segment_id_started": runs[i]["segment_id"],
                }
            )
            exclude_run_ids.add(runs[i - 1]["run_id"])
            exclude_run_ids.add(runs[i]["run_id"])
            segments_started_after_gap.add(runs[i]["segment_id"])
    write_csv(
        OUTPUT_DIR / "01_gaps_over_60m.csv",
        [
            "gap_start_run_id",
            "gap_start_time_utc",
            "gap_end_run_id",
            "gap_end_time_utc",
            "gap_minutes",
            "segment_id_started",
        ],
        gap_rows,
    )

    filtered_counts: dict[tuple[str, str], int] = defaultdict(int)
    segment_snapshot_counts: dict[str, int] = defaultdict(int)
    for run in runs:
        run_id = run["run_id"]
        if run_id in exclude_run_ids:
            continue
        seg = run["segment_id"]
        segment_snapshot_counts[seg] += 1
        for post_id in ids_by_run[run_id]:
            filtered_counts[(post_id, seg)] += 1

    n1_by_segment = defaultdict(int)
    for (post_id, seg), n in filtered_counts.items():
        if n == 1:
            n1_by_segment[seg] += 1

    seg_rows: list[dict] = []
    for seg in sorted(segment_snapshot_counts, key=lambda s: int(s)):
        snapshots = segment_snapshot_counts[seg]
        n1_count = n1_by_segment.get(seg, 0)
        seg_rows.append(
            {
                "segment_id": seg,
                "n1_count": n1_count,
                "num_snapshots": snapshots,
                "n1_per_snapshot": (n1_count / snapshots) if snapshots else None,
            }
        )
    seg_rows.sort(key=lambda r: (-r["n1_count"], int(r["segment_id"])))
    write_csv(
        OUTPUT_DIR / "01_segment_n1_contrib_gap_filtered.csv",
        ["segment_id", "n1_count", "num_snapshots", "n1_per_snapshot"],
        seg_rows,
    )

    # Step 2: churn
    churn_rows: list[dict] = []
    for i in range(len(runs) - 1):
        left = runs[i]
        right = runs[i + 1]
        s_t = ids_by_run[left["run_id"]]
        s_t1 = ids_by_run[right["run_id"]]
        survivors = len(s_t & s_t1)
        churn_rows.append(
            {
                "run_id_t": left["run_id"],
                "run_id_t1": right["run_id"],
                "run_time_t": left["run_started_utc"],
                "run_time_t1": right["run_started_utc"],
                "dt_minutes": right["dt_minutes"],
                "new_posts": len(s_t1 - s_t),
                "dropped": len(s_t - s_t1),
                "survivors": survivors,
                "survival_rate": (survivors / len(s_t)) if s_t else None,
            }
        )
    write_csv(
        OUTPUT_DIR / "02_churn_pairs.csv",
        [
            "run_id_t",
            "run_id_t1",
            "run_time_t",
            "run_time_t1",
            "dt_minutes",
            "new_posts",
            "dropped",
            "survivors",
            "survival_rate",
        ],
        churn_rows,
    )

    dt20_rows = [r for r in churn_rows if r["dt_minutes"] is not None and r["dt_minutes"] <= 20]
    churn_dt20 = {
        "new_posts": summary_stats([r["new_posts"] for r in dt20_rows]),
        "dropped": summary_stats([r["dropped"] for r in dt20_rows]),
        "survivors": summary_stats([r["survivors"] for r in dt20_rows]),
        "survival_rate": summary_stats([r["survival_rate"] for r in dt20_rows if r["survival_rate"] is not None]),
    }
    with (OUTPUT_DIR / "02_churn_summary_dt_le_20.json").open("w", encoding="utf-8") as handle:
        json.dump(churn_dt20, handle, indent=2)

    # Load post_level once for remaining steps
    post_rows: list[dict] = []
    with POST_LEVEL_PATH.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            post_rows.append(row)

    # Step 3: age histogram by n group
    age_bins = [
        ("0-15m", 0, 15),
        ("15-30m", 15, 30),
        ("30-60m", 30, 60),
        ("1-2h", 60, 120),
        ("2-4h", 120, 240),
        ("4-8h", 240, 480),
        ("8-12h", 480, 720),
        ("12-24h", 720, 1440),
        ("1-2d", 1440, 2880),
        ("2-7d", 2880, 10080),
        ("7-30d", 10080, 43200),
        ("30-90d", 43200, 129600),
        ("90-365d", 129600, 525600),
        (">1y", 525600, None),
    ]

    ages_n1: list[float] = []
    ages_nge2: list[float] = []
    for row in post_rows:
        n = int(row["n_appearances"])
        lag = row.get("discovery_lag_minutes")
        if lag is None or lag == "":
            continue
        age = float(lag)
        if n == 1:
            ages_n1.append(age)
        else:
            ages_nge2.append(age)

    age_hist_rows: list[dict] = []
    for label, low, high in age_bins:
        count_n1 = 0
        count_nge2 = 0
        for v in ages_n1:
            if (high is None and v >= low) or (high is not None and low <= v < high):
                count_n1 += 1
        for v in ages_nge2:
            if (high is None and v >= low) or (high is not None and low <= v < high):
                count_nge2 += 1
        age_hist_rows.append(
            {
                "bin_label": label,
                "bin_start_min": low,
                "bin_end_min": "" if high is None else high,
                "count_n1": count_n1,
                "count_nge2": count_nge2,
            }
        )
    write_csv(
        OUTPUT_DIR / "03_age_hist_by_n.csv",
        ["bin_label", "bin_start_min", "bin_end_min", "count_n1", "count_nge2"],
        age_hist_rows,
    )

    # Step 4: span histogram for n>=2
    span_bins = [
        ("0-15m", 0, 15),
        ("15-30m", 15, 30),
        ("30-60m", 30, 60),
        ("1-2h", 60, 120),
        ("2-4h", 120, 240),
        ("4-6h", 240, 360),
        ("6-8h", 360, 480),
        ("8-12h", 480, 720),
        ("12-24h", 720, 1440),
        (">24h", 1440, None),
    ]

    spans_nge2: list[float] = []
    for row in post_rows:
        n = int(row["n_appearances"])
        if n < 2:
            continue
        first_seen = parse_ts(row["first_seen_time_utc"])
        last_seen = parse_ts(row["last_seen_time_utc"])
        spans_nge2.append((last_seen - first_seen).total_seconds() / 60.0)

    span_hist_rows: list[dict] = []
    for label, low, high in span_bins:
        count = 0
        for v in spans_nge2:
            if (high is None and v >= low) or (high is not None and low <= v < high):
                count += 1
        span_hist_rows.append(
            {
                "bin_label": label,
                "bin_start_min": low,
                "bin_end_min": "" if high is None else high,
                "count": count,
            }
        )
    write_csv(
        OUTPUT_DIR / "04_span_hist_nge2.csv",
        ["bin_label", "bin_start_min", "bin_end_min", "count"],
        span_hist_rows,
    )

    # Step 5: rank mixture (n1 vs sampled n>=2)
    run_time_to_run = {run["run_started_utc"]: run for run in runs}
    n1_rows: list[dict] = []
    nge2_rows: list[dict] = []
    for row in post_rows:
        item = {
            "post_id": row["post_id"],
            "segment_id": row["segment_id"],
            "first_seen_time_utc": row["first_seen_time_utc"],
            "age_at_first_seen_minutes": float(row["discovery_lag_minutes"])
            if row.get("discovery_lag_minutes") not in (None, "")
            else None,
        }
        if int(row["n_appearances"]) == 1:
            n1_rows.append(item)
        else:
            nge2_rows.append(item)

    rng = random.Random(42)
    sample_size = min(len(n1_rows), len(nge2_rows))
    nge2_sample = rng.sample(nge2_rows, sample_size)

    def rank_for(item: dict) -> int | None:
        run = run_time_to_run.get(item["first_seen_time_utc"])
        if run is None:
            return None
        return rank_by_run[run["run_id"]].get(item["post_id"])

    n1_ranks: list[int] = []
    n1_top_ages: list[float] = []
    n1_deep_ages: list[float] = []
    for row in n1_rows:
        rank = rank_for(row)
        if rank is None:
            continue
        n1_ranks.append(rank)
        age = row["age_at_first_seen_minutes"]
        if age is None:
            continue
        if rank < 750:
            n1_top_ages.append(age)
        else:
            n1_deep_ages.append(age)

    nge2_ranks: list[int] = []
    for row in nge2_sample:
        rank = rank_for(row)
        if rank is not None:
            nge2_ranks.append(rank)

    rank_bins = [
        ("1-50", 1, 51),
        ("51-100", 51, 101),
        ("101-200", 101, 201),
        ("201-300", 201, 301),
        ("301-400", 301, 401),
        ("401-500", 401, 501),
        ("501-750", 501, 751),
        ("751-1000", 751, 1001),
        (">1000", 1001, None),
    ]

    def count_bins(values: list[int]) -> dict[str, int]:
        out = {label: 0 for label, _, _ in rank_bins}
        for v in values:
            for label, low, high in rank_bins:
                if high is None:
                    if v >= low:
                        out[label] += 1
                        break
                elif low <= v < high:
                    out[label] += 1
                    break
        return out

    n1_bin_counts = count_bins(n1_ranks)
    nge2_bin_counts = count_bins(nge2_ranks)
    rank_hist_rows: list[dict] = []
    for label, low, high in rank_bins:
        rank_hist_rows.append(
            {
                "bin_label": label,
                "bin_start": low,
                "bin_end": "" if high is None else high - 1,
                "count_n1": n1_bin_counts[label],
                "count_nge2_sample": nge2_bin_counts[label],
            }
        )
    write_csv(
        OUTPUT_DIR / "05_rank_hist_compare.csv",
        ["bin_label", "bin_start", "bin_end", "count_n1", "count_nge2_sample"],
        rank_hist_rows,
    )

    n1_group_rows = [
        {
            "rank_group": "top",
            "count": len(n1_top_ages),
            "mean_age": mean(n1_top_ages) if n1_top_ages else None,
            "median_age": median(n1_top_ages) if n1_top_ages else None,
        },
        {
            "rank_group": "deep",
            "count": len(n1_deep_ages),
            "mean_age": mean(n1_deep_ages) if n1_deep_ages else None,
            "median_age": median(n1_deep_ages) if n1_deep_ages else None,
        },
    ]
    write_csv(
        OUTPUT_DIR / "05_n1_rank_age_groups.csv",
        ["rank_group", "count", "mean_age", "median_age"],
        n1_group_rows,
    )

    # Step 6: deep+old n1 attribution to gap-started segments
    deep_old_rows: list[dict] = []
    for row in n1_rows:
        age = row["age_at_first_seen_minutes"]
        if age is None or age <= 400:
            continue
        rank = rank_for(row)
        if rank is None or rank < 750:
            continue
        seg = row["segment_id"]
        deep_old_rows.append(
            {
                "post_id": row["post_id"],
                "segment_id": seg,
                "first_seen_time_utc": row["first_seen_time_utc"],
                "rank_in_new": rank,
                "age_minutes": age,
                "segment_after_gap_gt60": seg in segments_started_after_gap,
            }
        )
    write_csv(
        OUTPUT_DIR / "06_deep_old_n1_by_segment.csv",
        ["post_id", "segment_id", "first_seen_time_utc", "rank_in_new", "age_minutes", "segment_after_gap_gt60"],
        deep_old_rows,
    )

    total_deep_old = len(deep_old_rows)
    count_after_gap = sum(1 for row in deep_old_rows if row["segment_after_gap_gt60"])
    by_segment = Counter(row["segment_id"] for row in deep_old_rows)
    step6_summary = {
        "total_rows": total_deep_old,
        "count_after_gap": count_after_gap,
        "count_not_after_gap": total_deep_old - count_after_gap,
        "fraction_after_gap": (count_after_gap / total_deep_old) if total_deep_old else None,
        "counts_by_segment": dict(sorted(by_segment.items(), key=lambda kv: int(kv[0]))),
    }
    with (OUTPUT_DIR / "06_deep_old_n1_gap_attribution.json").open("w", encoding="utf-8") as handle:
        json.dump(step6_summary, handle, indent=2)

    # README: retained artifacts only
    n1_count = depth_dist.get(1, 0)
    n2_count = depth_dist.get(2, 0)
    actual_n1_n2_ratio = (n1_count / n2_count) if n2_count else None
    s_median = churn_dt20["survival_rate"]["median"] if churn_dt20["survival_rate"] else None
    expected_n1_n2_ratio = (1 / s_median) if s_median else None
    factor = (actual_n1_n2_ratio / expected_n1_n2_ratio) if expected_n1_n2_ratio else None
    flush_intervals = (1000 / churn_dt20["new_posts"]["median"]) if churn_dt20["new_posts"] else None

    readme_lines = [
        "# Observation Depth Investigation",
        "",
        "This directory contains the retained, canonical observation-depth investigation artifacts supporting Figure 2.",
        "All outputs are generated by `scripts/audit/observation_depth_investigation.py` from:",
        "- `analysis_outputs/audit/study_window_runs_compact.csv`",
        "- `local/raw_jsonl/{run_id}_new_limit1000.jsonl`",
        "- `analysis_outputs/post_level.csv`",
        "",
        "Segmentation rule: start a new segment when `dt_minutes > 60`.",
        "",
        "## Retained Outputs",
        "- `00_recomputed_observation_depth_distribution.csv`",
        "- `00_post_segment_diff.csv`",
        "- `01_gaps_over_60m.csv`",
        "- `01_segment_n1_contrib_gap_filtered.csv`",
        "- `02_churn_pairs.csv`",
        "- `02_churn_summary_dt_le_20.json`",
        "- `03_age_hist_by_n.csv`",
        "- `04_span_hist_nge2.csv`",
        "- `05_rank_hist_compare.csv`",
        "- `05_n1_rank_age_groups.csv`",
        "- `06_deep_old_n1_by_segment.csv`",
        "- `06_deep_old_n1_gap_attribution.json`",
        "",
        "## Provenance Notes",
        "- Step-2 primary churn estimates use `dt<=20` from `02_churn_summary_dt_le_20.json`.",
        f"- Derived from `02_churn_summary_dt_le_20.json`: expected_intervals_to_flush_1000 = {flush_intervals}.",
        f"- Derived from `02_churn_summary_dt_le_20.json`: survival median S = {s_median}.",
        f"- Derived from `00_recomputed_observation_depth_distribution.csv`: n1_count = {n1_count}, n2_count = {n2_count}, actual n1/n2 = {actual_n1_n2_ratio}.",
        f"- Derived from both files: expected n1/n2 = 1/S = {expected_n1_n2_ratio}, difference factor = {factor}.",
        "",
        "No other artifacts are emitted by this audit script.",
        "",
    ]
    (OUTPUT_DIR / "observation_depth_investigation.md").write_text("\n".join(readme_lines), encoding="utf-8")

    print(f"Wrote retained outputs to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
