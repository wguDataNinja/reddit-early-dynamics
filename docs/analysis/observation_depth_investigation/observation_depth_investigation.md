# Observation Depth Investigation

This document investigates the observation-depth distribution shown in Figure 2
(“Observation depth in /new”).

The audit focuses on a large spike at `n_appearances = 1` (≈2× `n = 2`) and a
broad hump at `n ≈ 26–28`, and examines these features in isolation.

## Definitions

**Unit of analysis:** `(post_id, segment_id)`  
**n_appearances:** number of snapshots within a segment in which a post appears in `/new`  
**Segment:** uninterrupted collection period. Breaks occur at gaps > 60 minutes.  
**Right-censoring:** post remains visible at segment end; later lifetime is unobserved.  

**Cadence regimes:**
- `dt ≤ 20 minutes`: primary cadence
- `dt ≤ 60 minutes`: includes soft gaps

## Inputs

- `analysis_outputs/audit/study_window_runs_compact.csv`  
  Run inclusion and ordering

- `local/raw_jsonl/*_new_limit1000.jsonl`  
  Raw `/new` snapshots

- `analysis_outputs/post_level.csv`  
  Post-level metadata (including discovery lag)

---

## Step 0 — Recompute the target distribution

**Artifacts:**
- [`00_recomputed_observation_depth_distribution.csv`](00_recomputed_observation_depth_distribution.csv)
- [`00_post_segment_diff.csv`](00_post_segment_diff.csv)

**Result:**  
The recomputed distribution does not exactly match the figure.
A post-segment-level diff shows that a small fraction of rows differ,
all by −1 appearance.

The vast majority of differing rows are right-censored post-segments,
where the figure counts the terminal snapshot and the raw recomputation does not.

**Conclusion:**  
The mismatch is explained by boundary handling at segment ends and does not
affect downstream analysis or interpretation.

---

## Step 1 — Do gaps and segmentation create most `n = 1` posts?

**Artifacts:**
- [`01_gaps_over_60m.csv`](01_gaps_over_60m.csv)
- [`01_segment_n1_contrib_gap_filtered.csv`](01_segment_n1_contrib_gap_filtered.csv)

**Result:**  
Filtering out gap-adjacent runs reduces the singleton count but does not
eliminate it. The same segments continue to dominate `n = 1`.

**Conclusion:**  
Gaps contribute to `n = 1` but do not explain its magnitude.

---

## Step 2 — Does normal churn flush posts after one snapshot?

**Artifacts:**
- [`02_churn_pairs.csv`](02_churn_pairs.csv)
- [`02_churn_summary_dt_le_20.json`](02_churn_summary_dt_le_20.json)

**Result:**  
Median churn implies ~26 intervals to fully flush a 1,000-item listing under
normal cadence. The implied per-interval survival rate is high.

**Conclusion:**  
Observed churn alone is inconsistent with the `n = 1` spike.

---

## Step 3 — Are `n = 1` posts already old when first observed?

**Artifacts:**
- [`03_age_hist_by_n.csv`](03_age_hist_by_n.csv)

**Result:**  
Median age at first observation is similar for `n = 1` and `n ≥ 2`.
`n = 1` exhibits a long tail of very old posts.

**Conclusion:**  
Age alone does not explain most singletons, but identifies an old-post subgroup.

---

## Step 4 — What produces the hump at `n ≈ 26–28`?

**Artifacts:**
- [`04_span_hist_nge2.csv`](04_span_hist_nge2.csv)

**Result:**  
The modal visibility span corresponds to ~6–8 hours, consistent with
~24–32 snapshots at ~15-minute cadence.

**Conclusion:**  
The hump reflects typical lifetime in the `/new` queue.

---

## Step 5 — Is `n = 1` a mixture of top/young and deep/old posts?

**Artifacts:**
- [`05_rank_hist_compare.csv`](05_rank_hist_compare.csv)
- [`05_n1_rank_age_groups.csv`](05_n1_rank_age_groups.csv)

**Result:**  
Most `n = 1` posts are young and high-ranked at first observation.
A minority are deep-ranked and old.

**Conclusion:**  
The singleton mass is heterogeneous.

---

## Step 6 — Are deep + old singletons primarily gap artifacts?

**Artifacts:**
- [`06_deep_old_n1_by_segment.csv`](06_deep_old_n1_by_segment.csv)
- [`06_deep_old_n1_gap_attribution.json`](06_deep_old_n1_gap_attribution.json)

**Result:**  
Most deep + old singletons occur in segments that start after gaps > 60 minutes.

**Conclusion:**  
The majority of the old + deep subgroup is attributable to collection gaps.

---

## Summary

The observation-depth distribution reflects a mixture:

- Fast-loss fresh posts that disappear between snapshots
- Normal queue survivors with ~6–8 hour persistence (the hump at `n ≈ 26–28`)
- Late-seen gap artifacts (deep + old singletons)

Normal queue dynamics alone do not explain the full singleton spike.
