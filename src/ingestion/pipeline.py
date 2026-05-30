from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.data.sample_issues import build_sample_issues


OUTPUT_PATH = Path("data/civic_issues.json")


def run_mock_pipeline(output_path: Path = OUTPUT_PATH) -> pd.DataFrame:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    issues = build_sample_issues()
    output_path.write_text(json.dumps(issues, indent=2), encoding="utf-8")
    return pd.DataFrame(issues)


def load_issues(path: Path = OUTPUT_PATH) -> pd.DataFrame:
    if not path.exists():
        return run_mock_pipeline(path)
    return pd.read_json(path)


if __name__ == "__main__":
    frame = run_mock_pipeline()
    print(f"Generated {len(frame)} Hyderabad civic issue records at {OUTPUT_PATH}")
