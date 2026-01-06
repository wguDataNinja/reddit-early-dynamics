# src/phase2/constants.py
from __future__ import annotations

# Frozen Phase 2 constants. Edit only before the 7-day window begins.

SUBREDDIT: str = "AskReddit"

SURFACES_ORDERED: list[str] = ["new", "hot", "rising", "controversial"]

NEW_LIMIT: int = 1000
RANKED_LIMIT: int = 100

# Core success floors
NEW_ROW_FLOOR: int = 900
RANKED_ROW_FLOOR: int = 1  # hot/rising/controversial must be > 0

# Output locations (local-only, gitignored)
RAW_DIR: str = "local/raw_jsonl"
LOG_DIR: str = "local/logs"
COHORT_DIR: str = "local/cohort"

MANIFEST_PATH: str = f"{LOG_DIR}/phase2_run_manifest.jsonl"
LOCK_PATH: str = f"{LOG_DIR}/phase2.lock"
PHASE2_START_PATH: str = f"{LOG_DIR}/phase2_start_utc.txt"
COHORT_STATE_PATH: str = f"{COHORT_DIR}/cohort_state.jsonl"

# Phase 2 runner behavior
SURFACE_PAUSE_SECONDS_RANGE: tuple[float, float] = (0.5, 1.0)

# Cohort control (must be set and frozen before the run starts)
COHORT_ENABLED: bool = True