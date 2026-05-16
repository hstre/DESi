"""v5.3 — per-pair rewrite audit."""
from __future__ import annotations

from desi.corpus_bias_audit.diff import (
    SAFE_PROBE_CLASSES, audit_pair,
)
from desi.corpus_bias_audit.enums import RewriteKind
from desi.corpus_bias_audit.raw_corpus import all_pairs


def test_six_safe_probe_classes() -> None:
    assert len(SAFE_PROBE_CLASSES) == 6


def test_audits_for_every_pair() -> None:
    pairs = all_pairs()
    audits = [audit_pair(p) for p in pairs]
    assert len(audits) == len(pairs)


def test_label_preservation_is_universal() -> None:
    pairs = all_pairs()
    for p in pairs:
        a = audit_pair(p)
        assert a.label_preservation is True


def test_rewrite_kind_in_closed_set() -> None:
    allowed = {k.value for k in RewriteKind}
    for p in all_pairs():
        assert audit_pair(p).rewrite_kind in allowed


def test_no_rewrite_kind_for_untouched_chains() -> None:
    for p in all_pairs():
        if not p.was_rewritten:
            assert audit_pair(p).rewrite_kind == (
                RewriteKind.NONE.value
            )


def test_audit_is_deterministic() -> None:
    p = all_pairs()[0]
    a = audit_pair(p)
    b = audit_pair(p)
    assert a.to_dict() == b.to_dict()


def test_semantic_similarity_in_unit_interval() -> None:
    for p in all_pairs():
        sim = audit_pair(p).semantic_similarity
        assert 0.0 <= sim <= 1.0
