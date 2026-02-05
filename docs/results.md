# Results

This section summarizes what can be observed about early post visibility and engagement in r/AskReddit during the study window. All statements below are derived directly from the analysis tables and should be read as descriptive facts under partial observability, not as causal claims.

## Collection coverage and segmentation

The dataset consists of repeated listing snapshots collected at approximately 15-minute intervals over a seven-day window. Most runs occur at regular cadence, with a small number of longer gaps. Gaps exceeding 60 minutes are treated as unobserved time and define four uninterrupted collection segments. No analysis crosses these segment boundaries.

This segmentation makes unobserved time explicit and limits analysis to uninterrupted periods.

## Visibility in the chronological listing

Posts observed in the `/new` listing often remain visible across many consecutive snapshots. The median post appears 27 times within an uninterrupted segment, corresponding to several hours of observed chronological presence. Roughly 8% of observed posts appear only once or twice before disappearing from captured listings.

The observation-depth distribution includes a substantial mass of posts observed exactly once. This feature is examined in `docs/analysis/observation_depth_investigation/`. That analysis describes multiple observed patterns: posts that disappear between snapshots, posts with multi-hour persistence, and a smaller class of late-seen posts coinciding with collection gaps. The persistence pattern among posts observed more than once remains visible in the distribution.

A detailed investigation of the observation-depth distribution is provided in  
`docs/analysis/observation_depth_investigation/observation_depth_investigation.md`.

## Engagement at first observation

A majority of observed posts already have comments present at their first captured appearance. Engagement in this study is measured using comment presence and counts. Vote scores are not analyzed because they are not decomposed into upvotes and downvotes and vary over time. Among posts that initially appear with zero comments, many accumulate comments within subsequent observations while they remain visible.

These patterns describe engagement as observed, not total engagement over a post’s lifetime.

## Ranked surface scarcity

Only a small fraction of observed posts ever appear in ranked listing surfaces. Approximately 13% of observed posts appear in `/hot`, and about 1–2% appear in `/rising`, based on top-100 snapshots. These rates are lower bounds due to ranked surface truncation.

Appearance in `/rising` is not a prerequisite for appearance in `/hot`. Many posts that reach `/hot` are never observed in `/rising`, consistent with non-nested overlap in the observed listings.

## Timing of ranked promotion

When posts do reach `/hot`, promotion often occurs within one or two snapshot intervals after first being observed in `/new`. Delayed promotion is uncommon, and the distribution of lag times is strongly front-loaded.

This timing reflects the discrete snapshot cadence in the observations.

## Summary

Taken together, these observations show that for posts observed in r/AskReddit, early chronological presence is typically observed across many snapshots, while ranked-surface intersections are rare in the observed data. Posts that do not reach ranked surfaces are typically observed multiple times in `/new`.

This study does not assess causality, optimization strategies, or post quality. It documents observable properties of Reddit’s listing architecture under real collection constraints.
