"""
Post-fetch manifest audit (minimal outputs).

Purpose:
- Validate manifest schema presence/nulls.
- Classify runs and report counts.
- Report first/last run_started_utc.

Input:
- local/logs/phase2_run_manifest.jsonl

Output:
- analysis_outputs/audit/manifest_audit_summary.json

Non-goals:
- No debug artifacts.
- No gap analysis or segmentation.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


MANIFEST_PATH = Path("local/logs/phase2_run_manifest.jsonl")
OUTPUT_PATH = Path("analysis_outputs/audit/manifest_audit_summary.json")

REQUIRED_FIELDS = [
    "run_id_utc",
    "run_started_utc",
    "run_finished_utc",
    "run_skipped_flag",
    "core_miss_flag",
    "errors_this_run",
    "core_row_count_new",
    "core_row_count_hot",
    "core_row_count_rising",
    "core_row_count_controversial",
]


def parse_iso_utc(timestamp: str) -> datetime:
    """Parse ISO UTC timestamp (ending in Z) to timezone-aware datetime."""
    if not isinstance(timestamp, str) or not timestamp:
        raise ValueError(f"Invalid timestamp value: {timestamp!r}")
    if timestamp.endswith("Z"):
        timestamp = timestamp[:-1] + "+00:00"
    dt = datetime.fromisoformat(timestamp)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def read_manifest(path: Path) -> List[Dict[str, Any]]:
    """Read JSONL manifest records from disk."""
    if not path.exists():
        raise FileNotFoundError(f"Manifest file missing: {path}")
    records: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                obj = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number}") from exc
            if not isinstance(obj, dict):
                raise ValueError(f"Manifest line {line_number} is not a JSON object")
            records.append(obj)
    if not records:
        raise ValueError("Manifest is empty; no records to audit")
    return records


def classify_run(record: Dict[str, Any]) -> str:
    """Classify a run as skipped, partial, or success."""
    if record.get("run_skipped_flag") is True:
        return "skipped"
    if record.get("core_miss_flag") is True:
        return "partial"
    return "success"


def main() -> None:
    """Run the manifest audit and write summary JSON."""
    records = read_manifest(MANIFEST_PATH)

    presence_counts = {field: 0 for field in REQUIRED_FIELDS}
    null_counts = {field: 0 for field in REQUIRED_FIELDS}

    run_started_values: List[str] = []
    success_count = 0
    partial_count = 0
    skipped_count = 0

    for record in records:
        for field in REQUIRED_FIELDS:
            if field in record:
                presence_counts[field] += 1
                if record[field] is None:
                    null_counts[field] += 1

        ts = record.get("run_started_utc")
        if ts is not None:
            run_started_values.append(ts)

        classification = classify_run(record)
        if classification == "success":
            success_count += 1
        elif classification == "partial":
            partial_count += 1
        else:
            skipped_count += 1

    missing_fields = [
        f for f in REQUIRED_FIELDS if presence_counts[f] != len(records)
    ]
    if missing_fields:
        raise ValueError(
            "Required manifest fields missing in one or more records: "
            + ", ".join(missing_fields)
        )

    if not run_started_values:
        raise ValueError("No run_started_utc values found in manifest")

    run_started_values.sort(key=lambda s: parse_iso_utc(s))

    summary = {
        "total_records": len(records),
        "required_fields_presence_counts": presence_counts,
        "required_fields_null_counts": null_counts,
        "run_classification_counts": {
            "success": success_count,
            "partial": partial_count,
            "skipped": skipped_count,
        },
        "first_run_started_utc": run_started_values[0],
        "last_run_started_utc": run_started_values[-1],
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    print(f"Wrote: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
