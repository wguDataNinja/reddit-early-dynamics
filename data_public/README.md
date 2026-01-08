# Public Data for reddit-early-dynamics

This folder is intended to hold redacted CSV outputs derived from Reddit snapshot collection. All content will be safe for public release.

---

## Included Files

- Currently empty. Future CSVs will include:
  - Observations of posts from the `/new` listing during their first hours.
  - Each row will represent a post at a specific snapshot.
  - Columns will include post ID, snapshot timestamp, listing surface, and surface rank.
  - No raw text, usernames, or direct identifiers will be included.

---

## Redaction Policy

- Raw JSONL, post text, comments, and usernames are excluded.
- Only structured metadata will be shared.
- Files will be suitable for reproducing summary statistics or engagement trajectories.

---

## Notes

- Collection cadence and window are described in [docs/project_plan.md](../docs/project_plan.md).
- Public tables will be deterministic derivations of internal snapshots.