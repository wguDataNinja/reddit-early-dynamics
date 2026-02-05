#!/usr/bin/env python3
"""
Figure 1: Collection coverage and hard gaps across the study timeline.

- Blue ticks: observed runs (success-only; from run_level.csv)
- Yellow shaded regions: unobserved hard gaps (gap_regime == "hard")
- Segment brackets: observed intervals between hard gaps (segment indexing)
- X-axis: calendar dates (sparse, human-readable)
"""

from pathlib import Path
import csv
from datetime import datetime, timezone
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ---------- locate repo ----------
here = Path(__file__).resolve()
REPO_ROOT = None
for p in [here, *here.parents[:8]]:
    if (p / "local" / "logs" / "phase2_run_manifest.jsonl").exists():
        REPO_ROOT = p
        break
if REPO_ROOT is None:
    raise RuntimeError("Could not locate phase2_run_manifest.jsonl")

RUN_LEVEL_PATH = REPO_ROOT / "analysis_outputs" / "run_level.csv"
OUTPUT_PATH = REPO_ROOT / "docs" / "visuals" / "figure_1_collection_coverage.png"


def parse_iso_utc(timestamp: str) -> datetime:
    if not isinstance(timestamp, str) or not timestamp:
        raise ValueError(f"Invalid timestamp: {timestamp!r}")
    if timestamp.endswith("Z"):
        timestamp = timestamp[:-1] + "+00:00"
    dt = datetime.fromisoformat(timestamp)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


# ---------- load run_level ----------
if not RUN_LEVEL_PATH.exists():
    raise FileNotFoundError(f"Missing run_level.csv: {RUN_LEVEL_PATH}")

with RUN_LEVEL_PATH.open("r", encoding="utf-8") as handle:
    run_rows = list(csv.DictReader(handle))

if not run_rows:
    raise RuntimeError("run_level.csv is empty")

run_rows.sort(key=lambda r: parse_iso_utc(r["run_time_utc"]))
run_times = [parse_iso_utc(r["run_time_utc"]) for r in run_rows]

# ---------- identify hard gaps ----------
hard_gaps = []
for idx in range(1, len(run_rows)):
    if (run_rows[idx].get("gap_regime") or "").strip().lower() != "hard":
        continue
    gap_start = parse_iso_utc(run_rows[idx - 1]["run_time_utc"])
    gap_end = parse_iso_utc(run_rows[idx]["run_time_utc"])
    hard_gaps.append((gap_start, gap_end))

hard_gaps.sort(key=lambda x: x[0])

segment_starts = [run_times[0]] + [end for _, end in hard_gaps]
segment_ends = [start for start, _ in hard_gaps] + [run_times[-1]]
n_segments = len(segment_starts)

# ---------- plotting ----------
fig, ax = plt.subplots(figsize=(12, 3))

# vertical layout
ticks_ymin, ticks_ymax = 0.12, 0.62
bracket_y = 0.82
bracket_feet_y = 0.74
label_y = 0.86

# observed runs
ax.vlines(
    run_times,
    ymin=ticks_ymin,
    ymax=ticks_ymax,
    color="#4C78A8",
    linewidth=1.0,
    alpha=0.6,
)

# hard gaps
for start, end in hard_gaps:
    ax.axvspan(start, end, color="#F58518", alpha=0.28)

# segment brackets + centered numbers
for i in range(n_segments):
    s = segment_starts[i]
    e = segment_ends[i]
    if e <= s:
        continue

    ax.vlines([s, e], ymin=bracket_feet_y, ymax=bracket_y, color="black", linewidth=1.0)
    ax.hlines(bracket_y, xmin=s, xmax=e, color="black", linewidth=1.0)

    mid = s + (e - s) / 2
    ax.text(mid, label_y, f"{i}", ha="center", va="bottom", fontsize=9)

# left-side label
ax.text(
    0.01,
    label_y,
    "Segment:",
    transform=ax.transAxes,
    ha="left",
    va="bottom",
    fontsize=9,
)

# title + subtitle
ax.set_title("Collection coverage and gaps", fontsize=11, pad=18)
ax.text(
    0.5,
    1.02,
    "Yellow shaded regions indicate unobserved intervals used as segment boundaries.",
    transform=ax.transAxes,
    ha="center",
    va="bottom",
    fontsize=9,
)

# x-axis formatting: calendar dates
ax.set_xlabel("date (UTC)")
ax.xaxis.set_major_locator(mdates.DayLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
ax.xaxis.set_minor_locator(mdates.HourLocator(byhour=[0, 12]))
ax.tick_params(axis="x", which="minor", length=0)

# final styling
ax.set_ylim(0, 1.0)
ax.set_yticks([])
ax.grid(axis="x", which="major", alpha=0.35)

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
plt.tight_layout()
plt.savefig(OUTPUT_PATH, dpi=150)
plt.close(fig)

print(f"Wrote {OUTPUT_PATH}")