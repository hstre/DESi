"""Validate every claim in ``docs/reviewer_bundle/claim_index.json``
against the artefact it references."""
from __future__ import annotations

import json
import pathlib

import pytest


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
_INDEX = _REPO_ROOT / "docs" / "reviewer_bundle" / "claim_index.json"


def _load_claims() -> list[dict]:
    return json.loads(_INDEX.read_text())["claims"]


def _resolve_field(obj: object, path: str) -> object:
    """Walk a path with the documented prefixes:

      * ``len:KEY``       → length of ``obj[KEY]``
      * ``startswith:KEY``→ ``obj[KEY]`` (caller checks startswith)
      * ``A==B``          → ``obj[A] == obj[B]``
      * ``a.b.c``         → nested dict walk
    """
    if "==" in path:
        a, b = path.split("==", 1)
        return _resolve_field(obj, a.strip()) == _resolve_field(obj, b.strip())
    if path.startswith("len:"):
        target = _resolve_field(obj, path[4:])
        if target is None:
            return None
        return len(target)
    if path.startswith("startswith:"):
        return _resolve_field(obj, path[len("startswith:"):])
    cur = obj
    for seg in path.split("."):
        if isinstance(cur, dict):
            cur = cur.get(seg)
        else:
            return None
    return cur


def test_at_least_fifty_claims() -> None:
    claims = _load_claims()
    assert len(claims) >= 50, f"only {len(claims)} claims; need >= 50"


def test_every_claim_has_required_fields() -> None:
    for c in _load_claims():
        for f in (
            "claim_id", "statement", "artifact_path",
            "field_path", "expected_value", "replay_hash",
        ):
            assert f in c, f"claim {c.get('claim_id')!r} missing {f}"


def test_every_claim_id_unique() -> None:
    ids = [c["claim_id"] for c in _load_claims()]
    assert len(set(ids)) == len(ids)


def test_every_supporting_artifact_exists() -> None:
    missing: list[str] = []
    for c in _load_claims():
        p = _REPO_ROOT / c["artifact_path"]
        if not p.exists():
            missing.append(f"{c['claim_id']}: {c['artifact_path']}")
    assert not missing, f"missing artefacts: {missing}"


def test_every_replay_hash_resolves_when_present() -> None:
    for c in _load_claims():
        if not c["replay_hash"]:
            continue
        p = _REPO_ROOT / c["artifact_path"]
        payload = json.loads(p.read_text())
        actual = payload.get("replay_hash")
        assert actual == c["replay_hash"], (
            f"{c['claim_id']}: artefact replay_hash {actual!r} "
            f"!= claim replay_hash {c['replay_hash']!r}"
        )


@pytest.mark.parametrize("claim_id", [
    f"RB-{n:03d}" for n in range(1, 61)
])
def test_each_claim_value_matches_artifact(claim_id: str) -> None:
    claims = {c["claim_id"]: c for c in _load_claims()}
    if claim_id not in claims:
        pytest.skip(f"{claim_id} not in index")
    c = claims[claim_id]
    payload = json.loads(
        (_REPO_ROOT / c["artifact_path"]).read_text()
    )
    field_path = c["field_path"]
    expected = c["expected_value"]
    actual = _resolve_field(payload, field_path)
    if field_path.startswith("startswith:"):
        assert isinstance(actual, str), (
            f"{c['claim_id']}: startswith requires str, got {actual!r}"
        )
        assert actual.startswith(expected), (
            f"{c['claim_id']}: {actual!r} does not startswith "
            f"{expected!r}"
        )
        return
    assert actual == expected, (
        f"{c['claim_id']}: at {field_path!r} expected {expected!r}, "
        f"got {actual!r}"
    )
