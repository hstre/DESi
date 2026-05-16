"""v5.0 — probe definitions are newly named and closed."""
from __future__ import annotations

from desi.methodology_transfer.probe_generator import (
    ProbeType, generate_probes_for_taxonomy, probe_fires,
)
from desi.methodology_transfer.taxonomy import TaxonomyClass


# Closed list of v4 probe ids that must NOT be reused.
_V4_PROBE_IDS: frozenset[str] = frozenset({
    "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9",
    "W1", "W2", "W3", "W4", "W5",
    "S1", "S2", "S3", "S4", "S5",
    "M1", "M2", "M3",
    "G1", "G2",
})


def test_probe_ids_are_newly_generated() -> None:
    names = tuple(c.value for c in TaxonomyClass)
    for p in generate_probes_for_taxonomy(names):
        assert p.probe_id not in _V4_PROBE_IDS
        assert p.probe_id.startswith("MT-")


def test_probe_ids_unique() -> None:
    names = tuple(c.value for c in TaxonomyClass)
    ids = [p.probe_id for p in generate_probes_for_taxonomy(names)]
    assert len(set(ids)) == len(ids)


def test_probe_type_is_closed_enum() -> None:
    allowed = {t.value for t in ProbeType}
    names = tuple(c.value for c in TaxonomyClass)
    for p in generate_probes_for_taxonomy(names):
        assert p.probe_type in allowed


def test_probe_predicate_total_and_bool() -> None:
    sample = (
        "Some premise. Another premise. Therefore the "
        "claim follows."
    )
    for c in TaxonomyClass:
        result = probe_fires(c.value, sample)
        assert isinstance(result, bool)


def test_unknown_cluster_probe_does_not_fire() -> None:
    assert probe_fires(
        "MT_OTHER",
        "Premise one. Premise two. Therefore conclusion.",
    ) is False
    assert probe_fires(
        "no_such_cluster",
        "Premise one. Premise two. Therefore conclusion.",
    ) is False
