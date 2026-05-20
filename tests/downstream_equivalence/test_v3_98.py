"""v3.98 - downstream equivalence tests."""
from __future__ import annotations

import json
import pathlib

from desi.downstream_equivalence.equivalence import (
    all_axis_overlaps,
    audit_outcome_overlap,
    failure_class_overlap,
    intervention_overlap,
    outcome_divergence,
    path_overlap,
    rescue_eligibility_overlap,
    rollback_overlap,
    verdict_overlap,
)
from desi.downstream_equivalence.outcomes import (
    FinalVerdict,
    all_downstream_signatures,
)
from desi.downstream_equivalence.report import (
    VERDICT_OVERLAP_THRESHOLD,
    build_downstream_equivalence_artifact,
    build_report,
)


def test_signature_count_is_nineteen() -> None:
    assert len(all_downstream_signatures()) == 19


def test_all_signatures_have_final_verdict() -> None:
    allowed = {v.value for v in FinalVerdict}
    for s in all_downstream_signatures():
        assert s.final_verdict in allowed


def test_axis_overlap_count_is_eight() -> None:
    """Closed enum: 8 downstream axes."""
    assert len(all_axis_overlaps()) == 8


def test_verdict_overlap_passes_concept_gate() -> None:
    """Concept Gate condition #2:
    verdict_overlap >= 0.90."""
    assert verdict_overlap() >= (
        VERDICT_OVERLAP_THRESHOLD
    )


def test_verdict_overlap_is_one() -> None:
    """Killerfrage: verhalten sich die
    Doppelganger downstream wirklich gleich?
    Yes - every G/E pair shares the same final
    verdict."""
    assert verdict_overlap() == 1.0


def test_all_axes_overlap_in_unit_interval() -> None:
    for a in all_axis_overlaps():
        assert 0.0 <= a.overlap <= 1.0


def test_path_overlap_is_one() -> None:
    assert path_overlap() == 1.0


def test_intervention_overlap_is_one() -> None:
    assert intervention_overlap() == 1.0


def test_failure_class_overlap_is_one() -> None:
    assert failure_class_overlap() == 1.0


def test_audit_outcome_overlap_is_one() -> None:
    assert audit_outcome_overlap() == 1.0


def test_rescue_eligibility_overlap_is_one() -> None:
    assert rescue_eligibility_overlap() == 1.0


def test_rollback_overlap_is_one() -> None:
    assert rollback_overlap() == 1.0


def test_outcome_divergence_is_zero() -> None:
    assert outcome_divergence() == 0.0


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_fully_equivalent() -> None:
    assert build_report().recommendation == (
        "DOWNSTREAM_FULLY_EQUIVALENT"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "DOWNSTREAM_FULLY_EQUIVALENT",
        "DOWNSTREAM_VERDICT_EQUIVALENT",
        "DOWNSTREAM_DIVERGES",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_artifact_lists_all_axes() -> None:
    art = build_downstream_equivalence_artifact()
    assert len(art["axis_overlaps"]) == 8
    assert len(art["downstream_signatures"]) == 19


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_98" / "report.json").read_text(
            encoding="utf-8",
        )
    )
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
