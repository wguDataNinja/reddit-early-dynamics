# Data Dictionary

This document describes the data artifacts produced during collection.

It documents observed structure, not inferred meaning.  
Public tables are derived deterministically from these raw artifacts.

---

## early_window_snapshots (raw)

Dense observations of posts captured from the `/new` listing.

Each row represents one post at a specific snapshot time.

### Grain
One row per `(post_id, snapshot_time)` while visible in `/new`.

### Source
Reddit API via `subreddit.new`, up to 1,000 posts per run.

### Core fields
- `id`  
  Submission id.
- `run_id_utc`  
  Run identifier.
- `surface`  
  Always `"new"`.

### Time fields
- `created_utc`  
  Submission creation time.
- `captured_utc`  
  Snapshot time.

### Engagement fields
- `score`
- `num_comments`
- `upvote_ratio`

### Notes
- Posts may appear across multiple runs.
- Observation ends when a post exits `/new`.

---

## visibility_surface_snapshots (raw)

Observations of posts appearing on ranked listing surfaces.

### Surfaces
- `hot`
- `rising`
- `controversial`

Each surface is sampled to the first page only, up to 100 posts.

### Grain
One row per `(post_id, surface, snapshot_time)`.

### Core fields
- `id`
- `run_id_utc`
- `surface`
- `surface_rank`

### Time fields
- `created_utc`
- `captured_utc`

### Engagement fields
- `score`
- `num_comments`
- `upvote_ratio`

### Notes
- Absence implies non-observation, not invisibility.
- Posts may appear on multiple surfaces in the same run.

---

## run_manifest

Append-only record of each scheduled run.

### Grain
One row per run attempt.

### Timing fields
- `run_id_utc`
- `run_started_utc`
- `run_finished_utc`
- `duration_seconds`

### Run status
- `run_skipped_flag`
- `run_skip_reason`

### API accounting
- Per-run totals  
- Skips  
- Misses  
- API call counts  

### Notes
- Skipped runs perform no API calls.
- This log is the authoritative record of run health.

---

## long_horizon_cohort (raw)

State events for posts selected for extended follow-up.

This dataset exists only if cohort tracking is enabled.

### Grain
One row per post state event.

### Core fields
- `post_id`
- `event_type`
- `event_utc`

### Cohort fields
- `recruitment_day`
- `cohort_bin`
- `first_observed_utc`
- `drop_from_new_utc`

### Notes
- Events are append-only.
- State is reconstructed by replaying events in order.
- Recruitment is deterministic and rule-based.

---

## Public tables

Public tables are derived from the raw artifacts above.

They:
- Exclude post text and usernames  
- Preserve observed structure  
- Introduce no new information  

Schemas are fixed after collection.