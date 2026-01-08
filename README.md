# reddit-early-dynamics

This project measures how early engagement unfolds on Reddit, focusing on what can be observed during the first hours of a post’s life under real platform constraints.

The study targets r/AskReddit, one of Reddit’s largest and most active communities. Its posting volume allows many posts to be observed entering and exiting visibility within short time windows, without long-term tracking or intervention.

The project is strictly observational. No posts are interacted with.

---

## Listing surfaces and visibility

Reddit exposes post visibility through a set of default subreddit sorting views. This project observes a subset that is informative for early visibility and engagement:

- `/new`  
  chronological feed of newly created posts

- `hot`  
  default ranked view

- `rising`  
  posts gaining engagement quickly

- `controversial`  
  posts with polarized voting

Only these views are observed. They are sampled exactly as exposed through Reddit’s public API, without modification, deeper paging, or per-post polling.

---

## What is collected

Three parallel data streams are captured on a fixed 15-minute cadence over a single 7-day collection window.

### 1. Recent posts (`/new`)

Up to 1,000 of the most recent posts are recorded each run.

On r/AskReddit, `/new` typically spans roughly 2–4 hours of post creation. Most posts are therefore observed multiple times during their earliest visible period, producing several snapshots per post before they fall out of view.

This provides dense early-life coverage without individual post tracking.

---

### 2. Long-horizon cohort (~1%)

A **cohort** is a small, deterministic set of posts selected during days 2–3 of the 7-day window and followed to later post ages.

Cohort posts are:
- selected from early `/new` observations
- grouped into low, medium, and high early engagement bins
- limited in size to control API usage
- followed at fixed post ages rather than continuously

The cohort links early behavior to later outcomes without expanding into full per-post monitoring.

---

### 3. Visibility filters

Each run also snapshots the first page of ranked listing views:

- `hot`
- `rising`
- `controversial`

Up to 100 posts are recorded per surface per run. These snapshots capture competitive visibility without assuming continuous presence or full coverage.

---

## API constraints and design choices

API rate limiting is treated as a hard constraint.

r/AskReddit produces content at a scale where dense per-post polling risks throttling and data loss. The collection is designed to remain stable under these conditions:

- listing-based access instead of item-level polling  
- fixed execution cadence  
- bounded request volume per run  
- no retry storms or backfills  

Partial observability and truncation are treated as properties of the system, not errors to eliminate.

---

## Research focus

**Primary question**  
How does engagement begin to accumulate while posts are first becoming visible?

This includes:
- how many posts receive any activity
- how quickly comments and votes appear
- how early engagement trajectories diverge

**Secondary question**  
How does very early engagement relate to later outcomes and visibility in ranked listings?

---

## Current status

Collection is ongoing.

This repository reflects live collection behavior, operational stability, and documented measurement limits. Interpretation and analysis are intentionally not included at this stage.

---

## What this project is not

This project does not:
- predict post success
- infer ranking algorithms
- measure impressions or exposure
- assume full or continuous visibility
- track users
- provide setup or execution instructions

It measures what can be learned from public interfaces under partial observability.