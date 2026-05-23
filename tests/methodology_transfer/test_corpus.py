"""v5.0 — corpus: five new domains, balanced labels."""
from __future__ import annotations

from collections import Counter

from desi.methodology_transfer.corpus import (
    TransferChain, all_chains,
)
from desi.methodology_transfer.enums import (
    TransferDomain, TransferGroundTruth,
)


def test_corpus_has_five_distinct_domains() -> None:
    domains = {c.domain for c in all_chains()}
    expected = {d.value for d in TransferDomain}
    assert domains == expected
    assert len(domains) == 5


def test_corpus_size_at_least_five_hundred() -> None:
    assert len(all_chains()) >= 500


def test_each_domain_has_at_least_one_hundred_chains() -> None:
    by_domain = Counter(c.domain for c in all_chains())
    for d in TransferDomain:
        assert by_domain[d.value] >= 100, (d.value, by_domain[d.value])


def test_ground_truth_labels_are_closed_set() -> None:
    allowed = {g.value for g in TransferGroundTruth}
    for c in all_chains():
        assert c.ground_truth in allowed, c


def test_ground_truth_balanced_within_twenty_percent() -> None:
    counts = Counter(c.ground_truth for c in all_chains())
    total = sum(counts.values())
    mean = total / 3
    for label in ("VALID", "INVALID", "AMBIGUOUS"):
        share = counts[label]
        assert abs(share - mean) / mean <= 0.20, (
            label, share, mean,
        )


def test_chain_ids_unique() -> None:
    ids = [c.chain_id for c in all_chains()]
    assert len(set(ids)) == len(ids)


def test_chain_text_nonempty_and_has_therefore() -> None:
    for c in all_chains():
        assert c.text.strip()
        assert "Therefore" in c.text or "therefore" in c.text


def test_no_v4_corpus_chain_reused() -> None:
    """v5.0 disallows reusing any v4.0 external_probe chain
    text. Direct equality check."""
    from desi.external_probe.corpus import (
        all_chains as v4_all,
    )
    v4_texts = {c.text for c in v4_all()}
    for c in all_chains():
        assert c.text not in v4_texts, c.chain_id


def test_v5_does_not_reuse_v4_domain_strings() -> None:
    """The five v5.0 domain values must differ from every
    v4.0 ``Domain`` value."""
    from desi.external_probe.enums import Domain as V4Domain
    v4_doms = {d.value for d in V4Domain}
    v5_doms = {d.value for d in TransferDomain}
    assert v5_doms & v4_doms == set()
