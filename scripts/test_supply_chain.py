#!/usr/bin/env python3

from pathlib import Path

import yaml


repo_root = Path(__file__).resolve().parent.parent
workflow_path = repo_root / ".github" / "workflows" / "supply-chain.yml"
workflow = yaml.safe_load(workflow_path.read_text())

assert not (repo_root / "render.yaml").exists(), (
    "public deployment blueprints are blocked until the ECOM-109 security gate"
)
assert "onrender.com" not in (
    repo_root / "dashboard" / "next.config.mjs"
).read_text(), "public Render origins are blocked until the ECOM-109 security gate"

smoke_job = workflow["jobs"]["smoke"]
assert smoke_job.get("timeout-minutes") == 20, (
    "the smoke job must have a 20-minute global timeout"
)

publish_steps = [
    step["name"]
    for step in workflow["jobs"]["publish"]["steps"]
]
required_publish_order = [
    "Report HIGH and CRITICAL vulnerabilities",
    "Generate SPDX JSON SBOM",
    "Upload SBOM",
    "Block fixable HIGH and CRITICAL vulnerabilities",
    "Push immutable tag and resolve digest",
]
publish_positions = [
    publish_steps.index(step_name)
    for step_name in required_publish_order
]
assert publish_positions == sorted(publish_positions), (
    "publish must run report -> SBOM -> upload -> gate -> push"
)

publish_job = workflow["jobs"]["publish"]
build_step = next(
    step
    for step in publish_job["steps"]
    if step["name"] == "Build local image"
)
assert 'org.opencontainers.image.revision=$GITHUB_SHA' in build_step["run"], (
    "published images must carry their full source revision"
)

push_step = next(
    step
    for step in publish_job["steps"]
    if step["name"] == "Push immutable tag and resolve digest"
)
assert push_step["env"]["SOURCE_REVISION"] == "${{ github.sha }}", (
    "the retry guard must validate the workflow source revision"
)

python_dockerfiles = [
    repo_root / component / "Dockerfile"
    for component in ("api", "collector", "normalizer", "forecast")
]
for dockerfile in python_dockerfiles:
    assert "USER 10001:10001" in dockerfile.read_text(), (
        f"{dockerfile.relative_to(repo_root)} must run as the non-root app user"
    )

forecast_stages = (
    repo_root / "forecast" / "Dockerfile"
).read_text().splitlines()
runtime_start = max(
    index
    for index, line in enumerate(forecast_stages)
    if line.startswith("FROM ")
)
assert runtime_start > 0, "forecast must separate its build and runtime stages"
assert "build-essential" not in "\n".join(forecast_stages[runtime_start:]), (
    "the forecast runtime must not contain the compiler toolchain"
)

print("supply-chain workflow contract: ok")
