"""v4.5 — structural guard mirrors runtime behaviour."""
from __future__ import annotations

from desi.bidirectional_cycle_patch import (
    MIN_OVERLAP_PREMISES, MIN_OVERLAP_TOTAL,
    fires_on_text, overlap_signature,
)
from desi.logic.inference import (
    _V45_MIN_OVERLAP_PREMISES, _V45_MIN_OVERLAP_TOTAL,
)


def test_thresholds_mirror_runtime_constants() -> None:
    assert MIN_OVERLAP_PREMISES == _V45_MIN_OVERLAP_PREMISES == 2
    assert MIN_OVERLAP_TOTAL == _V45_MIN_OVERLAP_TOTAL == 3


def test_fires_on_known_v44_cycle() -> None:
    """D2I007 is the canonical BIDIRECTIONAL_CYCLE pattern."""
    text = (
        "Contract law voids unconscionable terms. "
        "The clause was negotiated freely by sophisticated "
        "parties. "
        "Therefore the clause is unconscionable as a matter "
        "of law."
    )
    assert fires_on_text(text)
    op, ot = overlap_signature(text)
    assert op >= MIN_OVERLAP_PREMISES
    assert ot >= MIN_OVERLAP_TOTAL


def test_does_not_fire_on_simple_two_premise_chain() -> None:
    """A clean cause-effect chain with no token cycle does not
    trigger the v4.5 guard."""
    text = (
        "Mice exposed to high-fat diet for twelve weeks "
        "gained significant body mass. "
        "Serum leptin concentrations rose in parallel. "
        "Therefore the diet drove adiposity through hormonal "
        "pathways."
    )
    assert not fires_on_text(text)
