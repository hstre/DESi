"""v5.2 — new evaluation corpus."""
from __future__ import annotations

from collections import Counter

from desi.taxonomy_generalization.corpus import all_chains
from desi.taxonomy_generalization.enums import (
    GeneralizationDomain, GeneralizationGroundTruth,
)


def test_corpus_size_at_least_five_hundred() -> None:
    assert len(all_chains()) >= 500


def test_each_domain_at_least_one_hundred() -> None:
    by = Counter(c.domain for c in all_chains())
    for d in GeneralizationDomain:
        assert by[d.value] >= 100, (d.value, by[d.value])


def test_five_domains_present() -> None:
    domains = {c.domain for c in all_chains()}
    expected = {d.value for d in GeneralizationDomain}
    assert domains == expected


def test_chain_ids_unique() -> None:
    ids = [c.chain_id for c in all_chains()]
    assert len(set(ids)) == len(ids)


def test_ground_truth_in_closed_set() -> None:
    allowed = {g.value for g in GeneralizationGroundTruth}
    for c in all_chains():
        assert c.ground_truth in allowed


def test_ground_truth_balanced_within_twenty_percent() -> None:
    counts = Counter(c.ground_truth for c in all_chains())
    mean = sum(counts.values()) / 3
    for label in ("VALID", "INVALID", "AMBIGUOUS"):
        share = counts[label]
        assert abs(share - mean) / mean <= 0.20, (
            label, share, mean,
        )


def test_no_v52_chain_reuses_v50_text() -> None:
    from desi.methodology_transfer.corpus import (
        all_chains as v50_all,
    )
    v50_texts = {c.text for c in v50_all()}
    for c in all_chains():
        assert c.text not in v50_texts, c.chain_id


def test_v52_domains_disjoint_from_v50() -> None:
    from desi.methodology_transfer.enums import (
        TransferDomain,
    )
    v50_doms = {d.value for d in TransferDomain}
    v52_doms = {d.value for d in GeneralizationDomain}
    assert v50_doms & v52_doms == set()
