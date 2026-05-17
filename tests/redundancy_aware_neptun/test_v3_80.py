"""v3.80 — redundancy-aware Neptun tests."""
from __future__ import annotations

import json
import pathlib

from desi.redundancy_aware_neptun.masking import (
    all_class_removal_outcomes,
)
from desi.redundancy_aware_neptun.neptun_retest import (
    all_class_localizations,
    candidate_match_score,
    false_missing_claim_rate,
    localization_accuracy,
)
from desi.redundancy_aware_neptun.report import (
    build_redundancy_aware_neptun_artifact,
    build_redundancy_masking_claims_artifact,
    build_report,
)


def test_class_removal_outcomes_count() -> None:
    """Three redundancy classes from v3.79 -> three
    outcomes."""
    assert len(all_class_removal_outcomes()) == 3


def test_high_class_removal_is_121() -> None:
    outs = {
        o.coverage_size: o
        for o in all_class_removal_outcomes()
    }
    assert outs[121].perturbation_magnitude == 121
    assert outs[121].single_member_perturbation == 0


def test_bridge_class_removal_is_12() -> None:
    outs = {
        o.coverage_size: o
        for o in all_class_removal_outcomes()
    }
    assert outs[12].perturbation_magnitude == 12
    assert outs[12].single_member_perturbation == 0


def test_zero_class_removal_is_zero() -> None:
    outs = {
        o.coverage_size: o
        for o in all_class_removal_outcomes()
    }
    assert outs[0].perturbation_magnitude == 0


def test_redundancy_aware_high_removal_is_121() -> None:
    r = build_report()
    assert r.redundancy_aware_high_removal == 121


def test_redundancy_aware_redundant_removal_is_zero() -> None:
    r = build_report()
    assert r.redundancy_aware_redundant_removal == 0


def test_gate1_recovered() -> None:
    """Concept gate #4: gate1_recovered = true."""
    assert build_report().gate1_recovered is True


def test_localization_accuracy_is_one() -> None:
    """Both eligible class removals (Class 0 and 1)
    correctly localize to their own centroid."""
    assert localization_accuracy(
        all_class_localizations(),
    ) == 1.0


def test_candidate_match_score_is_one() -> None:
    assert candidate_match_score(
        all_class_localizations(),
    ) == 1.0


def test_false_missing_claim_rate_meets_concept_gate() -> None:
    """Concept gate #5: false_missing_claim_rate
    <= 0.20. Inherits 0.00 from v3.77 negative
    controls."""
    assert false_missing_claim_rate() <= 0.20
    assert false_missing_claim_rate() == 0.0


def test_class_localization_class_zero_correct() -> None:
    locs = all_class_localizations()
    high = next(
        l for l in locs if l.coverage_size == 121
    )
    assert high.orphan_count == 121
    assert high.predicted_correctly is True


def test_class_localization_class_one_correct() -> None:
    locs = all_class_localizations()
    bridge = next(
        l for l in locs if l.coverage_size == 12
    )
    assert bridge.orphan_count == 12
    assert bridge.predicted_correctly is True


def test_class_localization_class_two_has_no_signal() -> None:
    locs = all_class_localizations()
    zero = next(
        l for l in locs if l.coverage_size == 0
    )
    assert zero.orphan_count == 0
    assert zero.predicted_correctly is False


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_recovered() -> None:
    assert build_report().recommendation == (
        "GATE1_RECOVERED"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "GATE1_RECOVERED",
        "GATE1_PARTIAL_RECOVERY",
        "GATE1_NOT_RECOVERED",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_artifact_records_classes() -> None:
    art = build_redundancy_aware_neptun_artifact()
    assert len(art["class_removal_outcomes"]) == 3
    assert len(art["class_localizations"]) == 3


def test_redundancy_masking_claims_artifact() -> None:
    art = build_redundancy_masking_claims_artifact()
    assert art["claim_count"] == 3
    # Classes 0 and 1 show masking; Class 2 does not.
    by_class = {
        c["class_id"]: c for c in art["claims"]
    }
    assert by_class[0]["masking_observed"] is True
    assert by_class[1]["masking_observed"] is True
    assert by_class[2]["masking_observed"] is False


def test_redundancy_masking_concept_gate_summary() -> None:
    """All six Redundancy Masking concept gates
    evaluated end-to-end."""
    from desi.redundancy_pair.report import (
        build_report as v378,
    )
    r78 = v378()
    r80 = build_report()
    # Gate 1: single_removal_perturbation == 0
    for pid, val in (
        r78.single_removal_perturbation.items()
    ):
        assert val == 0
    # Gate 2: double_removal_perturbation > 0
    assert r78.double_removal_perturbation > 0
    # Gate 3: redundancy_unmasking_gain > 0
    assert r78.redundancy_unmasking_gain > 0
    # Gate 4: gate1_recovered = true
    assert r80.gate1_recovered is True
    # Gate 5: false_missing_claim_rate <= 0.20
    assert r80.false_missing_claim_rate <= 0.20
    # Gate 6: replay stability
    assert r78.replay_stability == 1.0
    assert r80.replay_stability == 1.0


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_80" / "report.json").read_text(
            encoding="utf-8",
        )
    )
    live = build_report().to_dict()
    volatile = {"rationale"}
    art_stable = {
        k: v for k, v in art.items() if k not in volatile
    }
    live_stable = {
        k: v for k, v in live.items() if k not in volatile
    }
    assert art_stable == live_stable
