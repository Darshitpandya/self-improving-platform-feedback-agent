"""Signal 1: Post-scaffold removals from git history.

Production: Query GitHub API for commits in the first 7 days after scaffolding.
Blueprint: Reads from sample-data/git-removals.json.
"""

import json
from pathlib import Path


def collect(data_dir: str = "sample-data") -> dict:
    path = Path(data_dir) / "git-removals.json"
    with open(path) as f:
        return json.load(f)
