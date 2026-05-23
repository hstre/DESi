"""v4.9 — inversion guards mirror runtime behaviour."""
from __future__ import annotations

from desi.content_inversion_patch import (
    CONTRADICTION_PAIRS, POLARITY_PAIRS,
    any_inversion_fires,
    contradiction_fires_on_text, polarity_fires_on_text,
)
from desi.logic.inference import (
    _V49_CONTRADICTION_PAIRS, _V49_POLARITY_PAIRS,
)


def test_pair_tables_mirror_runtime() -> None:
    assert CONTRADICTION_PAIRS == _V49_CONTRADICTION_PAIRS
    assert POLARITY_PAIRS == _V49_POLARITY_PAIRS


def test_contradiction_fires_on_x2_v028() -> None:
    text = (
        "The statute of limitations bars claims filed late. "
        "The plaintiff filed within the limitation period, "
        "past the six-year limit. "
        "Therefore the claim is time-barred."
    )
    assert contradiction_fires_on_text(text)
    assert any_inversion_fires(text)


def test_polarity_fires_on_d1_i007() -> None:
    text = (
        "Stress-test electrodes lost capacity at higher "
        "discharge rates. "
        "Post-mortem imaging showed lithium plating on the "
        "anode. "
        "Therefore high-rate cycling improved anode "
        "durability."
    )
    assert polarity_fires_on_text(text)
    assert any_inversion_fires(text)


def test_does_not_fire_on_simple_chain() -> None:
    text = (
        "Mice exposed to high-fat diet for twelve weeks "
        "gained body mass. "
        "Serum leptin concentrations rose in parallel. "
        "Therefore the diet drove adiposity through "
        "hormonal pathways."
    )
    assert not any_inversion_fires(text)


def test_pair_requires_both_halves() -> None:
    """The guard requires *both* halves of a contradiction
    pair to appear; one alone does not suffice."""
    # premise half only (legal valid chain — within the
    # limitation period without time-barred conclusion).
    text = (
        "The tenant gave timely thirty-day notice within "
        "the limitation period before the deadline. "
        "Records confirm the timely entry on the docket. "
        "Therefore the notice satisfied the procedural "
        "requirement."
    )
    assert not contradiction_fires_on_text(text)
