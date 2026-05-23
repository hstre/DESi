"""v4.7 — modality guard mirrors runtime behaviour."""
from __future__ import annotations

from desi.modality_patch import (
    MODAL_TOKENS, PAST_AUXILIARIES,
    all_premises_past, conclusion_has_modal, fires_on_text,
)
from desi.logic.inference import (
    _V47_MODAL_TOKENS, _V47_PAST_AUXILIARIES,
)


def test_modality_constants_mirror_runtime() -> None:
    assert MODAL_TOKENS == _V47_MODAL_TOKENS
    assert PAST_AUXILIARIES == _V47_PAST_AUXILIARIES
    # All-grammatical, closed sets.
    assert "will" in MODAL_TOKENS
    assert "cannot" in MODAL_TOKENS
    assert "was" in PAST_AUXILIARIES
    assert "had" in PAST_AUXILIARIES


def test_fires_on_canonical_v46_correlation_case() -> None:
    text = (
        "A study showed correlation between coffee and "
        "longer life. The study controlled for several "
        "lifestyle variables. Therefore drinking more "
        "coffee will extend a person's lifespan."
    )
    assert fires_on_text(text)
    assert conclusion_has_modal(text)
    assert all_premises_past(text)


def test_fires_on_canonical_v46_sample_to_universal_case() -> None:
    text = (
        "The candidate appeared tired during the debate. "
        "Body language analysts identified signs of "
        "distress. Therefore the candidate cannot withstand "
        "the demands of office."
    )
    assert fires_on_text(text)


def test_does_not_fire_on_consistent_chain() -> None:
    text = (
        "Mice exposed to high-fat diet gained body mass. "
        "Serum leptin concentrations rose in parallel. "
        "Therefore the diet drove adiposity through "
        "hormonal pathways."
    )
    assert not fires_on_text(text)
