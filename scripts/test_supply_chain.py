#!/usr/bin/env python3

from pathlib import Path

import yaml


repo_root = Path(__file__).resolve().parent.parent
workflow_path = repo_root / ".github" / "workflows" / "supply-chain.yml"
workflow = yaml.safe_load(workflow_path.read_text())

smoke_job = workflow["jobs"]["smoke"]
assert smoke_job.get("timeout-minutes") == 20, (
    "the smoke job must have a 20-minute global timeout"
)

print("supply-chain workflow contract: ok")
