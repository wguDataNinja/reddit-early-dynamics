# reddit-early-dynamics

This repository produces a minimal, audit-friendly description of early engagement visibility on Reddit using public listing snapshots. The analysis is strictly observational and designed to make observability limits explicit rather than model around them.

The study is scoped to r/AskReddit and measures what can be directly observed about posts as they first become visible in Reddit’s public listings.

The unit of analysis is the post-segment (`post_id`, `segment_id`), where segments are uninterrupted collection periods separated by hard gaps.

Tables figures and generated summaries are derived from the analysis tables. Investigation materials may read raw snapshots.

---

## Why this exists

Reddit’s public APIs expose no listing history and no impression data. As a result, analyses of engagement often condition on posts that persist, receive interaction, or enter ranked feeds, without bounding what was never observed. This project treats observability itself as the object of measurement, restricting claims to what can be seen under snapshot-based collection.

---

## Minimal analysis pipeline

scripts/analysis/00_build_tables.py  
scripts/analysis/01_ranked_intersections.py  
scripts/analysis/02_write_facts.py  

Outputs:

analysis_outputs/run_level.csv  
analysis_outputs/post_level.csv  
analysis_outputs/ranked_intersections.csv  
analysis_outputs/ANALYSIS_FACTS.md  

Each script is single-purpose. Downstream steps consume only the analysis tables produced upstream.

---

## What this measures

- Visibility of posts as observed in subreddit listing snapshots
- Repeated exposure in the chronological feed (`/new`)
- Lower-bound intersections with ranked listings (`/hot`, `/rising`)
- Timing of ranked appearances relative to first observation
- Effects of collection gaps via explicit segmentation

All measurements reflect what is observed, not total lifetime behavior.

---

## What this does not claim

- No causal claims
- No ranking-algorithm inference
- No impressions or exposure measurement
- No user-level tracking
- No stitching across hard gaps
- No prediction or optimization framing

Unobserved time is treated as non-inferable.

---

## Observed patterns

- Posts observed in `/new` typically remain visible across many consecutive snapshots within uninterrupted collection periods.
- Only a small minority of observed posts intersect with ranked listings; these intersections are lower bounds due to snapshot truncation.
- When ranked intersections occur, they are usually observed within one or two snapshot intervals of first appearance in `/new`.
- Many posts already have comments present at first observation.
- Collection gaps alter the composition of first-observed posts and require explicit segmentation.

Full results are described in [`docs/results.md`](docs/results.md).

---

## Key outputs

- analysis_outputs/run_level.csv  
  Run universe cadence gaps and segment boundaries.

- analysis_outputs/post_level.csv  
  Post-segment aggregates from `/new` observations within segments.

- analysis_outputs/ranked_intersections.csv  
  Observed intersections between `/new` post-segments and ranked surfaces.

- analysis_outputs/ANALYSIS_FACTS.md  
  A machine-generated summary derived solely from the analysis tables.

---

## Repository structure

analysis_outputs/  
Analysis tables and audit summaries used by the main analysis.

docs/  
Methodology dataset description results visuals and a targeted investigation.

scripts/  
Single-purpose analysis and audit scripts used to produce the tables above.

---

## Documentation

- [`docs/methodology.md`](docs/methodology.md) — measurement mechanics and table definitions  
- [`docs/dataset_description.md`](docs/dataset_description.md) — schema-level description of outputs  
- [`docs/results.md`](docs/results.md) — narrative interpretation  
- [`docs/visuals/`](docs/visuals/) — figures scripts and inspectable data  
- [`observation_depth_investigation.md`](docs/analysis/observation_depth_investigation/observation_depth_investigation.md) — investigation of the observation-depth distribution