"""v5.5 — claims schema, uniqueness, scope, validation."""
from __future__ import annotations

from collections import Counter

from ._helpers import (
    artifact_hash, load_artifact, load_claims, navigate,
)


def test_claim_count_at_least_one_hundred_forty() -> None:
    assert len(load_claims()) >= 140


def test_claim_ids_unique() -> None:
    ids = [c["claim_id"] for c in load_claims()]
    assert len(set(ids)) == len(ids)


def test_claim_ids_are_c_three_digit_format() -> None:
    import re
    for c in load_claims():
        assert re.match(
            r"^C\d{3,}$", c["claim_id"],
        ), c["claim_id"]


def test_every_claim_has_required_fields() -> None:
    required = {
        "claim_id", "text", "artifact", "field_path",
        "expected_value", "replay_hash", "claim_scope",
    }
    for c in load_claims():
        missing = required - set(c.keys())
        assert not missing, (c["claim_id"], missing)


def test_claim_scope_in_closed_set() -> None:
    allowed = {
        "diagnostic_only", "intervention_only", "cross_layer",
    }
    for c in load_claims():
        assert c["claim_scope"] in allowed, c["claim_id"]


def test_every_replay_hash_claim_carries_repro_class() -> None:
    for c in load_claims():
        if c["field_path"] == "replay_hash":
            assert "repro_class" in c, c["claim_id"]


def test_repro_class_values_are_closed_set() -> None:
    allowed = {
        "FROZEN_ARTIFACT_REPLAYABLE",
        "HISTORICAL_RUNTIME_DRIFT",
        "LIVE_REPLAY_STABLE",
        "NON_REPLAYABLE_BY_DESIGN",
        "ENVIRONMENT_DEPENDENT",
        "UNKNOWN",
    }
    for c in load_claims():
        if "repro_class" in c:
            assert c["repro_class"] in allowed, c["claim_id"]


def test_every_claim_resolves_to_artifact_value() -> None:
    """The artifact-pinning check. Each claim's
    expected_value must match what the live artifact
    actually carries."""
    for c in load_claims():
        if c["field_path"] == "replay_hash":
            actual = artifact_hash(c["artifact"])
        else:
            doc = load_artifact(c["artifact"])
            actual = navigate(doc, c["field_path"])
        assert actual == c["expected_value"], (
            c["claim_id"], c["field_path"], actual,
            c["expected_value"],
        )


def test_claim_scope_distribution_is_balanced() -> None:
    counts = Counter(c["claim_scope"] for c in load_claims())
    # All three scopes are represented.
    assert counts["diagnostic_only"] >= 20
    assert counts["intervention_only"] >= 10
    assert counts["cross_layer"] >= 10
