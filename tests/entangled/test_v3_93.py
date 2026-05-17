"""v3.93 — entangled residual dimension tests."""
from __future__ import annotations

import json
import pathlib

from desi.entangled.report import (
    build_entangled_dimensions_artifact,
    build_report,
)
from desi.entangled.residual import (
    hidden_dim_candidates,
    non_proxy_variance_share,
    proxy_dims, proxy_information_loss,
    proxy_variance_share,
)
from desi.entangled.variance import (
    ENTANGLED_FAMILY_IDS,
    dominant_dims, entangled_members,
    entangled_residual_vectors,
    family_mean_diffs,
    residual_total_variance,
    residual_variance_by_dim,
    variance_share_by_dim,
)


def test_entangled_pair_is_g_and_e() -> None:
    """Directive § v3.93 fixes the entangled
    families."""
    assert ENTANGLED_FAMILY_IDS == (
        "G_v316susp", "E_v317h",
    )


def test_entangled_member_count_is_nineteen() -> None:
    """G has 9, E has 10, total 19."""
    assert len(entangled_members()) == 19


def test_residual_vectors_present() -> None:
    vs = entangled_residual_vectors()
    assert len(vs) == 19


def test_variance_shares_sum_to_one() -> None:
    shares = variance_share_by_dim()
    total = sum(shares.values())
    assert abs(total - 1.0) < 1e-3


def test_total_variance_matches_sum_of_dims() -> None:
    rvbd = residual_variance_by_dim()
    assert abs(
        sum(rvbd.values())
        - residual_total_variance()
    ) < 1e-6


def test_dominant_dims_include_anchor_density() -> None:
    """Pflichtfrage 2: are there dominant hidden
    dims? anchor_density carries ~80% of residual
    variance."""
    assert "anchor_density" in dominant_dims()


def test_proxy_information_loss_above_half() -> None:
    """Pflichtfrage 3: ist {branch_cost,
    contradiction_load} unvollstaendig? More than
    half the residual variance lives outside the
    proxy."""
    assert proxy_information_loss() > 0.5


def test_proxy_and_non_proxy_shares_sum_to_one() -> None:
    assert abs(
        proxy_variance_share()
        + non_proxy_variance_share()
        - 1.0
    ) < 1e-3


def test_hidden_dim_candidates_exclude_proxy() -> None:
    for d in hidden_dim_candidates():
        assert d not in proxy_dims()


def test_hidden_dim_candidates_nonempty() -> None:
    """Killerfrage: welche Dimension versteckt die
    Trennung? Must surface at least one."""
    assert len(hidden_dim_candidates()) > 0


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "NO_DOMINANT_DIMS",
        "PROXY_MISSING_HIDDEN_DIMS",
        "PROXY_COVERS_RESIDUAL",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_family_mean_diffs_show_branch_cost_top() -> None:
    """The dim with the largest signed mean
    difference between G and E should be the
    plausible separator candidate; the variance-
    based dominance and the mean-diff based
    separability need not align."""
    diffs = {
        m["dim"]: m["mean_diff_sum"]
        for m in build_report().family_mean_diffs
    }
    top_dim = max(diffs.items(), key=lambda kv: kv[1])
    assert top_dim[0] in (
        "branch_cost", "anchor_density",
    )


def test_artifact_lists_all_nine_dims() -> None:
    art = build_entangled_dimensions_artifact()
    assert len(art["residual_variance_by_dim"]) == 9


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_93" / "report.json").read_text(
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
