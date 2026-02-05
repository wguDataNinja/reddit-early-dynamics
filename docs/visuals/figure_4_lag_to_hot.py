#!/usr/bin/env python3
"""
Figure 4: Distribution of cadence intervals to /hot.

Shows how many snapshot intervals elapsed between first observation in /new
and first observation in /hot, among posts that ever reached /hot.

One interval ≈ 15 minutes.
"""

from pathlib import Path
import csv
import matplotlib.pyplot as plt
from collections import Counter

# ---------- locate repo ----------
here = Path(__file__).resolve()
REPO_ROOT = None
for p in [here, *here.parents[:8]]:
    if (p / "analysis_outputs" / "ranked_intersections.csv").exists():
        REPO_ROOT = p
        break
if REPO_ROOT is None:
    raise RuntimeError("Could not locate analysis_outputs/ranked_intersections.csv")

RANKED_PATH = REPO_ROOT / "analysis_outputs" / "ranked_intersections.csv"
OUTPUT_PATH = REPO_ROOT / "docs" / "visuals" / "figure_4_lag_to_hot.png"

# ---------- load data ----------
intervals = []
with RANKED_PATH.open("r", encoding="utf-8") as handle:
    reader = csv.DictReader(handle)
    for row in reader:
        if str(row.get("ever_in_hot")).strip().lower() != "true":
            continue
        lag = row.get("lag_to_hot_minutes")
        if lag is None or lag == "":
            continue
        minutes = float(lag)
        if minutes < 0:
            continue
        # convert minutes to cadence index (15-minute snapshots)
        interval = int(round(minutes / 15.0))
        intervals.append(interval)

if not intervals:
    raise RuntimeError("No cadence intervals found")

# ---------- bin intervals ----------
# bins: 0,1,2,3,4,5+
binned = []
for i in intervals:
    if i >= 5:
        binned.append("5+")
    else:
        binned.append(str(i))

counts = Counter(binned)
total = sum(counts.values())

labels = ["0", "1", "2", "3", "4", "5+"]
values = [counts.get(lbl, 0) / total for lbl in labels]

# ---------- plotting ----------
fig, ax = plt.subplots(figsize=(7, 4))

ax.bar(labels, values, color="#4C78A8")

ax.set_title("Cadence to /hot among posts that reach /hot", fontsize=11, pad=18)
ax.text(
    0.5,
    1.02,
    "Measured in snapshot intervals from first /new observation (≈15 minutes each).",
    transform=ax.transAxes,
    ha="center",
    va="bottom",
    fontsize=9,
)

ax.set_xlabel("snapshot intervals from first /new to first /hot")
ax.set_ylabel("fraction of posts")
ax.set_ylim(0, 1.0)
ax.grid(axis="y", alpha=0.3)

for x, v in zip(labels, values):
    if v > 0:
        ax.text(
            x,
            v + 0.02,
            f"{v:.0%}",
            ha="center",
            va="bottom",
            fontsize=9,
        )

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
plt.tight_layout()
plt.savefig(OUTPUT_PATH, dpi=150)
plt.close(fig)

print(f"Wrote {OUTPUT_PATH}")