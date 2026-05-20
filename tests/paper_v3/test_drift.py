"""Aufgabe 8 — drift checks.

Every claim in ``v3_claims.json`` is verified against the live
artifact file:

* the artifact's ``replay_hash`` must match the claim's
  ``replay_hash``;
* the value at ``field_path`` must match the claim's
  ``expected_value``.

`drift_findings` must be zero for the audit to pass.
"""
from __future__ import annotations

from ._helpers import (
    load_artifact, load_claims, navigate, values_equal,
)


def test_at_least_100_claims() -> None:
    claims = load_claims()
    assert len(claims) >= 100, (
        f"v3.24 requires >= 100 claims, found {len(claims)}"
    )


def test_every_claim_has_required_fields() -> None:
    required = {
        "claim_id", "text", "artifact", "field_path",
        "expected_value", "replay_hash",
    }
    for c in load_claims():
        missing = required - set(c)
        assert not missing, (
            f"{c.get('claim_id')} missing fields {missing}"
        )


def test_no_value_drift() -> None:
    drift: list[str] = []
    for c in load_claims():
        try:
            artifact = load_artifact(c["artifact"])
            observed = navigate(artifact, c["field_path"])
        except (KeyError, FileNotFoundError) as exc:
            drift.append(f"{c['claim_id']}: {exc}")
            continue
        if not values_equal(observed, c["expected_value"]):
            drift.append(
                f"{c['claim_id']}: expected="
                f"{c['expected_value']!r}, observed={observed!r}"
            )
    assert drift == [], (
        f"{len(drift)} drift findings: {drift[:5]}"
    )


def test_no_hash_drift() -> None:
    drift: list[str] = []
    for c in load_claims():
        artifact = load_artifact(c["artifact"])
        actual = artifact.get("replay_hash")
        if actual != c["replay_hash"]:
            drift.append(
                f"{c['claim_id']}: {c['artifact']} "
                f"hash claimed={c['replay_hash']}, "
                f"actual={actual}"
            )
    assert drift == [], drift


def test_drift_findings_zero() -> None:
    # Composite of the two checks above — the directive's
    # explicit ``drift_findings == 0`` requirement.
    drift = 0
    for c in load_claims():
        try:
            artifact = load_artifact(c["artifact"])
            observed = navigate(artifact, c["field_path"])
        except (KeyError, FileNotFoundError):
            drift += 1
            continue
        if not values_equal(observed, c["expected_value"]):
            drift += 1
        if artifact.get("replay_hash") != c["replay_hash"]:
            drift += 1
    assert drift == 0, f"drift_findings={drift}"
