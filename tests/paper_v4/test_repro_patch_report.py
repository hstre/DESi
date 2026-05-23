"""v4.12 — report artifact + recommendation gate."""
from __future__ import annotations

import json
import pathlib


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def _v4_12() -> dict:
    p = _REPO_ROOT / "artifacts" / "v4_12" / "report.json"
    return json.loads(p.read_text(encoding="utf-8"))


def test_artifact_exists() -> None:
    p = _REPO_ROOT / "artifacts" / "v4_12" / "report.json"
    assert p.exists()


def test_recommendation_is_confirmed() -> None:
    d = _v4_12()
    assert d["recommended_next"] == (
        "V4_PAPER_REPRO_PATCH_CONFIRMED"
    )


def test_claim_count_invariant() -> None:
    d = _v4_12()
    assert d["original_claim_count"] == 127
    assert d["patched_claim_count"] == 127


def test_patched_count_meets_minimum() -> None:
    d = _v4_12()
    assert d["patched_claims"] >= 20


def test_contradiction_count_is_zero() -> None:
    d = _v4_12()
    assert d["contradiction_count"] == 0


def test_section_count_unchanged() -> None:
    d = _v4_12()
    assert d["section_count"] == 15


def test_references_v4_10_and_v4_11_pins() -> None:
    d = _v4_12()
    assert d["v4_10_replay_hash"] == "42f0a23f3c054e00"
    assert d["v4_11_replay_hash"] == "70556e8d1100172d"
