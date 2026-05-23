"""Tests for the Claim object: construction, serialisation, deserialisation."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from desi.memory import Claim, ClaimState, Provenance


def _fixture_claim(**overrides) -> Claim:
    base = dict(
        content="Water boils at 100C at sea-level pressure.",
        method="T6[hypothesis_builder]",
        state=ClaimState.PROPOSED,
        confidence=0.8,
        version=1,
        provenance=Provenance(
            source="des_v0.1",
            run_id="run_xyz",
            operator_path=("T6", "T2"),
            timestamp=datetime(2026, 5, 14, 9, 0, tzinfo=timezone.utc),
        ),
    )
    base.update(overrides)
    return Claim(**base)


# ----------------------------------------------------------------------------
# Construction and id derivation
# ----------------------------------------------------------------------------


def test_claim_derives_id_from_content_method_run() -> None:
    a = _fixture_claim()
    b = _fixture_claim()
    assert a.claim_id == b.claim_id
    assert a.claim_id.startswith("c_")
    assert len(a.claim_id) == 2 + 16


def test_claim_id_differs_when_method_differs() -> None:
    a = _fixture_claim()
    b = _fixture_claim(method="human_annotation")
    assert a.claim_id != b.claim_id


def test_claim_id_differs_when_run_differs() -> None:
    a = _fixture_claim()
    b = _fixture_claim(
        provenance=Provenance(source="des_v0.1", run_id="run_other"),
    )
    assert a.claim_id != b.claim_id


def test_explicit_claim_id_is_preserved() -> None:
    c = _fixture_claim(claim_id="c_explicit_id_123")
    assert c.claim_id == "c_explicit_id_123"


# ----------------------------------------------------------------------------
# Validation
# ----------------------------------------------------------------------------


def test_empty_content_rejected() -> None:
    with pytest.raises(Exception):
        _fixture_claim(content="")


def test_empty_method_rejected() -> None:
    with pytest.raises(Exception):
        _fixture_claim(method="")


def test_confidence_out_of_range_rejected() -> None:
    with pytest.raises(Exception):
        _fixture_claim(confidence=1.5)
    with pytest.raises(Exception):
        _fixture_claim(confidence=-0.1)


def test_version_must_be_positive() -> None:
    with pytest.raises(Exception):
        _fixture_claim(version=0)


def test_extra_fields_rejected() -> None:
    # extra="forbid" on Claim
    with pytest.raises(Exception):
        Claim(
            content="x",
            method="y",
            provenance=Provenance(source="s", run_id="r"),
            unknown_field=1,
        )


# ----------------------------------------------------------------------------
# Serialisation / deserialisation
# ----------------------------------------------------------------------------


def test_to_record_is_flat() -> None:
    rec = _fixture_claim().to_record()
    # Flat namespace: no nested dicts.
    assert all(not isinstance(v, dict) for v in rec.values())
    # Provenance is flattened with prov_ prefix.
    assert "prov_source" in rec
    assert "prov_run_id" in rec
    assert "prov_operator_path" in rec
    assert "prov_timestamp" in rec


def test_to_record_uses_iso_timestamp() -> None:
    rec = _fixture_claim().to_record()
    assert rec["prov_timestamp"] == "2026-05-14T09:00:00+00:00"


def test_roundtrip_preserves_all_fields() -> None:
    original = _fixture_claim()
    rec = original.to_record()
    rebuilt = Claim.from_record(rec)
    assert rebuilt == original


def test_roundtrip_preserves_empty_operator_path() -> None:
    original = _fixture_claim(
        provenance=Provenance(
            source="human",
            run_id="r1",
            operator_path=(),
            timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        ),
    )
    rebuilt = Claim.from_record(original.to_record())
    assert rebuilt.provenance.operator_path == ()


def test_state_roundtrips_as_enum() -> None:
    original = _fixture_claim(state=ClaimState.CONFIRMED)
    rec = original.to_record()
    assert rec["state"] == "confirmed"
    rebuilt = Claim.from_record(rec)
    assert rebuilt.state is ClaimState.CONFIRMED


def test_provenance_to_from_record_independently() -> None:
    p = Provenance(
        source="src",
        run_id="r",
        operator_path=("T1", "T3"),
        timestamp=datetime(2026, 3, 14, 12, 30, tzinfo=timezone.utc),
    )
    rec = p.to_record()
    p2 = Provenance.from_record(rec)
    assert p2 == p
