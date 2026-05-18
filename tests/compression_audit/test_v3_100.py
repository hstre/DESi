"""v3.100 - compression vs information loss tests."""
from __future__ import annotations

import json
import pathlib

from desi.compression_audit.compression import (
    collapsed_anchor_count,
    compression_gain,
    degenerate_vectors,
    dim_a, dim_b,
    distinct_point_count_a,
    distinct_point_count_b,
    separated_vectors,
)
from desi.compression_audit.loss import (
    downstream_diversity_a,
    downstream_diversity_b,
    downstream_failure_class_set_b,
    downstream_intervention_set_b,
    downstream_verdict_set_b,
    failure_class_delta,
    information_loss,
    predictive_delta,
    reasoning_delta,
)
from desi.compression_audit.report import (
    INFORMATION_LOSS_THRESHOLD,
    PREDICTIVE_DELTA_THRESHOLD,
    build_compression_vs_information_loss_artifact,
    build_report,
)


def test_dim_a_is_one_greater_than_dim_b() -> None:
    """A adds a one-hot family_id channel."""
    assert dim_a() == dim_b() + 1
    assert dim_a() == 46
    assert dim_b() == 45


def test_vectors_count_is_nineteen() -> None:
    assert len(degenerate_vectors()) == 19
    assert len(separated_vectors()) == 19


def test_separated_keeps_family_id_one_hot() -> None:
    """The 46th coordinate is 1.0 for G_v316susp
    members and 0.0 for E_v317h members."""
    seps = separated_vectors()
    for tid, v in seps.items():
        if tid.startswith("v316-susp:"):
            assert v[-1] == 1.0
        elif tid.startswith("v317-h:"):
            assert v[-1] == 0.0


def test_compression_gain_positive() -> None:
    """B collapses at least one A-distinct
    point."""
    assert compression_gain() > 0.0


def test_distinct_point_b_lte_distinct_point_a() -> None:
    assert (
        distinct_point_count_b()
        <= distinct_point_count_a()
    )


def test_collapsed_anchors_above_half() -> None:
    """At least 10 of 19 anchors share a B-point
    with at least one other anchor."""
    assert collapsed_anchor_count() >= 10


def test_information_loss_in_unit_interval() -> None:
    assert 0.0 <= information_loss() <= 1.0


def test_information_loss_does_not_pass_gate() -> None:
    """Concept Gate condition #4: information_loss
    <= 0.10. We fail this under the upper-bound
    diversity model: A could in principle assign
    one downstream tuple per (family, current
    outcome) cell that B cannot."""
    assert information_loss() > (
        INFORMATION_LOSS_THRESHOLD
    )


def test_predictive_delta_passes_gate() -> None:
    """Concept Gate condition #5: predictive_delta
    <= 0.10. Current DESi downstream logic does
    not consult family_id, so the two
    representations are equally (un)predictive."""
    assert predictive_delta() <= (
        PREDICTIVE_DELTA_THRESHOLD
    )


def test_predictive_delta_is_zero() -> None:
    assert predictive_delta() == 0.0


def test_failure_class_delta_is_zero() -> None:
    assert failure_class_delta() == 0.0


def test_reasoning_delta_above_zero() -> None:
    """If A could express richer downstream
    distinctions per family, B loses reasoning
    capacity even when current outputs match."""
    assert reasoning_delta() > 0.0


def test_downstream_verdict_set_singleton() -> None:
    """All 19 anchors collapse to a single final
    verdict in the production pipeline."""
    assert len(downstream_verdict_set_b()) == 1


def test_downstream_intervention_set_singleton() -> None:
    assert len(downstream_intervention_set_b()) == 1


def test_downstream_failure_class_set_singleton() -> None:
    assert len(downstream_failure_class_set_b()) == 1


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_compression_with_information_loss() -> None:
    """Mixed verdict: predictive_delta passes its
    gate, information_loss fails. The directive's
    closed verdict for this cell is
    COMPRESSION_WITH_INFORMATION_LOSS."""
    assert build_report().recommendation == (
        "COMPRESSION_WITH_INFORMATION_LOSS"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "USEFUL_COMPRESSION",
        "COMPRESSION_WITH_PREDICTIVE_COST",
        "COMPRESSION_WITH_INFORMATION_LOSS",
        "BLIND_INFORMATION_LOSS",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_downstream_diversity_a_at_least_b() -> None:
    a = downstream_diversity_a()
    b = downstream_diversity_b()
    for axis in b:
        assert a.get(axis, 0) >= b[axis]


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_100" / "report.json").read_text(
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
