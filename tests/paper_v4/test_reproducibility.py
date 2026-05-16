"""Aufgaben 3 + 4 — every required source artifact loads and
re-runs deterministically.

Each claim's artifact + field_path is replayed live; the
result must equal the claim's expected_value bit-for-bit
(modulo the float tolerance in ``values_equal``)."""
from __future__ import annotations

from ._helpers import (
    load_artifact, load_claims, navigate, values_equal,
)


_REQUIRED_ARTIFACTS = (
    "v4_0", "v4_1", "v4_2", "v4_3", "v4_4",
    "v4_5", "v4_6", "v4_7", "v4_8", "v4_9",
    "v3_11", "v3_13", "v3_14", "v3_15", "v3_16",
    "v3_17", "v3_18", "v3_19", "v3_20", "v3_21",
    "v3_22", "v3_23",
)


def test_every_required_artifact_loads() -> None:
    for name in _REQUIRED_ARTIFACTS:
        d = load_artifact(name)
        assert "replay_hash" in d, name


def test_every_claim_replays_deterministically() -> None:
    for c in load_claims():
        artifact = load_artifact(c["artifact"])
        observed = navigate(artifact, c["field_path"])
        assert values_equal(observed, c["expected_value"]), (
            c["claim_id"]
        )


def test_v2_8_reconstruction_pin() -> None:
    """v2.8 reconstruction hash carried forward unchanged."""
    from desi.rule_patch_protocol import (
        RulePatchProtocol, causal_chain_v2_7_candidate,
        fake_rule_without_guards_candidate,
    )
    rec = RulePatchProtocol().run(causal_chain_v2_7_candidate())
    assert rec.replay_hash == "1f4d9dfe44cb16e1"
    fail = RulePatchProtocol().run(
        fake_rule_without_guards_candidate(),
    )
    assert fail.replay_hash == "d83d81ab8417c022"
