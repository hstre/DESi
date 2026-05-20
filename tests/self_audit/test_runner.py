"""End-to-end tests for v3.0 SelfAuditRunner (Aufgabe 7)."""
from __future__ import annotations

from desi.self_audit import (
    SelfAuditReport,
    SelfAuditRunner,
)


def test_runner_returns_self_audit_report() -> None:
    rep = SelfAuditRunner().run()
    assert isinstance(rep, SelfAuditReport)


def test_runner_indexes_at_least_ten_documents() -> None:
    rep = SelfAuditRunner().run()
    assert rep.total_documents >= 10


def test_runner_extracts_at_least_one_hundred_claims() -> None:
    """Aufgabe success-criterion: claims >= 100."""
    rep = SelfAuditRunner().run()
    assert rep.total_claims >= 100, (
        f"only {rep.total_claims} claims extracted"
    )


def test_self_deception_rate_in_unit_interval() -> None:
    rep = SelfAuditRunner().run()
    assert 0.0 <= rep.self_deception_rate <= 1.0


def test_verdict_counts_sum_to_total() -> None:
    rep = SelfAuditRunner().run()
    sum_ = (rep.verified_claims
            + rep.hash_mismatch_claims
            + rep.value_mismatch_claims
            + rep.ambiguous_claims)
    # missing_artifact = unverifiable - (hash + value + ambiguous)
    missing = (rep.unverifiable_claims
               - rep.hash_mismatch_claims
               - rep.value_mismatch_claims
               - rep.ambiguous_claims)
    assert sum_ + missing == rep.total_claims


def test_two_runs_produce_identical_replay_hash() -> None:
    a = SelfAuditRunner().run()
    b = SelfAuditRunner().run()
    assert a.replay_hash == b.replay_hash


def test_two_runs_produce_identical_counts() -> None:
    a = SelfAuditRunner().run()
    b = SelfAuditRunner().run()
    assert a.total_documents == b.total_documents
    assert a.total_claims == b.total_claims
    assert a.verified_claims == b.verified_claims
    assert a.unverifiable_claims == b.unverifiable_claims
    assert a.contradictions_count == b.contradictions_count
    assert a.drift_findings_count == b.drift_findings_count


def test_report_to_dict_round_trip_shape() -> None:
    rep = SelfAuditRunner().run()
    d = rep.to_dict()
    for k in (
        "total_documents", "total_claims", "verified_claims",
        "unverifiable_claims", "hash_mismatch_claims",
        "value_mismatch_claims", "ambiguous_claims",
        "contradictions_count", "drift_findings_count",
        "self_deception_rate", "replay_hash",
    ):
        assert k in d


def test_runner_finds_required_memory_docs() -> None:
    import pathlib
    rep = SelfAuditRunner().run()
    indexed = {pathlib.Path(d.path).name for d in rep.documents}
    for required in ("v2_7.md", "v2_8.md", "v2_9.md"):
        assert required in indexed
