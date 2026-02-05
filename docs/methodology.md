# Methodology

This document describes the analysis pipeline and table definitions. It focuses on measurement mechanics.

## Run universe

- Source: `local/logs/phase2_run_manifest.jsonl`
- Roster: `analysis_outputs/audit/study_window_runs_compact.csv` (success-classified `run_id_utc` only)
- Inclusion: runs whose `run_id_utc` appears in the roster

The study window is fixed at seven days by design.

## Segmentation

- Hard gap threshold: 60.0 minutes
- `segment_id` increments when `dt_minutes > 60.0`
- No stitching across segments
- `gap_regime` values: cadence (`dt_minutes <= 20`), soft (`20 < dt_minutes <= 60`), hard (`dt_minutes > 60`)

## Unit of analysis

- Post-segment: `(post_id, segment_id)`
- One run = one observation opportunity

## Core tables

These tables are the sole inputs to all downstream analysis, figures, and summaries; no raw logs or snapshots are consumed beyond this point.

1. `run_level.csv`
- Derived from the manifest within the study window.

2. `post_level.csv`
- Aggregated from `/new` snapshots within segments.
- `n_appearances`: count of runs in the segment where the post appears in `/new`
- `comments_present_at_first_observation`: `num_comments > 0` at first appearance in the segment
- `ever_observed_comments`: any appearance has `num_comments > 0`
- `first_observed_nonzero_comments_obs_index`: 0-based index since first appearance where `num_comments > 0`
- `is_fresh_capture`: `discovery_lag_minutes <= 15`
- `right_censored`: last_seen_time_utc == segment end time

3. `ranked_intersections.csv`
- Links `/new` post-segments to observed appearances in `hot` and `rising`.
- Lower bound only, due to top-N snapshots.

## Censoring

- Right-censoring: post remains visible at segment end.
- Left-censoring: posts may have engagement prior to first observation (not directly observed).

## Output summary

- `analysis_outputs/ANALYSIS_FACTS.md` is generated from the produced tables only.
