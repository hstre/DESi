"""v5.5 — reproducibility-class coverage on replay
hashes."""
from __future__ import annotations

from ._helpers import artifact_hash, load_claims


_V411_TAXONOMY = {
    "FROZEN_ARTIFACT_REPLAYABLE",
    "HISTORICAL_RUNTIME_DRIFT",
    "LIVE_REPLAY_STABLE",
    "NON_REPLAYABLE_BY_DESIGN",
}


def test_every_replay_hash_claim_has_repro_class_from_v411() -> None:
    for c in load_claims():
        if c["field_path"] == "replay_hash":
            cls = c.get("repro_class")
            assert cls in _V411_TAXONOMY, (
                c["claim_id"], cls,
            )


def test_every_replay_hash_claim_matches_artifact() -> None:
    for c in load_claims():
        if c["field_path"] == "replay_hash":
            assert artifact_hash(c["artifact"]) == (
                c["expected_value"]
            ), c["claim_id"]


def test_all_v5_artifacts_pinned_with_replay_hash_claim() -> None:
    """Every v5 ARTIFACT under artifacts/v5_X/ must have
    a corresponding replay_hash claim. Files whose names
    start with an underscore are end-of-sprint scratch /
    status files (e.g. ``_regression_status.json``), not
    paper-v5 artifacts; they are not part of the manifest
    and are skipped."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parents[2]
    expected = set()
    for v in ("v5_0", "v5_1", "v5_2", "v5_3", "v5_4"):
        for f in sorted((root / "artifacts" / v).glob("*.json")):
            if f.name.startswith("_"):
                continue
            expected.add(f"{v}/{f.name}")
    pinned = {
        c["artifact"] for c in load_claims()
        if c["field_path"] == "replay_hash"
        and c["artifact"].startswith("v5_")
    }
    missing = expected - pinned
    assert not missing, missing
