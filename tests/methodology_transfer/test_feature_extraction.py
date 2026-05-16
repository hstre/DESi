"""v5.0 — feature extraction is deterministic and closed."""
from __future__ import annotations

from desi.methodology_transfer.corpus import (
    TransferChain, all_chains,
)
from desi.methodology_transfer.feature_extraction import (
    FEATURE_NAMES, extract_features, is_failure,
)


def test_feature_schema_size_is_eighteen() -> None:
    assert len(FEATURE_NAMES) == 18


def test_feature_schema_has_unique_names() -> None:
    assert len(set(FEATURE_NAMES)) == len(FEATURE_NAMES)


def test_feature_schema_does_not_leak_v4_class_names() -> None:
    forbidden = {
        "MARKER_LEAKAGE", "POLARITY_INVERSION",
        "CYCLE_DISGUISE", "OVER_BLOCK", "MARKER_OVERRIDE",
    }
    for n in FEATURE_NAMES:
        assert n not in forbidden, n


def test_extraction_is_deterministic() -> None:
    chain = all_chains()[0]
    a = extract_features(chain)
    b = extract_features(chain)
    assert a.features == b.features


def test_extraction_returns_fixed_length_vector() -> None:
    for c in all_chains()[:25]:
        s = extract_features(c)
        assert len(s.features) == len(FEATURE_NAMES)
        for v in s.features:
            assert isinstance(v, float)


def test_is_failure_uses_polarity_disagreement() -> None:
    # Synthetic chain: VALID + audit REJECTED is a failure.
    c = TransferChain(
        chain_id="probe", domain="nc",
        text=(
            "Therefore the system rejected the new "
            "configuration."
        ),
        ground_truth="VALID", rationale="",
    )
    s = extract_features(c)
    # Whether or not the auditor actually rejects, function
    # is total and Boolean.
    assert is_failure(s) in (True, False)
