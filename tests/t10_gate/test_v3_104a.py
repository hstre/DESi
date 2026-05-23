"""v3.104a - T10 historical delta decomposition
tests."""
from __future__ import annotations

import json
import pathlib

from desi.t10_gate.classify import (
    ClassifiedOutcome, DeltaKind,
    all_classified_outcomes, classify_outcome,
)
from desi.t10_gate.delta import (
    adverse_auc_delta,
    adverse_flip_count,
    affected_sprint_ids,
    beneficial_auc_delta,
    beneficial_flip_count,
    historical_delta_map,
    neutral_count,
)
from desi.t10_gate.report import (
    build_report,
    build_t10_delta_decomposition_artifact,
)


def test_four_delta_kinds() -> None:
    """Closed enum: 4 cells."""
    assert len({k.value for k in DeltaKind}) == 4


def test_classify_neutral_pass() -> None:
    """Stored=PASS, cf=PASS -> NEUTRAL_PASS."""
    from desi.t10_compat.replay import (
        HistoricalGateOutcome,
    )
    o = HistoricalGateOutcome(
        sprint_id="x", gate_metric="m",
        stored_value=1.0,
        counterfactual_value=1.0,
        threshold=0.5, higher_is_better=True,
        stored_pass=True,
        counterfactual_pass=True,
    )
    assert classify_outcome(o) == (
        DeltaKind.NEUTRAL_PASS.value
    )


def test_classify_beneficial_flip() -> None:
    from desi.t10_compat.replay import (
        HistoricalGateOutcome,
    )
    o = HistoricalGateOutcome(
        sprint_id="x", gate_metric="m",
        stored_value=0.5,
        counterfactual_value=1.0,
        threshold=0.7, higher_is_better=True,
        stored_pass=False,
        counterfactual_pass=True,
    )
    assert classify_outcome(o) == (
        DeltaKind.BENEFICIAL_FLIP.value
    )


def test_classify_adverse_flip() -> None:
    from desi.t10_compat.replay import (
        HistoricalGateOutcome,
    )
    o = HistoricalGateOutcome(
        sprint_id="x", gate_metric="m",
        stored_value=1.0,
        counterfactual_value=0.5,
        threshold=0.7, higher_is_better=True,
        stored_pass=True,
        counterfactual_pass=False,
    )
    assert classify_outcome(o) == (
        DeltaKind.ADVERSE_FLIP.value
    )


def test_classified_outcome_count_matches_v3103() -> None:
    """v3.103 produced 12 historical outcomes; the
    classifier preserves the count."""
    assert len(all_classified_outcomes()) == 12


def test_beneficial_flip_count_is_four() -> None:
    assert beneficial_flip_count() == 4


def test_adverse_flip_count_is_zero() -> None:
    """Killerfrage: sind die historischen
    Aenderungen wirklich ausschliesslich
    nuetzlich? Yes - no historical PASS
    becomes a FAIL under T10."""
    assert adverse_flip_count() == 0


def test_neutral_count_is_eight() -> None:
    """12 total - 4 beneficial - 0 adverse = 8
    neutral."""
    assert neutral_count() == 8


def test_adverse_auc_delta_is_zero() -> None:
    """Because adverse_flip_count is zero, the
    adverse AUC delta is also zero."""
    assert adverse_auc_delta() == 0.0


def test_beneficial_auc_delta_matches_v3103() -> None:
    """The v3.103 historical_auc_delta was 0.494,
    driven entirely by beneficial v3.96
    resolved_auc flip."""
    assert abs(
        beneficial_auc_delta() - 0.494239,
    ) < 1e-3


def test_affected_sprints_are_t10_targets() -> None:
    """The three sprints with flips are exactly
    the rescue targets."""
    affected = set(affected_sprint_ids())
    assert affected == {
        "v3.94 entangled_ablation",
        "v3.96 entangled_resolution",
        "v3.100 compression_audit",
    }


def test_historical_delta_map_keys_sorted() -> None:
    keys = list(historical_delta_map().keys())
    assert keys == sorted(keys)


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_purely_beneficial() -> None:
    assert build_report().recommendation == (
        "DELTA_PURELY_BENEFICIAL"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "DELTA_PURELY_BENEFICIAL",
        "DELTA_NEUTRAL",
        "DELTA_PURELY_ADVERSE",
        "DELTA_MIXED",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_artifact_lists_all_classifications() -> None:
    art = build_t10_delta_decomposition_artifact()
    assert len(art["classified_outcomes"]) == 12


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_104a" / "report.json").read_text(
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
