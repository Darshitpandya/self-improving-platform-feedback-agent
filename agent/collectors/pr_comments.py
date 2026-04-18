"""Signal 4: PR review friction from GitHub PR comments.

Production: Query GitHub API for PR review comments mentioning golden path components.
Blueprint: Reads from sample-data/pr-comments.json.
"""

import json
from pathlib import Path


def collect(data_dir: str = "sample-data") -> dict:
    path = Path(data_dir) / "pr-comments.json"
    with open(path) as f:
        return json.load(f)
