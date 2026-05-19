"""v13.0 - paper structure audit tests."""
from __future__ import annotations

import json
import pathlib

from desi.paper_integrity.bridges import (
    bridge_validity, causal_overreach_count,
    causal_overreach_detection,
)
from desi.paper_integrity.claims import (
    CLAIM_KINDS, ClaimKind, PAPER_CLASSES,
    PaperClass, class_counts, fixture,
)
from desi.paper_integrity.evidence import (
    evidence_consistency, evidence_gap_count,
)
from desi.paper_integrity.lineage import (
    epistemic_density, lineage_records,
)
from desi.paper_integrity.methods import (
    claim_method_alignment, method_gap_count,
)
from desi.paper_integrity.report import (
    build_report,
    build_structure_audit_artifact,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "paper_integrity"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


def test_paper_classes_closed_set() -> None:
    assert PAPER_CLASSES == tuple(
        c.value for c in PaperClass
    )
    assert len(PAPER_CLASSES) == 5


def test_claim_kinds_closed_set() -> None:
    assert CLAIM_KINDS == tuple(
        k.value for k in ClaimKind
    )
    assert len(CLAIM_KINDS) == 4


def test_fixture_balanced_classes() -> None:
    counts = class_counts()
    assert set(counts.keys()) == set(
        PAPER_CLASSES,
    )
    assert set(counts.values()) == {2}


def test_claim_method_alignment_bounded() -> (
    None
):
    """Pflichtfrage 1: sind Claims methodisch
    getragen? GOLD and WEAK and BORDERLINE
    contribute 6 supported claims; SLUDGE and
    ADVERSARIAL contribute 1 supported claim
    (paper-adv-002 has ms=True even though
    it cherry-picks)."""
    cma = claim_method_alignment()
    assert cma >= 0.50


def test_bridge_validity_bounded() -> None:
    """Pflichtfrage 2: stimmen Methoden und
    Evidenz ueberein?"""
    assert bridge_validity() >= 0.50


def test_epistemic_density_bounded() -> None:
    """Pflichtfrage 3: gibt es epistemische
    Luecken?"""
    assert epistemic_density() >= 0.40


def test_causal_overreach_detection_full() -> (
    None
):
    """Pflichtfrage 5: ist die Argumentation
    replaybar? Every ground-truth overreach is
    flagged."""
    assert causal_overreach_detection() == 1.0


def test_gold_papers_all_supported() -> None:
    """Sanity invariant: every GOLD paper has
    method, evidence, bridge AND substantive
    limitations."""
    for c in fixture():
        if c.paper_class == (
            PaperClass.GOLD.value
        ):
            assert c.method_supported
            assert c.evidence_supported
            assert c.bridge_valid
            assert (
                c.has_substantive_limitations
            )


def test_sludge_papers_unsupported() -> None:
    """Every AI_SLUDGE paper must FAIL at
    method, evidence, and bridge."""
    for c in fixture():
        if c.paper_class == (
            PaperClass.AI_SLUDGE.value
        ):
            assert not c.method_supported
            assert not c.evidence_supported
            assert not c.bridge_valid
            assert c.has_hallucinated_diagram
            assert c.has_hallucinated_stats


def test_borderline_legit_supported() -> None:
    """The directive's core point: BORDERLINE
    AI-assisted papers must be supported - they
    are legitimate. The audit MUST accept them."""
    for c in fixture():
        if c.paper_class == (
            PaperClass.BORDERLINE.value
        ):
            assert c.method_supported
            assert c.evidence_supported
            assert c.bridge_valid
            assert (
                c.has_substantive_limitations
            )


def test_adversarial_overreach_caught() -> None:
    """Every ADVERSARIAL paper has an overclaim
    or method-evidence gap; bridge_valid is
    False."""
    for c in fixture():
        if c.paper_class == (
            PaperClass.ADVERSARIAL.value
        ):
            assert not c.bridge_valid


def test_lineage_records_match_fixture() -> None:
    assert len(lineage_records()) == len(
        fixture(),
    )


def test_replay_stability_one() -> None:
    """Pflichtfrage 4: werden Limitationen
    ehrlich behandelt? Replay anchors the
    deterministic audit."""
    assert build_report().replay_stability == (
        1.0
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "AUDIT_STRUCTURE_SOUND",
        "AUDIT_OVERREACH_LEAK",
        "AUDIT_METHOD_THIN",
        "AUDIT_BRIDGE_WEAK",
        "AUDIT_DENSITY_LOW",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in (
        allowed
    )


def test_recommendation_is_sound() -> None:
    """Killerfrage: erkennt DESi
    wissenschaftliche Substanz - oder nur
    wissenschaftlichen Stil?"""
    assert build_report().recommendation == (
        "AUDIT_STRUCTURE_SOUND"
    )


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_artifact_present() -> None:
    art = _load("v13_0_structure_audit.json")
    assert art["schema_version"] == (
        "v13_0_paper_structure_audit"
    )


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v13_0_structure_audit.json")
    required = {
        "claim_method_alignment",
        "bridge_validity",
        "epistemic_density",
        "causal_overreach_detection",
    }
    assert required.issubset(art.keys())


def test_artifact_report_matches_live_build() -> (
    None
):
    art = _load("v13_0_report.json")
    live = build_report().to_dict()
    volatile = {"rationale"}
    art_stable = {
        k: v for k, v in art.items()
        if k not in volatile
    }
    live_stable = {
        k: v for k, v in live.items()
        if k not in volatile
    }
    assert art_stable == live_stable


def test_artifact_full_matches_live_build() -> None:
    art = _load("v13_0_structure_audit.json")
    live = build_structure_audit_artifact()
    assert art == live


def test_no_author_identification() -> None:
    """The fixture must NOT contain author
    fields. The directive bans authorship
    detection."""
    for c in fixture():
        d = c.to_dict()
        forbidden = {
            "author", "author_name",
            "writing_style",
            "ai_probability",
        }
        assert not (
            set(d.keys()) & forbidden
        )
