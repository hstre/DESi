"""v4.5 — effect + contamination + non-target invariants."""
from __future__ import annotations

from desi.bidirectional_cycle_patch import (
    EXPECTED_REDUCTION, TARGET_AFTER_COUNT,
    TARGET_BEFORE_COUNT, TARGET_CLUSTER,
    contamination_check, effect_measure,
)


def test_contamination_is_zero() -> None:
    rep = contamination_check()
    assert rep.contamination_count == 0, [
        t[:80] for t in rep.contaminating_texts
    ]
    assert rep.protected_pool_size > 0


def test_v45_target_cluster_fully_retired_under_live_audit() -> None:
    """v4.5's own target cluster (BIDIRECTIONAL_CYCLE) must
    remain at after_count = 0 under any later patched
    runtime. Subsequent patches (v4.7) flip additional
    clusters that v4.5 left untouched — that drift is
    documented in docs/memory/v4_7.md."""
    e = effect_measure(TARGET_CLUSTER)
    for p in e.per_class:
        if p.targeted:
            assert p.cluster == TARGET_CLUSTER
            assert p.after_count == 0
            assert p.reduction == p.before_count


def test_v45_historical_effect_pinned_in_frozen_artifact() -> None:
    """The v4.5-era effect (24 -> 19, reduction 5) is the
    historical snapshot pinned in artifacts/v4_5/report.json.
    Later patches reduce false_support_after further; we pin
    the v4.5-era numbers via the frozen file rather than the
    live rebuild."""
    import json, pathlib
    p = (
        pathlib.Path(__file__).resolve().parents[2]
        / "artifacts" / "v4_5" / "report.json"
    )
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["effect"]["false_support_before"] == (
        TARGET_BEFORE_COUNT
    )
    assert data["effect"]["false_support_after"] == (
        TARGET_AFTER_COUNT
    )
    assert data["effect"]["reduction"] == EXPECTED_REDUCTION
