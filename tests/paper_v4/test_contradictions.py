"""Aufgabe 7 — contradiction checks.

For every artifact referenced by claims, every (field_path)
must map to a single value. Two claims with the same
(artifact, field_path) but different expected_values
constitute a contradiction.

``contradiction_count`` must be zero.
"""
from __future__ import annotations

from collections import defaultdict

from ._helpers import load_claims, values_equal


def test_no_intra_artifact_contradiction() -> None:
    """No two claims may pin the same (artifact, field_path)
    to inconsistent values."""
    by_key: dict[tuple[str, str], list] = defaultdict(list)
    for c in load_claims():
        by_key[(c["artifact"], c["field_path"])].append(c)
    contradictions: list[str] = []
    for key, group in by_key.items():
        if len(group) < 2:
            continue
        first = group[0]["expected_value"]
        for c in group[1:]:
            if not values_equal(c["expected_value"], first):
                contradictions.append(
                    f"{key}: "
                    f"{group[0]['claim_id']}={first!r} vs "
                    f"{c['claim_id']}={c['expected_value']!r}"
                )
    assert contradictions == [], contradictions


def test_no_cross_artifact_hash_contradiction() -> None:
    """The same artifact name must map to one replay_hash
    across every claim referencing it."""
    by_artifact: dict[str, set[str]] = defaultdict(set)
    for c in load_claims():
        by_artifact[c["artifact"]].add(c["replay_hash"])
    bad = [
        (name, sorted(hashes)) for name, hashes in by_artifact.items()
        if len(hashes) > 1
    ]
    assert bad == [], bad


def test_contradiction_count_is_zero() -> None:
    """Composite check used by the recommendation gate."""
    by_key: dict[tuple[str, str], list] = defaultdict(list)
    for c in load_claims():
        by_key[(c["artifact"], c["field_path"])].append(c)
    n = 0
    for group in by_key.values():
        if len(group) < 2:
            continue
        first = group[0]["expected_value"]
        for c in group[1:]:
            if not values_equal(c["expected_value"], first):
                n += 1
    assert n == 0
