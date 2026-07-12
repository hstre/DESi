"""Correction-packet actuator tests (deterministic, no network).

Locks: it fires ONLY at risk (never on clean cases), it is built from the report's status fields, it
stays short (capped), and it carries the recovery target."""
from __future__ import annotations

from desi_router.governance import build_correction_packet, packet_applies, report_from_snapshot
from desi_router.governance.benchmark.cases import _Snap


def _rep(**kw):
    kw.setdefault("extraction_confidence", 0.95)
    kw.setdefault("state_recall_estimate", 1.0)
    return report_from_snapshot("t", _Snap(), **kw)


def test_does_not_fire_on_a_clean_case():
    r = _rep(selected_claim_ids=("C1",), selected_claim_texts=("the rate limit is 100/min",))
    assert packet_applies(r) is False


def test_fires_when_invalidated_claim_is_touched():
    r = _rep(selected_claim_ids=("C1",), selected_claim_texts=("roll out via a 5% canary",),
             invalidated_claim_ids=("D9",), invalidated_claim_texts=("ship to 100% of users",),
             task_touches_invalidated=True)
    assert packet_applies(r) is True


def test_fires_on_open_conflict_recovery_and_verifier_failure():
    conf = report_from_snapshot(
        "t", _Snap(conflicts=(("K1", "cost", ("a", "b")),)),
        selected_claim_ids=("C1",), selected_claim_texts=("x",),
        answer_requires_conflict_resolution=True, extraction_confidence=0.9, state_recall_estimate=1.0)
    assert packet_applies(conf) is True
    clean = _rep(selected_claim_ids=("C1",), selected_claim_texts=("x",))
    assert packet_applies(clean, recovery_mode=True) is True
    assert packet_applies(clean, verifier_failed_once=True) is True


def test_packet_is_built_from_status_and_carries_recovery_target():
    r = _rep(selected_claim_ids=("C17", "C18"),
             selected_claim_texts=("the current decision is schema-per-tenant",
                                   "the earlier global-schema option was superseded"),
             invalidated_claim_ids=("C04",),
             invalidated_claim_texts=("global schema as final architecture",),
             task_touches_invalidated=True)
    p = build_correction_packet(r)
    assert p.startswith("EPISTEMIC CORRECTION PACKET")
    assert "Current valid state:" in p and "[C17]" in p and "schema-per-tenant" in p
    assert "Invalidated / superseded" in p and "[C04]" in p
    assert "Recovery target:" in p and "Answer from the current valid state" in p


def test_packet_is_capped_short():
    big = tuple(f"a very long claim number {i} " * 20 for i in range(20))
    r = _rep(selected_claim_ids=tuple(f"C{i}" for i in range(20)), selected_claim_texts=big)
    p = build_correction_packet(r, max_chars=1200)
    assert len(p) <= 1220                              # capped, with the truncation marker
