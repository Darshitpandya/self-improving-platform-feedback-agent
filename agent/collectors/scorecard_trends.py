"""Signal 3: Stale scorecard rules from developer portal trends.

Production: Query Port.io API for scorecard score trends over 30+ days.
Blueprint: Reads from sample-data/scorecard-trends.json.
"""

import json
from pathlib import Path


def collect(data_dir: str = "sample-data") -> dict:
    path = Path(data_dir) / "scorecard-trends.json"
    with open(path) as f:
        return json.load(f)
