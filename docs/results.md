# Results

This document tracks collection status and operational stability.

It records what has been collected and how the system is behaving.  
It does not interpret patterns or explain outcomes.

---

## Collection status

- Collection window: active  
- Window length: 7 days  
- Start marker (UTC): 2026-01-06T16:36:56Z  

---

## Data written per run

Each run writes:

- `/new` snapshot, up to 1,000 posts  
- `hot` snapshot, up to 100 posts  
- `rising` snapshot, up to 100 posts  
- `controversial` snapshot, up to 100 posts  

All snapshots are written as local JSONL files.

Each run also writes:
- One per-run log file  
- One appended manifest record  
- Cohort state events (if cohort is enabled)

---

## Run accounting

Run logs and the manifest record:

- Per-run totals  
- Skips  
- Misses  
- API call counts  

These logs are the authoritative source for operational status.

---

## Stability checks

Observed so far:

- No skipped runs  
- No repeated misses  
- Stable row counts for `/new`, `hot`, and `controversial`  
- Consistent underfill on `rising`  

Underfill on `rising` is treated as an observed property of the listing response.

---

## Cohort status

The **cohort** is enabled.

The cohort is approximately 1 percent of expected posts, selected during days 2–3 of the 7-day collection window and followed to later post ages.

Selection details:
- Drawn from early `/new` observations  
- Split into three bins: low, medium, and high early engagement  
- Deterministic and fixed once recruited  

Operational notes:
- Cohort API usage increases sharply during the recruitment window  
- This increase is expected while the full cohort is assembled  
- Once recruitment completes, cohort-related API calls are expected to level out  

API usage is monitored continuously.

After the full cohort is collected:
- Total API usage will be reviewed  
- Cohort cost will be weighed against analytical value  
- Cohort tracking may be continued or stopped  

If rate limiting, sustained errors, or instability appear, cohort tracking will be disabled without affecting core collection.

---

## What this does not contain

This document does not include:

- Diagnostics  
- Distributional summaries  
- Visibility pathway analysis  
- Narrative conclusions  

These belong after collection completes.

---

## Updates to append later

After collection completes:
- Total runs completed  
- Total skips and misses  
- Total API calls  
- Total raw files written  

After diagnostics begin:
- What the data can and cannot support