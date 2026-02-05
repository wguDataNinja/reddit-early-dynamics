#!/usr/bin/env python3
"""
Figure 2: distribution of observation depth (n_appearances) for post-segments.
"""

from pathlib import Path
import csv
import matplotlib.pyplot as plt

# ---------- locate repo ----------
here = Path(__file__).resolve()
REPO_ROOT = None
for p in [here, *here.parents[:8]]:
    if (p / "analysis_outputs" / "post_level.csv").exists():
        REPO_ROOT = p
        break
if REPO_ROOT is None:
    raise RuntimeError("Could not locate analysis_outputs/post_level.csv")

POST_LEVEL_PATH = REPO_ROOT / "analysis_outputs" / "post_level.csv"
OUTPUT_PATH = REPO_ROOT / "docs" / "visuals" / "figure_2_observation_depth.png"

# ---------- load data ----------
values = []
with POST_LEVEL_PATH.open("r", encoding="utf-8") as handle:
    reader = csv.DictReader(handle)
    for row in reader:
        val = row.get("n_appearances")
        if val is None or val == "":
            continue
        values.append(int(float(val)))

if not values:
    raise RuntimeError("No n_appearances values found")

values.sort()

# ---------- stats ----------
mid = len(values) // 2
if len(values) % 2 == 1:
    median_val = float(values[mid])
else:
    median_val = (values[mid - 1] + values[mid]) / 2.0

leq2 = sum(1 for v in values if v <= 2)
leq2_pct = 100.0 * leq2 / len(values)

# ---------- plotting ----------
fig, ax = plt.subplots(figsize=(8, 4))

max_val = max(values)
counts = [0] * (max_val + 1)
for v in values:
    counts[v] += 1

x_vals = list(range(1, max_val + 1))
y_vals = [counts[v] for v in x_vals]

ax.bar(x_vals, y_vals, color="#4C78A8", edgecolor="white", width=0.9)

ax.set_title("Observation depth (/new appearances per post)")
ax.set_xlabel("appearances")
ax.set_ylabel("posts")
ax.grid(axis="y", alpha=0.3)

annotation = (
    f"Median: {median_val:.1f}\n"
    f"<=2 appearances: {leq2_pct:.1f}%"
)
ax.text(
    0.98,
    0.95,
    annotation,
    transform=ax.transAxes,
    ha="right",
    va="top",
    fontsize=9,
    bbox=dict(boxstyle="round", facecolor="white", alpha=0.8, edgecolor="#CCCCCC"),
)

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
plt.tight_layout()
plt.savefig(OUTPUT_PATH, dpi=150)
plt.close(fig)

print(f"Wrote {OUTPUT_PATH}")
