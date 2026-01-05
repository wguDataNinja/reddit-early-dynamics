# Terminology and Conceptual Glossary

This project uses a fixed vocabulary to avoid ambiguity, overclaiming, and unintended inference. Terms are chosen to reflect observation under platform constraints rather than system behavior or intent.

## Data artifacts

**early_window_snapshots**  
Dense, short horizon observations of submissions captured from the subreddit new listing. These data provide high resolution coverage of early post dynamics but are limited to the period during which posts remain visible in the new listing.

**long_horizon_cohort**  
A small, deterministic panel of submissions selected from the early window and followed for an extended period. This cohort bridges early engagement dynamics to later outcomes but is not intended to be representative of the full population.

**visibility_surface_snapshots**  
Periodic observations of ranked listing views such as hot, rising, and controversial. These snapshots record observed presence and rank position as a proxy for visibility states.

## Measurement and observation

**observation window**  
The time span during which a submission can be observed through a given listing surface.

**snapshot**  
A single retrieval of a listing surface at a specific time.

**snapshot cadence**  
The fixed interval at which snapshots are collected.

**discovery lag**  
The delay between a submission’s creation time and its first observation in the dataset.

**coverage gap**  
Periods during which a submission exists but is not observable through the sampled listing surfaces.

## Temporal concepts

**post age**  
Time elapsed since submission creation, used as the primary temporal axis.

**age aligned snapshots**  
Snapshots indexed by post age rather than wall clock time to enable cohort-relative comparison.

**early window**  
The initial period of a submission’s life during which dense observations are available.

**follow up horizon**  
The maximum post age reached through cohort tracking.

## Sampling concepts

**listing based sampling**  
Data collection driven by listing endpoints rather than per submission queries.

**deterministic cohort selection**  
Rule-based selection of submissions for extended tracking, applied consistently and without manual intervention.

**stratified early engagement bands**  
Grouping submissions by early engagement levels for cohort selection or comparison.

**surface limited sampling**  
Sampling constrained to the first page of ranked listing views.

## Visibility concepts

**visibility surface**  
A ranked subreddit listing view that may present submissions to users.

**surface appearance**  
An observed instance of a submission appearing on a sampled visibility surface.

**surface entry**  
The first observed appearance of a submission on a visibility surface.

**surface exit**  
The last observed appearance of a submission on a visibility surface.

**observed presence**  
A binary or ordinal indicator that a submission appears on a sampled surface at a given snapshot.

## Analytical framing

**descriptive association**  
Observed relationships between variables without causal or predictive claims.

**distributional comparison**  
Comparison of outcome distributions across groups or strata.

**trajectory divergence**  
Separation of engagement paths over time.

**variance amplification**  
An increase in dispersion of engagement outcomes over time.

**variance damping**  
A reduction in dispersion of engagement outcomes over time.

## Biases and limitations

**partial observability**  
The inability to observe all states or transitions of a submission due to platform constraints.

**survivorship bias**  
Bias introduced by analyzing only submissions that remain observable on a surface.

**right censoring**  
Loss of observation beyond a certain post age or time horizon.

**surface truncation**  
Limitation caused by observing only the first page of ranked listing views.

**API mediated measurement**  
Measurement artifacts introduced by platform API design and rate limits.

## Project framing

**measurement study**  
An analysis focused on how data can be observed and what can be inferred under constraints.

**observational analysis**  
A study that describes patterns without intervening in or manipulating the system.

**platform constrained data**  
Data whose structure and availability are determined by external platform interfaces.

**early dynamics**  
Engagement behavior occurring shortly after submission creation.