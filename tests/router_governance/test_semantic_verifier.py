"""Phase-3.5 semantic-verifier parser tests (deterministic, no network)."""
from __future__ import annotations

from desi_router.governance.benchmark.semantic_verifier import classify, parse_verdict


def test_parse_verdict_maps_three_classes():
    assert parse_verdict("ADOPTS") == "adopts"
    assert parse_verdict("  rejects.") == "rejects"
    assert parse_verdict("ABSENT") == "absent"
    assert parse_verdict("REJECTS — it is superseded") == "rejects"
    assert parse_verdict("") == "absent"          # unknown defaults to absent
    assert parse_verdict("the answer ADOPTS it") == "adopts"   # adopts wins on mention


def test_classify_uses_backend_and_parses(monkeypatch):
    class FakeBackend:
        def call_messages(self, system, messages, *, model, temperature, max_tokens):
            assert "INVALID" in messages[0]["content"]
            return {"text": "REJECTS"}
    out = classify("we will not use the old plan; it is superseded", "the old plan",
                   backend=FakeBackend(), model="x")
    assert out["verdict"] == "rejects"
