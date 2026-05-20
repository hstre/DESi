"""Validate every machine-checkable claim in
``docs/rule_patch_protocol/method_claims.json`` against the
artefact it references."""
from __future__ import annotations

import json
import pathlib

import pytest


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
_CLAIMS = _REPO_ROOT / "docs" / "rule_patch_protocol" / "method_claims.json"


def _load_claims() -> list[dict]:
    payload = json.loads(_CLAIMS.read_text())
    return payload["claims"]


def _resolve_field(obj: object, path: str) -> object:
    """Walk a dot-separated path with two prefixes:

    * ``len:KEY``       → ``len(obj[KEY])``
    * ``startswith:KEY``→ ``obj[KEY]`` (the caller checks startswith)
    * ``A==B``          → ``obj[A] == obj[B]``
    """
    if "==" in path:
        a, b = path.split("==", 1)
        return _resolve_field(obj, a.strip()) == _resolve_field(obj, b.strip())
    if path.startswith("len:"):
        return len(_resolve_field(obj, path[4:]))
    if path.startswith("startswith:"):
        return _resolve_field(obj, path[len("startswith:"):])
    current = obj
    for segment in path.split("."):
        if isinstance(current, dict):
            current = current.get(segment)
        else:
            current = getattr(current, segment, None)
    return current


# ---------------------------------------------------------------------------
# Aufgabe 6 + 7
# ---------------------------------------------------------------------------


def test_at_least_twenty_claims() -> None:
    claims = _load_claims()
    assert len(claims) >= 20, f"need >= 20 claims, got {len(claims)}"


def test_every_claim_has_required_fields() -> None:
    for c in _load_claims():
        for f in (
            "claim_id", "text", "supporting_artifact",
            "field_path", "expected_value", "replay_hash",
        ):
            assert f in c, f"claim {c.get('claim_id')!r} missing {f!r}"


def test_every_claim_id_unique() -> None:
    ids = [c["claim_id"] for c in _load_claims()]
    assert len(set(ids)) == len(ids), "duplicate claim_id"


def test_every_supporting_artifact_exists() -> None:
    missing: list[str] = []
    for c in _load_claims():
        p = _REPO_ROOT / c["supporting_artifact"]
        if not p.exists():
            missing.append(f"{c['claim_id']}: {c['supporting_artifact']}")
    assert not missing, f"missing artefacts: {missing}"


def test_every_replay_hash_resolves_when_present() -> None:
    """If a claim carries a non-empty replay_hash, the supporting
    artefact's top-level ``replay_hash`` field must match it."""
    for c in _load_claims():
        if not c["replay_hash"]:
            continue
        p = _REPO_ROOT / c["supporting_artifact"]
        payload = json.loads(p.read_text())
        actual = payload.get("replay_hash")
        assert actual == c["replay_hash"], (
            f"{c['claim_id']}: artefact replay_hash {actual!r} "
            f"!= claim replay_hash {c['replay_hash']!r}"
        )


@pytest.mark.parametrize("claim_id", [
    f"C-{n:03d}" for n in range(1, 31)
])
def test_each_claim_value_matches_artifact(claim_id: str) -> None:
    """Every claim's expected_value resolves against its artefact."""
    claims = {c["claim_id"]: c for c in _load_claims()}
    if claim_id not in claims:
        pytest.skip(f"claim {claim_id} not present")
    c = claims[claim_id]
    payload = json.loads(
        (_REPO_ROOT / c["supporting_artifact"]).read_text()
    )
    field_path = c["field_path"]
    expected = c["expected_value"]
    actual = _resolve_field(payload, field_path)
    if field_path.startswith("startswith:"):
        assert isinstance(actual, str), (
            f"{c['claim_id']}: field_path 'startswith:' but value "
            f"is not str: {actual!r}"
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
