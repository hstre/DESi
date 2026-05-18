"""v3.96b - root cause isolation tests."""
from __future__ import annotations

import json
import pathlib

from desi.determinism_root_cause.containers import (
    container_kind_counts,
    high_risk_hit_count,
    total_hit_count,
    unstable_container_kinds,
)
from desi.determinism_root_cause.ordering import (
    OrderingFix, all_classifications,
    unstable_functions,
)
from desi.determinism_root_cause.report import (
    build_report,
    build_root_cause_trace_artifact,
)
from desi.determinism_root_cause.trace import (
    all_trace_hits, builtin_hash_hits,
    hits_by_kind, is_high_risk,
)


def test_high_risk_hit_count_is_one() -> None:
    """Exactly one production-code call to
    Python's built-in randomized hash() exists in
    src/desi/."""
    assert high_risk_hit_count() == 1


def test_root_cause_at_extractor_line_236() -> None:
    """Killerfrage: Wo entsteht die
    Nichtdeterministik? At
    src/desi/epistemic_trajectory/extractor.py
    line 236."""
    bh = builtin_hash_hits()
    assert len(bh) == 1
    h = bh[0]
    assert h.path == (
        "src/desi/epistemic_trajectory/extractor.py"
    )
    assert h.line_number == 236


def test_root_cause_excerpt_uses_hash_on_operator() -> None:
    bh = builtin_hash_hits()
    assert "hash(" in bh[0].excerpt
    assert "operator" in bh[0].excerpt


def test_unstable_container_is_builtin_hash() -> None:
    assert "builtin_hash" in unstable_container_kinds()


def test_recommendation_is_root_cause_identified() -> None:
    assert build_report().recommendation == (
        "ROOT_CAUSE_IDENTIFIED"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "ROOT_CAUSE_IDENTIFIED",
        "ROOT_CAUSE_NOT_FOUND",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_ordering_fix_for_builtin_hash_is_stable_hash() -> None:
    cls = [
        c for c in all_classifications()
        if c.kind == "builtin_hash"
    ]
    for c in cls:
        assert c.suggested_fix == (
            OrderingFix.STABLE_HASH.value
        )


def test_unstable_function_includes_extractor() -> None:
    ufs = unstable_functions()
    assert any(
        "extractor.py:236" in u for u in ufs
    )


def test_total_hit_count_matches_classifications() -> None:
    assert total_hit_count() == len(
        all_classifications(),
    )


def test_container_kind_counts_consistent() -> None:
    counts = container_kind_counts()
    by_kind: dict[str, int] = {}
    for h in all_trace_hits():
        by_kind[h.kind] = by_kind.get(h.kind, 0) + 1
    assert counts == by_kind


def test_is_high_risk_only_for_builtin_hash() -> None:
    assert is_high_risk("builtin_hash")
    assert not is_high_risk("raw_set_literal")
    assert not is_high_risk("dict_fromkeys")


def test_artifact_present() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2] / "artifacts" / "v3_96b"
    art = json.loads(
        (root / "report.json").read_text(
            encoding="utf-8",
        ),
    )
    assert art["recommendation"] == (
        "ROOT_CAUSE_IDENTIFIED"
    )
    assert art["high_risk_hit_count"] == 1


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2] / "artifacts" / "v3_96b"
    art = json.loads(
        (root / "report.json").read_text(
            encoding="utf-8",
        ),
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


def test_root_cause_trace_artifact_present() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2] / "artifacts" / "v3_96b"
    art = json.loads(
        (root / "root_cause_trace.json").read_text(
            encoding="utf-8",
        ),
    )
    assert (
        art["schema_version"]
        == "v3_96b_root_cause_trace"
    )
    assert art["high_risk_hit_count"] == 1
