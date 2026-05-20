"""Tests for v2.9 paper-draft consistency (Aufgabe 7)."""
from __future__ import annotations

import json
import pathlib


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
_DOCS = _REPO_ROOT / "docs" / "rule_patch_protocol"


_PHASES = (
    "DISCOVERY", "RISK_PROBE", "GUARD_SYNTHESIS",
    "IMPLEMENTATION", "REGRESSION", "REPLAY_VERIFICATION", "COMPLETE",
)


# ---------------------------------------------------------------------------
# Every required document exists
# ---------------------------------------------------------------------------


def test_readme_exists() -> None:
    assert (_DOCS / "README.md").exists()


def test_phase_diagram_exists() -> None:
    assert (_DOCS / "phase_diagram.md").exists()


def test_tinkering_table_exists() -> None:
    assert (_DOCS / "tinkering_vs_science.md").exists()


def test_worked_example_exists() -> None:
    assert (_DOCS / "worked_example_v27.md").exists()


def test_negative_control_exists() -> None:
    assert (_DOCS / "negative_control.md").exists()


def test_method_claims_exists() -> None:
    assert (_DOCS / "method_claims.json").exists()


# ---------------------------------------------------------------------------
# Phase coverage — every PatchPhase appears in the diagram exactly once
# ---------------------------------------------------------------------------


def test_phase_diagram_lists_every_phase_exactly_once() -> None:
    text = (_DOCS / "phase_diagram.md").read_text()
    for phase in _PHASES:
        count = text.count(phase)
        assert count >= 1, f"phase {phase} missing from diagram"


def test_readme_references_every_phase() -> None:
    text = (_DOCS / "README.md").read_text()
    for phase in _PHASES:
        assert phase in text, f"README does not reference {phase}"


def test_tinkering_table_has_at_least_ten_rows() -> None:
    """Aufgabe 3 requires at least 10 rows in the comparison table."""
    text = (_DOCS / "tinkering_vs_science.md").read_text()
    # Count rows of the form '| ... | ... |' excluding header + separator.
    rows = [
        ln for ln in text.splitlines()
        if ln.startswith("|") and "---" not in ln and ln.count("|") >= 3
    ]
    # Header row counts as one, the rest are data.
    assert len(rows) - 1 >= 10, (
        f"tinkering_vs_science.md only has {len(rows) - 1} data rows"
    )


# ---------------------------------------------------------------------------
# Worked example matches v2.8 reconstruction
# ---------------------------------------------------------------------------


def test_worked_example_replay_hash_matches_artifact() -> None:
    recon = json.loads(
        (_REPO_ROOT / "artifacts" / "v2_8" / "reconstruction.json")
        .read_text()
    )
    text = (_DOCS / "worked_example_v27.md").read_text()
    assert recon["replay_hash"] in text, (
        f"worked_example_v27.md must cite reconstruction replay_hash "
        f"{recon['replay_hash']}"
    )


def test_worked_example_cites_seven_guards() -> None:
    recon = json.loads(
        (_REPO_ROOT / "artifacts" / "v2_8" / "reconstruction.json")
        .read_text()
    )
    text = (_DOCS / "worked_example_v27.md").read_text()
    assert "7" in text and len(recon["created_guards"]) == 7


def test_worked_example_cites_eight_touched_files() -> None:
    recon = json.loads(
        (_REPO_ROOT / "artifacts" / "v2_8" / "reconstruction.json")
        .read_text()
    )
    text = (_DOCS / "worked_example_v27.md").read_text()
    assert "8" in text and len(recon["touched_files"]) == 8


def test_worked_example_cites_aggregate_hash() -> None:
    recon = json.loads(
        (_REPO_ROOT / "artifacts" / "v2_8" / "reconstruction.json")
        .read_text()
    )
    text = (_DOCS / "worked_example_v27.md").read_text()
    assert recon["benchmark_hash_before"] in text


# ---------------------------------------------------------------------------
# Negative control matches v2.8 fail-case
# ---------------------------------------------------------------------------


def test_negative_control_replay_hash_matches_artifact() -> None:
    fail = json.loads(
        (_REPO_ROOT / "artifacts" / "v2_8" / "fail_case.json").read_text()
    )
    text = (_DOCS / "negative_control.md").read_text()
    assert fail["replay_hash"] in text


def test_negative_control_cites_guard_synthesis_phase() -> None:
    fail = json.loads(
        (_REPO_ROOT / "artifacts" / "v2_8" / "fail_case.json").read_text()
    )
    assert fail["phase"] == "guard_synthesis"
    text = (_DOCS / "negative_control.md").read_text()
    assert "guard_synthesis" in text


def test_negative_control_cites_missing_guards_reason() -> None:
    fail = json.loads(
        (_REPO_ROOT / "artifacts" / "v2_8" / "fail_case.json").read_text()
    )
    assert fail["fail_reason"].startswith("missing_guards")
    text = (_DOCS / "negative_control.md").read_text()
    assert "missing_guards" in text


# ---------------------------------------------------------------------------
# Aufgabe 7 — no runtime imports from docs
# ---------------------------------------------------------------------------


def test_no_runtime_imports_from_docs() -> None:
    """Production code under src/desi/* must not import from docs/."""
    import re
    src_root = _REPO_ROOT / "src" / "desi"
    pattern = re.compile(r"from\s+docs|import\s+docs")
    for p in src_root.rglob("*.py"):
        text = p.read_text(encoding="utf-8")
        assert not pattern.search(text), (
            f"{p} imports from docs — directive violation"
        )
