"""v5.1 - open-world claim-stream tests."""
from __future__ import annotations

import json
import pathlib

from desi.open_world.claim_stream import (
    CONFLICT_KINDS, FRAME_TYPES, FrameType,
    all_conflicts, blindness_pools,
    classify_frame, conflict_kind_counts,
    frame_counts, source_counts,
    stream_claims,
)
from desi.open_world.injector import (
    inject_all, replay_injection,
)
from desi.open_world.report import (
    blindness_growth,
    build_open_world_claim_stream_artifact,
    build_report, claim_diversity,
    conflict_count, new_conflict_types,
    new_frame_count,
)
from desi.open_world.sources import (
    CLAIM_SOURCES, ClaimSource, generate_claim,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "v5_1"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


def test_claim_sources_closed_set() -> None:
    assert CLAIM_SOURCES == tuple(
        s.value for s in ClaimSource
    )
    assert len(CLAIM_SOURCES) == 6


def test_frame_types_closed_set() -> None:
    assert FRAME_TYPES == tuple(
        f.value for f in FrameType
    )
    assert len(FRAME_TYPES) == 8


def test_conflict_kinds_closed_set() -> None:
    assert len(CONFLICT_KINDS) == 4


def test_generate_claim_is_deterministic() -> None:
    a = generate_claim(
        ClaimSource.WIKIPEDIA, 0, 0,
    )
    b = generate_claim(
        ClaimSource.WIKIPEDIA, 0, 0,
    )
    assert a == b


def test_classify_frame_definitional() -> None:
    assert classify_frame(
        "X is a concept in epistemology.",
    ) == FrameType.DEFINITIONAL


def test_classify_frame_bug_report() -> None:
    assert classify_frame(
        "BUG: cannot reproduce in CI.",
    ) == FrameType.BUG_REPORT


def test_classify_frame_adversarial_to_unknown() -> (
    None
):
    """Adversarial markers MUST take precedence
    over any other frame so the conjunction is
    surfaced as blindness, not as a regular
    claim."""
    assert classify_frame(
        "X is necessary AND X is not necessary - "
        "both at once.",
    ) == FrameType.UNKNOWN


def test_stream_claim_count() -> None:
    """6 sources x 5 claims = 30."""
    assert len(stream_claims()) == 30


def test_stream_is_deterministic() -> None:
    a = [c.to_dict() for c in stream_claims()]
    b = [c.to_dict() for c in stream_claims()]
    assert a == b


def test_source_counts_uniform() -> None:
    sc = source_counts()
    assert len(sc) == 6
    assert set(sc.values()) == {5}


def test_new_frame_count_positive() -> None:
    """Pflichtfrage 3: entstehen neue Frames?"""
    assert new_frame_count() >= 1


def test_new_conflict_types_positive() -> None:
    """Pflichtfrage 4: entstehen neue
    Konfliktarten?"""
    assert new_conflict_types() >= 1


def test_blindness_growth_recorded() -> None:
    """Pflichtfrage 2: entstehen neue Blindness
    Pools? Synthetic-adversarial source seeds at
    least one blindness pool."""
    assert blindness_growth() >= 1


def test_synthetic_adversarial_is_blindness_source() -> (
    None
):
    pools = blindness_pools()
    sources = {p.source for p in pools}
    assert (
        ClaimSource.SYNTHETIC_ADVERSARIAL.value
        in sources
    )


def test_claim_diversity_bounded() -> None:
    cd = claim_diversity()
    assert 0.0 <= cd <= 1.0


def test_claim_diversity_is_uniform() -> None:
    """All sources contribute the same number
    of claims, so the normalised entropy is
    exactly 1.0."""
    assert claim_diversity() == 1.0


def test_conflict_count_consistent() -> None:
    assert conflict_count() == (
        len(all_conflicts())
    )


def test_conflict_kinds_observed_subset() -> None:
    observed = set(conflict_kind_counts().keys())
    assert observed.issubset(set(CONFLICT_KINDS))


def test_inject_all_is_deterministic() -> None:
    a = inject_all()
    b = replay_injection()
    assert a.to_dict() == b.to_dict()


def test_injection_step_count_matches_claims() -> (
    None
):
    inj = inject_all()
    assert len(inj.steps) == len(stream_claims())


def test_replay_stability_one() -> None:
    """Pflichtfrage 1: bleibt Replay stabil?"""
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "OPEN_WORLD_TRACTABLE",
        "OPEN_WORLD_OVERWHELMED",
        "OPEN_WORLD_SILENT",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in (
        allowed
    )


def test_recommendation_is_tractable() -> None:
    """Killerfrage answer: DESi sees real-world
    disorder and remains tractable - more frames
    emerge than blindness pools."""
    assert build_report().recommendation == (
        "OPEN_WORLD_TRACTABLE"
    )


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_artifact_present() -> None:
    art = _load("open_world_claim_stream.json")
    assert art["schema_version"] == (
        "v5_1_open_world_claim_stream"
    )


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("open_world_claim_stream.json")
    required = {
        "new_frame_count",
        "new_conflict_types",
        "blindness_growth",
        "claim_diversity",
    }
    assert required.issubset(art.keys())


def test_artifact_report_matches_live_build() -> (
    None
):
    art = _load("report.json")
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


def test_artifact_full_matches_live_build() -> None:
    art = _load("open_world_claim_stream.json")
    live = (
        build_open_world_claim_stream_artifact()
    )
    assert art == live


def test_no_live_internet_imports() -> None:
    """The open_world package must not import
    any network library; the directive forbids
    live internet."""
    import importlib
    forbidden = {
        "requests", "urllib3", "httpx",
        "aiohttp",
    }
    pkg = importlib.import_module(
        "desi.open_world",
    )
    seen = set(dir(pkg))
    assert not (seen & forbidden)


def test_frame_counts_consistent() -> None:
    fc = frame_counts()
    assert sum(fc.values()) == len(
        stream_claims(),
    )
