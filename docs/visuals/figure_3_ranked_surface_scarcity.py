#!/usr/bin/env python3
"""
Figure 3: Ranked surface scarcity (lower bounds).

Share of post-segments (post_id × segment_id) that were ever observed in ranked
surface snapshots (/hot, /rising), using top-100 captures only.
"""

from pathlib import Path
import csv
import matplotlib.pyplot as plt

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
OUTPUT_PATH = REPO_ROOT / "docs" / "visuals" / "figure_3_ranked_surface_scarcity.png"


def to_bool(value: str) -> bool:
    return str(value).strip().lower() == "true"


# ---------- load data ----------
with RANKED_PATH.open("r", encoding="utf-8") as handle:
    rows = list(csv.DictReader(handle))

if not rows:
    raise RuntimeError("No rows found in ranked_intersections.csv")

total = len(rows)
ever_hot = sum(1 for r in rows if to_bool(r.get("ever_in_hot")))
ever_rising = sum(1 for r in rows if to_bool(r.get("ever_in_rising")))
ever_both = sum(1 for r in rows if to_bool(r.get("ever_in_both")))

labels = ["ever in /hot", "ever in /rising", "ever in both"]
values = [
    ever_hot / total * 100.0,
    ever_rising / total * 100.0,
    ever_both / total * 100.0,
]

# ---------- plotting ----------
fig, ax = plt.subplots(figsize=(6, 4))

bars = ax.bar(labels, values, color=["#4C78A8", "#F58518", "#54A24B"])

ax.set_ylabel("percent of post-segments")
ax.set_ylim(0, 16)
ax.grid(axis="y", alpha=0.3)

# title + subtitle (no overlap)
ax.set_title("Ranked surface scarcity", fontsize=11, pad=18)
ax.text(
    0.5,
    1.02,
    "Lower bounds from top-100 snapshots.",
    transform=ax.transAxes,
    ha="center",
    va="bottom",
    fontsize=9,
)

# value labels
for bar, val in zip(bars, values):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 0.4,
        f"{val:.1f}%",
        ha="center",
        va="bottom",
        fontsize=9,
    )

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
plt.tight_layout()
plt.savefig(OUTPUT_PATH, dpi=150)
plt.close(fig)

print(f"Wrote {OUTPUT_PATH}")