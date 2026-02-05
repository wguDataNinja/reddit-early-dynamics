# Visuals — Early Engagement Dynamics

This directory contains figures used to interpret the **Reddit Early Engagement Dynamics** study, along with the scripts and inspectable data used to generate them.

All figures are **descriptive and non-causal**. Their purpose is to make the collection process, coverage gaps, and structural limits of Reddit listing surfaces visible and understandable.

---

## Figure 1 — Collection coverage and gaps

- **Image:** [`figure_1_collection_coverage.png`](figure_1_collection_coverage.png)  
- **Script:** [`figure_1_collection_coverage.py`](figure_1_collection_coverage.py)  
- **Data:** [`data/collection_timeline_segments_data.csv`](data/collection_timeline_segments_data.csv)

**What this figure shows**  
A timeline of successful collection runs across the study window. Each
vertical tick represents a completed run. Shaded regions indicate
**hard gaps** (>60 minutes) where no data was collected. Brackets mark
uninterrupted collection periods.

**How to read it**  
Dense ticks indicate regular collection. Shaded regions are unobserved
time. Brackets group runs that can be analyzed without assuming
continuity across gaps.

**What it means**  
This figure establishes the actual coverage of the dataset. Gaps are
explicit and visible, and analysis is restricted to uninterrupted
periods to avoid inferring activity during unobserved time.

---

## Figure 2 — Observation depth in `/new`

- **Image:** [`figure_2_observation_depth.png`](figure_2_observation_depth.png)  
- **Script:** [`figure_2_observation_depth.py`](figure_2_observation_depth.py)  
- **Data:**  
  - [`data/observation_depth_distribution_freq.csv`](data/observation_depth_distribution_freq.csv)  
  - [`data/observation_depth_distribution_summary.csv`](data/observation_depth_distribution_summary.csv)

**What this figure shows**  
How many times an observed post appears in `/new` during uninterrupted
collection periods.

**How to read it**  
Higher values mean a post remained visible across multiple snapshots.

**What it means**  
Posts observed exactly once reflect a mixture of fast-disappearing posts and gap-adjacent observations, rather than normal queue churn alone.
Limited engagement cannot typically be explained by lack of `/new` exposure alone.

---

## Figure 3 — Ranked surface scarcity

- **Image:** [`figure_3_ranked_surface_scarcity.png`](figure_3_ranked_surface_scarcity.png)  
- **Script:** [`figure_3_ranked_surface_scarcity.py`](figure_3_ranked_surface_scarcity.py)  
- **Data:** [`data/ranked_intersection_rates.csv`](data/ranked_intersection_rates.csv)

**What this figure shows**  
The fraction of observed posts that ever appear in ranked listings
(`/hot`, `/rising`), based on top-100 snapshots.

**How to read it**  
Bars show lower-bound intersection rates between `/new` and ranked
listings.

**What it means**  
Ranked listings are structurally scarce. They represent selective
attention surfaces rather than extensions of chronological listings.
These rates describe platform structure, not post quality or outcomes.

---

## Figure 4 — Cadence to `/hot`

- **Image:** [`figure_4_lag_to_hot.png`](figure_4_lag_to_hot.png)  
- **Script:** [`figure_4_lag_to_hot.py`](figure_4_lag_to_hot.py)  
- **Data:**  
  - [`data/lag_to_hot_hist_1min.csv`](data/lag_to_hot_hist_1min.csv)  
  - [`data/lag_to_hot_summary.csv`](data/lag_to_hot_summary.csv)

**What this figure shows**  
How many snapshot intervals pass between first observation in `/new`
and first observation in `/hot`, among posts that reach `/hot`.
Each interval is approximately 15 minutes.

**How to read it**  
Bars represent discrete snapshot steps. Most promotions occur quickly,
with a small tail of later promotion.

**What it means**  
When ranked promotion happens, it usually happens early. Delayed
promotion exists but is uncommon among posts that reach `/hot`.

---

## Notes on scope and interpretation

- All figures refer to **posts as observed** during uninterrupted
  collection periods.
- Unobserved time is treated as unknowable.
- All rates and timings are **lower bounds** due to snapshot-based
  observation.
- No figure implies causation, optimization strategies, or fairness
  judgments.
