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


def test_artifact_recorded_one_high_risk_hit() -> None:
    """The v3.96b artifact captured the pre-patch
    trace: exactly one high-risk hit. The live
    trace post-v3.96c finds zero - the patch
    closed the issue."""
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2] / "artifacts" / "v3_96b"
    art = json.loads(
        (root / "report.json").read_text(
            encoding="utf-8",
        ),
    )
    assert art["high_risk_hit_count"] == 1


def test_artifact_root_cause_at_extractor_line_236() -> None:
    """Killerfrage answer from the v3.96b
    artifact: root cause was
    src/desi/epistemic_trajectory/extractor.py
    line 236."""
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2] / "artifacts" / "v3_96b"
    art = json.loads(
        (root / "report.json").read_text(
            encoding="utf-8",
        ),
    )
    bh = art["builtin_hash_hits"]
    assert len(bh) == 1
    assert bh[0]["path"] == (
        "src/desi/epistemic_trajectory/extractor.py"
    )
    assert bh[0]["line_number"] == 236


def test_artifact_excerpt_uses_hash_on_operator() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2] / "artifacts" / "v3_96b"
    art = json.loads(
        (root / "report.json").read_text(
            encoding="utf-8",
        ),
    )
    bh = art["builtin_hash_hits"]
    assert "hash(" in bh[0]["excerpt"]
    assert "operator" in bh[0]["excerpt"]


def test_post_patch_live_trace_finds_zero_hits() -> None:
    """The v3.96c patch removed the only high-risk
    hit; running the trace live should now find
    zero. This test pins the post-patch state."""
    assert high_risk_hit_count() == 0
    assert builtin_hash_hits() == ()


def test_artifact_unstable_container_is_builtin_hash() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2] / "artifacts" / "v3_96b"
    art = json.loads(
        (root / "report.json").read_text(
            encoding="utf-8",
        ),
    )
    assert "builtin_hash" in (
        art["unstable_container"]
    )


def test_artifact_recommendation_is_root_cause_identified() -> None:
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


def test_artifact_recommendation_in_closed_set() -> None:
    allowed = {
        "ROOT_CAUSE_IDENTIFIED",
        "ROOT_CAUSE_NOT_FOUND",
        "HALT_REPLAY_DRIFT",
    }
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2] / "artifacts" / "v3_96b"
    art = json.loads(
        (root / "report.json").read_text(
            encoding="utf-8",
        ),
    )
    assert art["recommendation"] in allowed


def test_artifact_replay_stability_is_one() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2] / "artifacts" / "v3_96b"
    art = json.loads(
        (root / "report.json").read_text(
            encoding="utf-8",
        ),
    )
    assert art["replay_stability"] == 1.0


def test_ordering_fix_taxonomy_includes_stable_hash() -> None:
    """OrderingFix taxonomy must contain the fix
    kind the patch used."""
    assert OrderingFix.STABLE_HASH.value == (
        "stable_hash"
    )


def test_artifact_unstable_function_includes_extractor() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2] / "artifacts" / "v3_96b"
    art = json.loads(
        (root / "report.json").read_text(
            encoding="utf-8",
        ),
    )
    assert any(
        "extractor.py:236" in u
        for u in art["unstable_function"]
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


def test_artifact_pre_patch_diverges_from_post_patch_live() -> None:
    """The v3.96b artifact captures the pre-patch
    trace; the post-v3.96c live build produces a
    DIFFERENT result because the patched line no
    longer matches. Documenting the divergence is
    the point - both states are correct at their
    respective moments."""
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2] / "artifacts" / "v3_96b"
    art = json.loads(
        (root / "report.json").read_text(
            encoding="utf-8",
        ),
    )
    live = build_report().to_dict()
    # Pre-patch: 1 high-risk hit. Post-patch: 0.
    assert art["high_risk_hit_count"] == 1
    assert live["high_risk_hit_count"] == 0
    # Pre-patch verdict: ROOT_CAUSE_IDENTIFIED.
    # Post-patch verdict: ROOT_CAUSE_NOT_FOUND.
    assert art["recommendation"] == (
        "ROOT_CAUSE_IDENTIFIED"
    )
    assert live["recommendation"] == (
        "ROOT_CAUSE_NOT_FOUND"
    )


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
