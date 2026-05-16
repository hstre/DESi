"""v5.0 — full transfer report and recommendation gate."""
from __future__ import annotations

import json
import pathlib

from desi.methodology_transfer.enums import (
    PatchabilityRecommendation, TransferRecommendation,
)
from desi.methodology_transfer.report import (
    MAX_CLUSTER_COUNT, MIN_CLUSTER_COUNT,
    MIN_LARGEST_CLUSTER, MAX_UNKNOWN_FRACTION,
    MIN_NC_ACCURACY, MIN_SAFE_PROBES, V50Report,
    build_report,
)


def test_build_report_is_deterministic() -> None:
    a = build_report()
    b = build_report()
    assert a.to_dict() == b.to_dict()


def test_report_recommendation_is_closed_enum() -> None:
    allowed = {r.value for r in TransferRecommendation}
    r = build_report()
    assert r.recommendation in allowed


def test_report_recommendation_is_confirmed() -> None:
    """All gates must pass on the v5.0 corpus."""
    r = build_report()
    assert r.recommendation == (
        TransferRecommendation.CONFIRMED.value
    ), r.rationale


def test_report_rationale_explains_each_gate() -> None:
    r = build_report()
    assert len(r.rationale) >= 6
    for reason in r.rationale:
        assert reason.startswith(("PASS:", "FAIL:"))


def test_patchability_uses_closed_enum() -> None:
    allowed = {p.value for p in PatchabilityRecommendation}
    r = build_report()
    for name, label in r.patchability.items():
        assert label in allowed, (name, label)


def test_metrics_within_required_bounds() -> None:
    r = build_report()
    m = r.metrics
    assert m.unknown_fraction <= MAX_UNKNOWN_FRACTION
    assert m.taxonomy_completeness >= 0.90
    assert 0.0 <= m.safe_probe_fraction <= 1.0
    assert 0.0 <= m.unsafe_probe_rejection_rate <= 1.0
    assert m.cross_domain_transfer_variance >= 0.0


def test_cluster_count_in_corridor() -> None:
    r = build_report()
    assert MIN_CLUSTER_COUNT <= r.cluster_count <= MAX_CLUSTER_COUNT


def test_largest_cluster_meets_threshold() -> None:
    r = build_report()
    assert r.largest_cluster_fraction >= MIN_LARGEST_CLUSTER


def test_safe_probe_count_meets_threshold() -> None:
    r = build_report()
    assert r.safe_probe_count >= MIN_SAFE_PROBES


def test_nc_accuracy_meets_threshold() -> None:
    r = build_report()
    assert r.nc_accuracy >= MIN_NC_ACCURACY


def test_report_to_json_round_trips() -> None:
    r = build_report()
    txt = r.to_json()
    obj = json.loads(txt)
    assert obj["recommendation"] == r.recommendation
    assert obj["cluster_count"] == r.cluster_count


def test_artifact_report_matches_live_build() -> None:
    """The committed artifact must match the live build."""
    root = pathlib.Path(__file__).resolve().parents[2]
    artifact = json.loads(
        (root / "artifacts" / "v5_0" / "report.json")
        .read_text(encoding="utf-8"),
    )
    live = build_report().to_dict()
    assert artifact == live


def test_artifact_taxonomy_matches_live_build() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    artifact = json.loads(
        (root / "artifacts" / "v5_0" / "taxonomy.json")
        .read_text(encoding="utf-8"),
    )
    r = build_report()
    expected = {
        "taxonomy": [t.to_dict() for t in r.taxonomy],
        "cluster_count": r.cluster_count,
        "largest_cluster_fraction":
            r.largest_cluster_fraction,
        "failure_count": r.failure_count,
    }
    assert artifact == expected
