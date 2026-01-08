# Project Phases and Execution Plan

**reddit-early-dynamics**

This document outlines the project from initial framing through publication.

Work is organized into phases to keep scope clear.

---

## Phase 0: Concept and Framing (Completed)

### Purpose  
Fix intent, scope, and boundaries before any code or data exists.

### Key outcomes  
- Framed as a measurement study and observational analysis  
- r/AskReddit selected as the sole target  
- Early dynamics and listing-based visibility defined as the focus  
- No prediction, causal inference, or algorithm inference  
- Partial observability treated as a hard constraint  

### Artifacts  
- Project overview  
- Research question structure  
- Scope definitions and exclusions  

### Exit condition  
- Language and boundaries are stable  

---

## Phase 1: Pilot (Completed)

### Purpose  
Determine what can be observed, at what cadence, and with what limits, before committing to collection.

### Includes  
- Repository structure  
- Documentation scaffolding  
- Fixed terminology  
- Pilot listing fetches:
  - `new`
  - `hot`
  - `rising`
  - `controversial`  
- Local raw JSONL pilot captures  
- Written pilot notes  

### Explicitly excludes  
- Long-running collection  
- Cohort tracking  
- Analysis or interpretation  

### Artifacts  
- Pilot collection code  
- Pilot notes  

### Exit condition  
- Observability limits are documented  
- Cadence options and surface behavior are understood  

---

## Phase 2: Collection (Active)

### Purpose  
Collect one clean, uninterrupted dataset under fixed rules.

### Includes  
- Locked snapshot cadence  
- `/new` up to 1,000  
- `hot`, `rising`, `controversial` up to 100  
- A single 7-day collection window  
- Deterministic logging and run manifests  
- Optional long-horizon cohort

A **cohort** is a small, deterministic set of posts selected during days 2–3 of the 7-day collection window and followed to a later post age.

### Explicitly excludes  
- Schema changes  
- Backfills or reruns  
- Mid-run tuning  

### Artifacts  
- Local raw JSONL listing snapshots  
- Run logs recording per-run totals, skips, misses, and api call counts  
- Cohort state events (if enabled)  

### Exit condition  
- The full collection window completes  
- The dataset is frozen  

---

## Phase 3: Diagnostics (Planned)

### Purpose  
Determine what the collected data can and cannot support.

### Includes  
- Discovery lag checks  
- Snapshot counts per post  
- Coverage gaps and censoring  
- Surface overlap rates  
- Decision to retain or drop the cohort  

### Explicitly excludes  
- Interpretation  

### Artifacts  
- Diagnostic notebooks  
- Summary tables  

---

## Phase 4: Analysis (Planned)

### Purpose  
Answer one research question within documented limits.

### Includes  
- Distributional comparisons  
- Trajectory-based analysis  
- Explicit discussion of partial observability  

### Explicitly excludes  
- Prediction framing  
- Algorithm inference  

### Artifacts  
- Analysis notebooks  
- `results.md`  

---

## Phase 5: Publication (Planned)

### Purpose  
Make the project readable without changing substance.

### Includes  
- Final README  
- Cleaned documentation  
- Stable, read-only repository state  

### Explicitly excludes  
- New data  
- New analyses  

---

## Phase Summary

- Phase 0: framing  
- Phase 1: pilot  
- Phase 2: collection  
- Phase 3: diagnostics  
- Phase 4: analysis  
- Phase 5: publication