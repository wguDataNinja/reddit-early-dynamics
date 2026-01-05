import json
from pathlib import Path

def test_jsonl_write_and_shape(tmp_path):
    path = tmp_path / "test.jsonl"
    row = {
        "id": "abc",
        "captured_utc": "2020-01-01T00:00:00Z",
        "surface": "new",
        "surface_rank": None,
        "listing_run_id": "run123",
    }
    with path.open("w", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")

    lines = path.read_text().strip().splitlines()
    assert len(lines) == 1
    data = json.loads(lines[0])
    for k in ["captured_utc", "surface", "surface_rank", "listing_run_id"]:
        assert k in data
