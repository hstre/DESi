"""v4.3 — verify marker tuples + contamination check."""
from __future__ import annotations

from desi.external_audit_patch import (
    PATCHED_CLUSTERS, all_extensions, contamination_check,
)
from desi.logic.inference import (
    _V43_AUTHORITY_LIKE_VERBS,
    _V43_NEGATION_EXTENSIONS,
    _V43_QUANTIFIER_EXTENSIONS,
)


def test_three_patched_clusters_named() -> None:
    assert PATCHED_CLUSTERS == (
        "HIDDEN_NEGATION",
        "QUANTIFIER_DRIFT",
        "AUTHORITY_CONTAMINATION",
    )


def test_extensions_mirror_runtime_tuples() -> None:
    ext = all_extensions()
    assert ext["HIDDEN_NEGATION"] == _V43_NEGATION_EXTENSIONS
    assert ext["QUANTIFIER_DRIFT"] == _V43_QUANTIFIER_EXTENSIONS
    assert ext["AUTHORITY_CONTAMINATION"] == (
        _V43_AUTHORITY_LIKE_VERBS
    )


def test_every_marker_is_space_padded() -> None:
    """All v4.3 markers must be authored as space-padded
    substrings to match the ``_contains_marker`` matcher used
    by ``_try_causal_chain``."""
    for tokens in all_extensions().values():
        for m in tokens:
            assert m.startswith(" "), m
            assert m.endswith(" "), m


def test_contamination_count_is_zero() -> None:
    rep = contamination_check()
    assert rep.total_contamination == 0, [
        (t.cluster, t.token, t.hits)
        for t in rep.per_token if t.hits
    ]
    assert rep.protected_pool_size > 0


def test_contamination_check_is_deterministic() -> None:
    a = contamination_check()
    b = contamination_check()
    assert a.to_dict() == b.to_dict()
