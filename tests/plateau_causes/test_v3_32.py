"""v3.32 — plateau cause-structure tests."""
from __future__ import annotations

import json
import pathlib

from desi.plateau_causes.cause_distribution import (
    collect_assignments, compute_distribution,
)
from desi.plateau_causes.cluster import cluster
from desi.plateau_causes.plateau_signals import (
    extract_features,
)
from desi.plateau_causes.report import (
    MAX_PLATEAU_NC_FP, build_cause_map_artifact,
    build_clusters_artifact, build_report,
)
from desi.epistemic_trajectory.extractor import (
    extract_all_trajectories,
)


def test_plateau_count_matches_v3_31() -> None:
    from desi.support_plateau.report import (
        build_report as v3_31_build,
    )
    assert (
        build_report().plateau_count
        == v3_31_build().metrics.plateau_count
    )


def test_plateau_nc_fp_rate_meets_stop_rule() -> None:
    """Directive Stop Rule: plateau_nc_fp > 0.10 halts.
    NCs by construction have final_support == 4.0."""
    r = build_report()
    assert r.plateau_nc_fp_rate <= MAX_PLATEAU_NC_FP
    assert not r.halt


def test_plateau_cluster_count_at_least_one() -> None:
    assert build_report().plateau_cluster_count >= 1


def test_dominant_class_recorded() -> None:
    r = build_report()
    assert r.dominant_plateau_class is not None
    assert isinstance(r.dominant_plateau_class, str)


def test_plateau_homogeneous_or_heterogeneous_reported() -> None:
    r = build_report()
    assert isinstance(r.plateau_homogeneous, bool)
    assert r.plateau_homogeneous == (
        r.plateau_cluster_count == 1
    )


def test_per_plateau_features_computable() -> None:
    """Pflichtfrage: für alle plateau trajectories
    feature vectors (branch_cost, novelty, confidence
    variance, frame flips)."""
    from desi.support_plateau.extractor import (
        plateau_trajectory_ids,
    )
    pids = set(plateau_trajectory_ids())
    trajs = [
        t for t in extract_all_trajectories()
        if t.trajectory_id in pids
    ]
    for t in trajs:
        f = extract_features(t)
        assert len(f.feature_vector()) == 6
        for v in f.feature_vector():
            assert isinstance(v, float)


def test_clusters_are_deterministic() -> None:
    from desi.support_plateau.extractor import (
        plateau_trajectory_ids,
    )
    pids = set(plateau_trajectory_ids())
    trajs = [
        t for t in extract_all_trajectories()
        if t.trajectory_id in pids
    ]
    feats = tuple(extract_features(t) for t in trajs)
    a = cluster(feats)
    b = cluster(feats)
    assert tuple(
        (c.cluster_id, c.size) for c in a
    ) == tuple(
        (c.cluster_id, c.size) for c in b
    )


def test_cause_distribution_is_closed_set() -> None:
    """Every primary cause must come from the v3.28
    closed CauseClass enum."""
    from desi.trajectory_root_cause.cause import CauseClass
    allowed = {c.value for c in CauseClass}
    rep = build_report().to_dict()
    for k in rep["plateau_cause_distribution"]:
        assert k in allowed, k


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "PLATEAU_IS_HOMOGENEOUS",
        "PLATEAU_HAS_SUBTYPES",
        "PLATEAU_EMPTY", "HALT_PLATEAU_NC_FP",
    }
    assert build_report().recommendation in allowed


def test_intra_cluster_variance_nonnegative() -> None:
    assert (
        build_report().intra_cluster_variance >= 0.0
    )


def test_clusters_artifact_has_features_and_clusters() -> None:
    art = build_clusters_artifact()
    assert "features" in art
    assert "clusters" in art


def test_cause_map_artifact_records_each_plateau() -> None:
    art = build_cause_map_artifact()
    assigns = art["assignments"]
    assert len(assigns) == build_report().plateau_count


def test_artifact_report_matches_live_build() -> None:
    """Stable fields pinned; cause distribution can
    drift by one trajectory across hash seeds."""
    root = pathlib.Path(__file__).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_32" / "report.json").read_text(
            encoding="utf-8",
        )
    )
    live = build_report().to_dict()
    volatile = {
        "plateau_cause_distribution", "dominant_plateau_class",
        "intra_cluster_variance",
    }
    art_stable = {
        k: v for k, v in art.items() if k not in volatile
    }
    live_stable = {
        k: v for k, v in live.items() if k not in volatile
    }
    assert art_stable == live_stable
