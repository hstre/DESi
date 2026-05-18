"""v3.96c - deterministic patch tests."""
from __future__ import annotations

import json
import pathlib

from desi.determinism_patch.patch import (
    PATCH, patch_helper,
)
from desi.determinism_patch.report import (
    build_deterministic_patch_artifact,
    build_report,
)
from desi.determinism_patch.verify import (
    artifact_diff_count, artifact_diffs,
    jittery_trajectories_post_patch,
    post_patch_jitter_rate,
    regression_breakage,
)


def test_patch_location_is_extractor_line_236() -> None:
    """Patch records the v3.96b root cause site."""
    assert PATCH.path == (
        "src/desi/epistemic_trajectory/extractor.py"
    )
    assert PATCH.line_number == 236


def test_patch_fix_kind_is_stable_hash() -> None:
    assert PATCH.fix_kind == "stable_hash"


def test_helper_function_is_deterministic() -> None:
    """The sha256-derived helper must return the
    same value for the same operator string across
    multiple calls (and across processes - but
    we only have one process available here)."""
    h = patch_helper()
    a = [h("T1"), h("T2"), h("T8")]
    b = [h("T1"), h("T2"), h("T8")]
    assert a == b


def test_helper_function_in_unit_range() -> None:
    h = patch_helper()
    for op in ("T1", "T8", "", "foo", "bar"):
        v = h(op)
        assert 0 <= v < 9


def test_helper_function_distinct_per_operator() -> None:
    """Sanity: different operator strings should
    generally produce different frame_ids."""
    h = patch_helper()
    vals = {h(f"T{i}") for i in range(1, 10)}
    assert len(vals) >= 4


def test_post_patch_jitter_rate_is_zero() -> None:
    """Killerfrage: Ist DESi jetzt wirklich
    deterministisch? Yes - across the v3.96c
    verification seeds the StateVector output is
    byte-identical."""
    assert post_patch_jitter_rate() == 0.0


def test_no_jittery_trajectories_remain() -> None:
    assert jittery_trajectories_post_patch() == ()


def test_artifact_diff_count_is_zero_for_tracked() -> None:
    """The tracked artifacts (novel-family /
    entangled sprints) do not depend on sample
    trajectories and must remain byte-identical
    after the patch."""
    assert artifact_diff_count() == 0


def test_artifact_diffs_have_consistent_count() -> None:
    diffs = artifact_diffs()
    failed = sum(1 for d in diffs if not d.matches)
    assert failed == artifact_diff_count()


def test_regression_breakage_is_zero() -> None:
    """v3.96c records zero breakage at development
    time; v3.96d audits the historical replays."""
    assert regression_breakage() == 0


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_determinism_restored() -> None:
    assert build_report().recommendation == (
        "DETERMINISM_RESTORED"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "DETERMINISM_RESTORED",
        "DETERMINISM_PARTIAL",
        "PATCH_DID_NOT_RESTORE_DETERMINISM",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_artifact_present() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2] / "artifacts" / "v3_96c"
    art = json.loads(
        (root / "report.json").read_text(
            encoding="utf-8",
        ),
    )
    assert art["post_patch_jitter_rate"] == 0.0
    assert art["recommendation"] == (
        "DETERMINISM_RESTORED"
    )


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2] / "artifacts" / "v3_96c"
    art = json.loads(
        (root / "report.json").read_text(
            encoding="utf-8",
        ),
    )
    live = build_report().to_dict()
    # numerical_delta compares post-patch frame_ids
    # against the parent process's Python hash(),
    # which is itself salted per-process; so the
    # value of the metric is meaningful but its
    # exact magnitude is non-deterministic in this
    # comparison test.
    volatile = {"rationale", "numerical_delta"}
    art_stable = {
        k: v for k, v in art.items()
        if k not in volatile
    }
    live_stable = {
        k: v for k, v in live.items()
        if k not in volatile
    }
    assert art_stable == live_stable
