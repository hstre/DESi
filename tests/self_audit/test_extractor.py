"""Tests for v3.0 claim extractor (Aufgabe 2)."""
from __future__ import annotations

from desi.self_audit import ClaimKind, extract_claims_from_text


def _extract(text: str):
    return extract_claims_from_text(
        doc_id="doc_test", doc_path="t.md", text=text,
    )


def test_extracts_hex16_hash_claim() -> None:
    claims = _extract("replay_hash = 1f4d9dfe44cb16e1")
    hex_claims = [c for c in claims if c.kind is ClaimKind.HASH]
    assert len(hex_claims) == 1
    assert hex_claims[0].value == "1f4d9dfe44cb16e1"
    assert hex_claims[0].key == "replay_hash"


def test_does_not_extract_short_hex() -> None:
    claims = _extract("see commit abc123")
    hex_claims = [c for c in claims if c.kind is ClaimKind.HASH]
    assert hex_claims == []


def test_extracts_phase_claim_from_assignment() -> None:
    claims = _extract("phase: complete")
    phase = [c for c in claims if c.kind is ClaimKind.PHASE]
    assert any(c.value == "complete" for c in phase)


def test_does_not_extract_phase_from_definition_line() -> None:
    """Bullet-style definition without : or = should not emit a claim."""
    # The line below has no colon/equals/pipe, so the extractor
    # ignores it.
    claims = _extract("* discovery is a phase")
    phases = [c for c in claims if c.kind is ClaimKind.PHASE]
    assert phases == []


def test_extracts_numeric_claim_for_precision() -> None:
    claims = _extract("precision: 1.000")
    numeric = [c for c in claims if c.kind is ClaimKind.NUMERIC]
    assert any(c.key == "precision" and c.value == "1.000"
               for c in numeric)


def test_extracts_ratio_count() -> None:
    claims = _extract("12/30 cases reached COMPLETE")
    counts = [c for c in claims if c.kind is ClaimKind.COUNT]
    assert any(c.value == "12/30" for c in counts)


def test_does_not_extract_year_in_ratio() -> None:
    claims = _extract("on 2026/05/15 we ran the audit")
    counts = [c for c in claims if c.kind is ClaimKind.COUNT]
    # 2026 exceeds the bound so the ratio is filtered.
    assert all(c.value != "2026/05/15" for c in counts)


def test_artifact_hint_extracted() -> None:
    claims = _extract(
        "see `artifacts/v2_8/reconstruction.json` for the replay_hash "
        "1f4d9dfe44cb16e1"
    )
    hex_claims = [c for c in claims if c.kind is ClaimKind.HASH]
    assert hex_claims
    assert hex_claims[0].referenced_artifact == (
        "artifacts/v2_8/reconstruction.json"
    )


def test_extractor_is_deterministic() -> None:
    text = "precision: 1.000\nreplay_hash = 1f4d9dfe44cb16e1\n12/30"
    a = _extract(text)
    b = _extract(text)
    assert a == b


def test_extractor_emits_zero_claims_for_blank_text() -> None:
    assert _extract("") == ()
    assert _extract("\n\n\n") == ()
