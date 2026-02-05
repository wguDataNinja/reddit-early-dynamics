# Analysis Facts

Machine-generated from tables in analysis_outputs/.

Invariants
Unit of analysis: (post_id, segment_id).
Segmentation rule: segment_id increments when dt_minutes > 60.
No cross-segment aggregation.
Ranked surfaces are lower bounds due to top-N snapshots.

Observation scope
Observed post-segments in /new: 27,226.
Study window duration (study definition): 7.0 days.

Segmentation and gaps
Segments: 4.
Gap counts (run_level.csv rows): cadence=605, soft=6, hard=3.
Largest hard gap (minutes): 461.1.

/new observations and comments (post_level.csv)
Median n_appearances: 27.0.
Median (last_seen_time_utc - first_seen_time_utc) minutes: 395.9.
comments_present_at_first_observation = true: 81.1%.
ever_observed_comments = true: 94.8%.
right_censored = true: 14.5%.
discovery_lag_minutes <= 15: 82.2%.

Ranked surfaces (ranked_intersections.csv)
ever_in_hot = true: 13.1%.
ever_in_rising = true: 1.6%.
ever_in_both = true: 1.6%.
hot_only among ever_in_hot: 87.7%.
Median lag_to_hot_minutes among ever_in_hot: 15.2 min.
