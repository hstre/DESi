"""Verify the quickstart document is coherent: every artefact it
cites exists, every command count claim resolves, the metrics
artefact satisfies the published budgets."""
from __future__ import annotations

import json
import pathlib
import re


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
_BUNDLE = _REPO_ROOT / "docs" / "reviewer_bundle"


_REQUIRED_BUNDLE_FILES: tuple[str, ...] = (
    "README.md",
    "quickstart.md",
    "reproduce_v27.md",
    "reproduce_v28.md",
    "reproduce_v31.md",
    "claim_index.md",
    "claim_index.json",
    "fake_reproduction.md",
)


def test_every_required_bundle_file_present() -> None:
    for name in _REQUIRED_BUNDLE_FILES:
        assert (_BUNDLE / name).exists(), f"missing {name}"


def test_quickstart_references_only_existing_artifacts() -> None:
    text = (_BUNDLE / "quickstart.md").read_text()
    for path in re.findall(r"`?artifacts/[A-Za-z0-9_./\-]+\.json", text):
        rel = path.strip("`")
        assert (_REPO_ROOT / rel).exists(), (
            f"quickstart references missing artefact {rel!r}"
        )


def test_quickstart_command_count_within_budget() -> None:
    """The quickstart promises <= 15 commands."""
    text = (_BUNDLE / "quickstart.md").read_text()
    # Count the bash command lines inside fenced code blocks that
    # start at column 0 with a known command head.
    in_bash = False
    count = 0
    for line in text.splitlines():
        if line.strip().startswith("```bash"):
            in_bash = True
            continue
        if line.strip().startswith("```"):
            in_bash = False
            continue
        if not in_bash:
            continue
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        head = s.split()[0]
        if head in (
            "git", "cd", "pytest", "python", "PYTHONPATH=src",
        ):
            count += 1
    assert count <= 15, f"quickstart has {count} commands; budget is 15"


def test_reviewer_metrics_within_budget() -> None:
    p = _REPO_ROOT / "artifacts" / "v3_2" / "reviewer_metrics.json"
    assert p.exists(), "artifacts/v3_2/reviewer_metrics.json missing"
    payload = json.loads(p.read_text())
    assert payload["total_claims"] >= 50
    assert payload["verified_claims"] == payload["total_claims"]
    assert payload["commands_required"] <= 15
    assert payload["estimated_minutes"] <= 15
    assert payload["broken_links"] == 0
    assert payload["missing_paths"] == 0
    assert payload["hash_mismatches"] == 0


def test_every_artifact_path_in_claim_index_exists() -> None:
    claims = json.loads(
        (_BUNDLE / "claim_index.json").read_text()
    )["claims"]
    missing: list[str] = []
    for c in claims:
        if not (_REPO_ROOT / c["artifact_path"]).exists():
            missing.append(c["artifact_path"])
    assert not missing, f"missing artefacts in claim index: {missing}"


def test_readme_references_every_main_chapter() -> None:
    text = (_BUNDLE / "README.md").read_text()
    for name in (
        "quickstart.md",
        "reproduce_v27.md",
        "reproduce_v28.md",
        "reproduce_v31.md",
        "claim_index.md",
        "fake_reproduction.md",
    ):
        assert name in text, f"README does not reference {name}"
