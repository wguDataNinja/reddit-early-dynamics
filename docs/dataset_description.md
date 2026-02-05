# Dataset Description

## Overview

This repository exposes a small set of tables describing observed listing
visibility and comment presence using repeated snapshots.

The unit of analysis is the post as observed during uninterrupted
collection periods, grouped by `segment_id`.

Segmentation rules and gap handling are defined in `docs/methodology.md`.

Each run is treated as one observation opportunity.

---

## Tables

### 1. `run_level.csv`

**Purpose**  
Defines the run universe, collection cadence, and segmentation boundaries.

Each row corresponds to one collection run.

**Primary key**
- `run_id`

**Key columns**
- `run_id` — unique identifier for the run  
- `run_time_utc` — run start time (UTC)  
- `dt_minutes` — minutes since the previous run  
- `segment_id` — uninterrupted collection segment identifier  
- `run_index_in_segment` — run order within the segment  
- `gap_regime` — cadence / soft / hard (based on `dt_minutes`)

**Notes**
- Segmentation rules and gap handling are defined in `docs/methodology.md`.

---

### 2. `post_level.csv`

**Purpose**  
Aggregated properties of posts as observed in `/new` during uninterrupted
collection periods.

Each row represents a post observed at least once within a segment.

**Primary key**
- `(post_id, segment_id)`

**Key columns**
- `post_id` — Reddit post identifier  
- `segment_id` — collection segment in which the post was observed  
- `first_seen_time_utc` — first observation time  
- `last_seen_time_utc` — last observation time  
- `n_appearances` — number of snapshots in which the post appeared  
- `created_time_utc` — post creation time (UTC)  
- `discovery_lag_minutes` — lag from creation to first observation  
- `comments_present_at_first_observation` — whether comments were present at first observation  
- `ever_observed_comments` — whether comments were ever observed  
- `first_observed_nonzero_comments_obs_index` — snapshot index of first observed comment  
- `is_fresh_capture` — whether the post was first observed near creation  
- `right_censored` — whether the post was last seen at segment end  

**Notes**
- Ranked-surface rates are lower bounds. Other timing metrics are snapshot-based.
- Posts may exist outside observation windows and are not fully observed.

---

### 3. `ranked_intersections.csv`

**Purpose**  
Observed intersections between posts seen in `/new` and ranked listing
surfaces (`/hot`, `/rising`).

**Primary key**
- `(post_id, segment_id)`

**Key columns**
- `ever_in_hot` — whether the post was observed in `/hot`  
- `ever_in_rising` — whether the post was observed in `/rising`  
- `ever_in_both` — whether the post was observed in both  
- `first_in_hot` — first `/hot` observation time  
- `first_in_rising` — first `/rising` observation time  
- `lag_to_hot_minutes` — lag from first `/new` observation to `/hot`  
- `lag_to_rising_minutes` — lag from first `/new` observation to `/rising`  
- `ranked_top_n` — snapshot depth used (top-N)

**Notes**
- Ranked intersections are lower bounds due to top-N truncation.
- Absence may reflect snapshot coverage limits.

---

### 4. `ANALYSIS_FACTS.md`

**Purpose**  
A generated summary of key counts and rates derived directly from the
tables above.

**Notes**
- Contains no interpretation or narrative.
- Serves as a stable reference for results and visuals.

---

## General Constraints

- Unobserved time is treated as non-inferable.
- No cross-segment aggregation is permitted.
- All findings are descriptive and non-causal.
- Results apply only to posts observed at least once during collection.
