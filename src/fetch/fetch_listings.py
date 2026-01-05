import json
import logging
from datetime import datetime
from pathlib import Path

from src.fetch.praw_client import get_reddit_client

SUBREDDIT = "AskReddit"
NEW_TARGET = 1000
SURFACE_LIMIT = 50
SURFACES = ["new", "hot", "rising", "controversial"]

def utc_stamp():
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")

def ensure_dirs():
    Path("local/raw_jsonl").mkdir(parents=True, exist_ok=True)
    Path("local/logs").mkdir(parents=True, exist_ok=True)

def write_jsonl(path, rows):
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, default=str) + "\n")

def main():
    ensure_dirs()
    run_id = utc_stamp()

    logging.basicConfig(
        level=logging.INFO,
        handlers=[
            logging.FileHandler(f"local/logs/{run_id}_pilot_fetch.log"),
            logging.StreamHandler(),
        ],
    )

    reddit = get_reddit_client()
    subreddit = reddit.subreddit(SUBREDDIT)

    for surface in SURFACES:
        limit = NEW_TARGET if surface == "new" else SURFACE_LIMIT
        rows = []
        snapshot_utc = datetime.utcnow().isoformat() + "Z"

        try:
            if surface == "new":
                listing = subreddit.new(limit=limit)
            elif surface == "hot":
                listing = subreddit.hot(limit=limit)
            elif surface == "rising":
                listing = subreddit.rising(limit=limit)
            else:
                listing = subreddit.controversial(limit=limit)

            for rank, submission in enumerate(listing, start=1):
                _ = submission.id
                row = vars(submission).copy()
                row["captured_utc"] = snapshot_utc
                row["surface"] = surface
                row["surface_rank"] = None if surface == "new" else rank
                row["listing_run_id"] = run_id
                rows.append(row)

        except Exception as e:
            logging.error(f"Fetch failed for {surface}: {e}")

        out_path = Path(f"local/raw_jsonl/{run_id}_{surface}_limit{limit}.jsonl")
        write_jsonl(out_path, rows)
        logging.info(f"Wrote {len(rows)} rows to {out_path}")

if __name__ == "__main__":
    main()
