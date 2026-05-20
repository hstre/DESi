"""v4.7 — effect + contamination + non-target invariants."""
from __future__ import annotations

from desi.modality_patch import (
    EXPECTED_REDUCTION, TARGET_AFTER_COUNT,
    TARGET_BEFORE_COUNT, TARGET_CLUSTERS,
    contamination_check, effect_measure,
)


def test_contamination_is_zero() -> None:
    rep = contamination_check()
    assert rep.contamination_count == 0, [
        t[:80] for t in rep.contaminating_texts
    ]
    assert rep.protected_pool_size > 0


def test_v47_target_clusters_remain_fully_retired() -> None:
    """v4.7's two target clusters (CORRELATION_TO_CAUSATION,
    SAMPLE_TO_UNIVERSAL) must remain at after_count = 0 under
    any later runtime patch. Subsequent patches (v4.9) flip
    additional clusters that v4.7 left untouched
    (MISSING_BRIDGE_RULE) — that drift is documented in
    docs/memory/v4_9.md."""
    e = effect_measure()
    for p in e.per_class:
        if p.targeted:
            assert p.cluster in TARGET_CLUSTERS
            assert p.after_count == 0


def test_v47_historical_effect_pinned_in_frozen_artifact() -> None:
    """The v4.7 frozen artifact pins the v4.7-era effect (19
    -> 9, reduction 10). After v4.9 the live rebuild reduces
    false_support_after further to zero; we pin the v4.7-era
    numbers via the frozen file rather than the live
    rebuild."""
    import json, pathlib
    p = (
        pathlib.Path(__file__).resolve().parents[2]
        / "artifacts" / "v4_7" / "report.json"
    )
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["effect"]["false_support_before"] == (
        TARGET_BEFORE_COUNT
    )
    assert data["effect"]["false_support_after"] == (
        TARGET_AFTER_COUNT
    )
    assert data["effect"]["reduction"] == EXPECTED_REDUCTION
    assert data["effect"]["non_target_relabel_count"] == 0
