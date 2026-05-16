"""v4.11 — global replay matrix + v2.8 boundary."""
from __future__ import annotations

from desi.repro_audit import (
    V2_8_FROZEN_RECONSTRUCTION_HASH, build_entry,
    build_matrix,
)
from desi.repro_audit.replay_matrix import (
    _REQUIRED_VERSIONS,
)


def test_matrix_covers_every_required_version() -> None:
    matrix = build_matrix()
    versions_in_matrix = tuple(e.version for e in matrix)
    assert versions_in_matrix == _REQUIRED_VERSIONS


def test_every_entry_has_closed_repro_class() -> None:
    from desi.repro_audit import ReproducibilityClass

    allowed = {v.value for v in ReproducibilityClass}
    for e in build_matrix():
        assert e.repro_class in allowed, e


def test_v2_8_frozen_hash_pinned() -> None:
    """v2.8 frozen artifact's reconstruction hash must
    remain the canonical 1f4d9dfe44cb16e1."""
    e = build_entry("v2_8")
    assert e.frozen_hash == V2_8_FROZEN_RECONSTRUCTION_HASH


def test_v2_8_live_replay_recorded() -> None:
    """The v2.8 live replay is attempted and the comparison
    surfaced — drift is reported, not hidden."""
    e = build_entry("v2_8")
    assert e.live_replay_available
    if e.hash_equal:
        assert e.repro_class == "LIVE_REPLAY_STABLE"
    else:
        assert e.repro_class == "HISTORICAL_RUNTIME_DRIFT"


def test_v3_line_classified_frozen_only() -> None:
    """Every v3.11-v3.23 artifact is classified as
    FROZEN_ARTIFACT_REPLAYABLE: their builders are not
    callable here, so we explicitly do not claim live
    stability."""
    for v in (
        "v3_11", "v3_13", "v3_14", "v3_15", "v3_16",
        "v3_17", "v3_18", "v3_19", "v3_20", "v3_21",
        "v3_22", "v3_23",
    ):
        e = build_entry(v)
        assert e.repro_class == "FROZEN_ARTIFACT_REPLAYABLE"


def test_v4_0_through_v4_8_classified_as_drift_or_stable() -> None:
    """v4.0-v4.8 are pre-v4.9 snapshots. Under the
    v4.9-patched runtime their live rebuilds may differ
    from the frozen artifact; that drift must be
    classified, not hidden."""
    allowed = {
        "LIVE_REPLAY_STABLE",
        "HISTORICAL_RUNTIME_DRIFT",
    }
    for v in (
        "v4_0", "v4_1", "v4_2", "v4_3", "v4_4",
        "v4_5", "v4_6", "v4_7", "v4_8",
    ):
        e = build_entry(v)
        assert e.repro_class in allowed, (v, e.repro_class)


def test_v4_10_is_non_replayable_by_design() -> None:
    """v4.10 is a consolidation report assembled via a
    one-off script in v4.10; no live builder is exposed."""
    e = build_entry("v4_10")
    assert e.repro_class == "NON_REPLAYABLE_BY_DESIGN"
