"""Signal 2: CI pipeline friction from OpenTelemetry traces.

Production: Query OTel/Prometheus API for CI pipeline step durations.
Blueprint: Reads from sample-data/ci-friction.json.
"""

import json
from pathlib import Path


def collect(data_dir: str = "sample-data") -> dict:
    path = Path(data_dir) / "ci-friction.json"
    with open(path) as f:
        return json.load(f)
