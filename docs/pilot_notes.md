# Pilot Observability Notes

This document records observations from the pilot collection.

Its purpose is to establish what can be observed through subreddit listing endpoints, for how long, and with what stability.  
All statements describe observed properties of the pilot data only.

No analysis or interpretation is performed.

---

## Pilot setup

- Subreddit: r/AskReddit  
- Listing surfaces:
  - `new`
  - `hot`
  - `rising`
  - `controversial`
- Execution: manual runs  
- Code state: unchanged across runs  
- Environment: local execution using authorized credentials  
- Runtime per run: ~10–14 seconds  
- Output: raw JSONL files, local only  

Paging depth used in pilot:
- `/new`: up to 1,000  
- `hot`: 50  
- `rising`: 50  
- `controversial`: 50  

---

## Runs executed

Six pilot runs were executed during a high-activity period.

Run identifiers (UTC):
- 20260105_233930  
- 20260106_000029  
- 20260106_002506  
- 20260106_010039  
- 20260106_020050  
- 20260106_035233  

Each run produced four files, one per surface.

Total pilot files: 24 JSONL files.

No partial runs occurred.  
No surfaces were missing.

---

## Row counts per surface

Typical observed counts per run:
- `/new`: 984–992  
- `hot`: 50  
- `controversial`: 50  
- `rising`: 25–26  

Notes:
- `/new` consistently returned just under the requested limit.
- `hot` and `controversial` consistently returned a full first page.
- `rising` consistently underfilled relative to the requested limit.
- No empty files were observed.

---

## Snapshot timing within runs

Within a single run:
- All four surfaces were captured within a narrow time window.
- Time between first and last snapshot ranged from ~7.6 to ~9.9 seconds.

Surfaces within a run can be treated as effectively simultaneous snapshots.

---

## Time gaps between runs

Observed gaps between consecutive runs:
- ~21.0 minutes  
- ~24.6 minutes  
- ~35.5 minutes  
- ~60.2 minutes  
- ~111.7 minutes  

The intended one-hour cadence was not enforced.  
Irregular spacing is recorded as an operational observation.

---

## Schema stability

Observed behavior:
- Required fields were present in all files.
- No required fields disappeared between runs or surfaces.
- One optional field (`author_cakeday`) appeared intermittently.

Surface rank behavior:
- `surface_rank` is null for `/new`.
- `surface_rank` is present for ranked surfaces.

Schema behavior was stable across the pilot.

---

## `/new` observability

Aggregate across all pilot runs:
- Total `/new` rows: 5,923  
- Unique posts observed: 1,585  

Post age at observation:
- Minimum: ~0.003 hours  
- Median: ~3.36 hours  
- 90th percentile: ~5.88 hours  
- Maximum: ~7.19 hours  

Snapshots per post:
- Minimum: 1  
- Median: 4  
- Maximum: 6  

Observed span per post:
- Minimum: 0 minutes  
- Median: ~141 minutes  
- Maximum: ~253 minutes  

Posts persist in `/new` long enough to be observed multiple times.

---

## Overlap between `/new` pulls

Overlap between consecutive `/new` snapshots:

- ~21 min gap: ~95.15%  
- ~24.6 min gap: ~94.22%  
- ~35.5 min gap: ~91.29%  
- ~60.2 min gap: ~84.55%  
- ~111.7 min gap: ~74.49%  

Overlap declines gradually as time between pulls increases.

---

## Ranked listing behavior

Observed behavior:
- `hot` consistently returns a full first page.
- `controversial` consistently returns a full first page.
- `rising` consistently underfills.

Overlap between ranked listings and `/new` was not quantified in the pilot.

---

## Operational stability

During all pilot runs:
- No rate limit (429) errors occurred.
- No partial or corrupted files were written.
- All runs completed successfully.

Initial authentication errors occurred before the pilot and were resolved.

---

## Confirmed expectations

- `/new` provides dense early coverage.
- Posts persist across multiple `/new` snapshots.
- Consecutive pulls show substantial overlap.
- `rising` underfills consistently.
- Runtime is short and stable.

---

## Not evaluated in pilot

The following were intentionally deferred:
- Discovery lag distributions  
- Cross-run overlap beyond consecutive pulls  
- Time-of-day effects  
- Ranked surface persistence  
- Statistical summaries beyond counts  

---

## Pilot status

Pilot observability objectives are met.

Terminology is fixed.  
Observability limits are documented.

No further collection proceeds until collection rules are locked.