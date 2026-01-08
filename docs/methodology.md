# Methodology

This document describes how data is collected and structured.  
It focuses on measurement mechanics, not interpretation.

---

## Study design

Prospective observational measurement study.

- Data collected forward in time  
- No retroactive backfills  
- No mid-run changes once collection begins  

---

## Target and scope

- Subreddit: r/AskReddit  
- Unit of observation: posts  
- Public data excludes post text and usernames  
- Time horizon: one fixed 7-day collection window  

---

## Listing-based sampling

All data is collected through subreddit listing endpoints.

### `/new`

- Primary sampling surface  
- Dense coverage of recent posts  
- Chronological order  
- Posts observed only while visible in `/new`  

### Ranked listings

Visibility surfaces captured each run:

- `hot`  
- `rising`  
- `controversial`  

For each surface:
- First page only  
- Up to 100 posts  

---

## Snapshot cadence

- Fixed before collection begins  
- One execution per run at a constant interval  

---

## Snapshot contents

Each snapshot records:

- Post identifier  
- Observation timestamp  
- Listing surface  
- Rank position (ranked listings only)  
- Engagement fields at capture time  

---

## Observation limits

- Discovery lag  
- Coverage gaps  
- Right censoring  

These arise from listing visibility constraints.

---

## Pilot calibration

A short pilot was used to confirm observability limits, cadence stability, and pipeline health.

---

## Long-horizon cohort

A **cohort** is a small, deterministic set of posts selected during days 2–3 of the 7-day collection window and followed to later post ages.

- Selected from early `/new` observations  
- Stratified into low, medium, and high early engagement bins  
- Limited in size to control API usage  
- Followed at fixed post ages  

---

## Data storage

- Raw data: local JSONL files, one per surface per run  
- Public data: redacted CSVs with no post text or usernames  

---

## What this does not do

- Measure impressions  
- Infer ranking algorithms  
- Track users  
- Poll posts individually  
- Make causal or predictive claims  