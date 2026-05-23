"""v4.12 — paper reproducibility patch.

These tests assert that the v4.10 paper + claims now carry
the v4.11 reproducibility classification, without losing
any prior content.
"""
from __future__ import annotations

import json
import re
from collections import Counter

from ._helpers import (
    load_claims, load_paper_text, navigate, values_equal,
)


# ---------------------------------------------------------------------------
# Claim preservation
# ---------------------------------------------------------------------------


def test_claim_count_unchanged_at_127() -> None:
    assert len(load_claims()) == 127


def test_every_claim_id_unique_and_preserved() -> None:
    ids = [c["claim_id"] for c in load_claims()]
    assert len(set(ids)) == len(ids)
    # The id sequence is contiguous from C001.
    for i, cid in enumerate(sorted(ids), start=1):
        assert cid == f"C{i:03d}", cid


def test_no_claim_was_deleted() -> None:
    """The v4.10 schema established 127 claims; v4.12 only
    *annotates* them. Every original claim_id must still be
    present."""
    ids = {c["claim_id"] for c in load_claims()}
    expected = {f"C{i:03d}" for i in range(1, 128)}
    assert ids == expected


# ---------------------------------------------------------------------------
# Repro class coverage
# ---------------------------------------------------------------------------


def test_at_least_twenty_claims_carry_repro_class() -> None:
    patched = sum(
        1 for c in load_claims()
        if "repro_class" in c
    )
    assert patched >= 20, patched


def test_repro_class_values_are_closed_set() -> None:
    allowed = {
        "FROZEN_ARTIFACT_REPLAYABLE",
        "LIVE_REPLAY_STABLE",
        "ENVIRONMENT_DEPENDENT",
        "HISTORICAL_RUNTIME_DRIFT",
        "NON_REPLAYABLE_BY_DESIGN",
        "UNKNOWN",
    }
    for c in load_claims():
        if "repro_class" in c:
            assert c["repro_class"] in allowed, c


def test_every_patched_claim_carries_all_three_fields() -> None:
    """The directive's Aufgabe 5: only add (repro_class,
    repro_source, environment_scope); never delete."""
    for c in load_claims():
        if "repro_class" in c:
            assert "repro_source" in c, c["claim_id"]
            assert "environment_scope" in c, c["claim_id"]


def test_repro_class_matches_v411_matrix() -> None:
    """Every annotated claim's repro_class equals the v4.11
    replay matrix entry for the same artifact."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parents[2]
    matrix = json.loads(
        (root / "artifacts" / "v4_11" / "replay_matrix.json")
        .read_text(encoding="utf-8"),
    )["matrix"]
    by_version = {e["version"]: e["repro_class"] for e in matrix}
    for c in load_claims():
        if "repro_class" in c:
            expected = by_version.get(c["artifact"])
            assert expected is not None, c
            assert c["repro_class"] == expected, (
                c["claim_id"], expected, c["repro_class"],
            )


# ---------------------------------------------------------------------------
# Section structure
# ---------------------------------------------------------------------------


def _extract_sections(text: str) -> list[str]:
    return re.findall(
        r"^## (\d+\..+)$", text, flags=re.MULTILINE,
    )


def test_section_count_remains_fifteen() -> None:
    assert len(_extract_sections(load_paper_text())) == 15


def test_reproducibility_classes_subsection_exists() -> None:
    text = load_paper_text()
    assert re.search(
        r"^### Reproducibility Classes\s*$",
        text, flags=re.MULTILINE,
    ), "Reproducibility Classes subsection missing"


def test_r001_through_r006_explicitly_encoded() -> None:
    """Sections 12's new subsection must explicitly carry
    R001-R006 corrections from the directive."""
    text = load_paper_text()
    for tag in ("R001", "R002", "R003", "R004", "R005", "R006"):
        assert tag in text, tag


# ---------------------------------------------------------------------------
# Contradiction scan
# ---------------------------------------------------------------------------


def test_no_unqualified_live_equals_frozen_claim() -> None:
    """The paper must not claim live-replay stability for
    v4.0-v4.8 (which are HISTORICAL_RUNTIME_DRIFT under the
    current runtime). Scan section 12 + 14 for unqualified
    `live = frozen` phrasing."""
    text = load_paper_text()
    forbidden_phrases = (
        "all hashes remain live-replay stable",
        "every live rebuild matches every frozen artifact",
        "live replay equals historical artifact",
    )
    low = text.lower()
    for phrase in forbidden_phrases:
        assert phrase not in low, phrase


def test_section_12_distinguishes_frozen_file_vs_live_rebuild() -> None:
    """After the v4.12 patch, section 12 must explicitly
    say 'frozen file vs live rebuild' (or equivalent)."""
    text = load_paper_text()
    section_12_match = re.split(
        r"^## \d+\..+$", text, flags=re.MULTILINE,
    )
    section_12 = section_12_match[12]
    assert "frozen" in section_12.lower()
    assert (
        "live rebuild" in section_12.lower()
        or "live replay" in section_12.lower()
    )


# ---------------------------------------------------------------------------
# Distribution / counts
# ---------------------------------------------------------------------------


def test_repro_class_distribution_covers_required_classes() -> None:
    distribution = Counter(
        c.get("repro_class") for c in load_claims()
        if "repro_class" in c
    )
    # Required by the directive's R001-R004 corrections.
    assert distribution["FROZEN_ARTIFACT_REPLAYABLE"] >= 1
    assert distribution["HISTORICAL_RUNTIME_DRIFT"] >= 1
    assert distribution["LIVE_REPLAY_STABLE"] >= 1
