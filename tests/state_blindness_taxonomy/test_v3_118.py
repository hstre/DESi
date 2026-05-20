"""v3.118 - state-blindness taxonomy tests."""
from __future__ import annotations

import json
import pathlib

from desi.state_blindness_taxonomy.cluster import (
    all_classified_pools,
    duplicate_rate,
    routing_rate,
    semantic_blindness_rate,
    structural_rate,
    taxonomy_counts,
    unknown_rate,
)
from desi.state_blindness_taxonomy.report import (
    build_report,
    build_state_blindness_taxonomy_artifact,
)
from desi.state_blindness_taxonomy.taxonomy import (
    BlindnessKind, classify_pool,
)


def test_five_blindness_kinds() -> None:
    """Closed enum: 5 categories."""
    assert len({k.value for k in BlindnessKind}) == 5


def test_classified_pool_count_matches_v3117() -> None:
    from desi.state_blindness.detect import (
        blindness_pool_count,
    )
    assert len(all_classified_pools()) == (
        blindness_pool_count()
    )


def test_taxonomy_counts_sum_to_total() -> None:
    tc = taxonomy_counts()
    total = sum(tc.values())
    assert total == len(all_classified_pools())


def test_rates_sum_to_one() -> None:
    """Closed exhaustive taxonomy: every pool
    falls into exactly one category."""
    total = (
        duplicate_rate()
        + semantic_blindness_rate()
        + structural_rate()
        + routing_rate()
        + unknown_rate()
    )
    assert abs(total - 1.0) < 1e-3


def test_semantic_blindness_rate_positive() -> None:
    """At least one pool exhibits genuine
    semantic blindness (different texts mapping
    to the same state signature)."""
    assert semantic_blindness_rate() > 0.0


def test_duplicate_rate_above_half() -> None:
    """The bulk of state-vector collisions come
    from literal text duplicates across
    corpora."""
    assert duplicate_rate() > 0.5


def test_unknown_rate_is_zero() -> None:
    """The taxonomy is exhaustive in this corpus."""
    assert unknown_rate() == 0.0


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "MOSTLY_SEMANTIC_BLINDNESS",
        "MOSTLY_DUPLICATE_BLINDNESS",
        "MIXED_BLINDNESS",
        "NO_SEMANTIC_BLINDNESS",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_recommendation_is_mostly_duplicate() -> None:
    """Killerfrage: blind fuer Duplikate - oder
    blind fuer Erkenntnis? Mostly Duplikate."""
    assert build_report().recommendation == (
        "MOSTLY_DUPLICATE_BLINDNESS"
    )


def test_artifact_lists_all_pools() -> None:
    art = build_state_blindness_taxonomy_artifact()
    assert len(art["classified_pools"]) == (
        len(all_classified_pools())
    )


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_118" / "report.json").read_text(
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
