"""v1.7 — every BLOCKED result carries an explicit BlockingReason.

The five values form a closed enum. Each test pins one classification
path so future refactors cannot silently drop or remap a reason.
"""
from __future__ import annotations

from desi.recursive import (
    BlockingReason,
    RecursiveResolver,
    ResolutionState,
)


def _resolve(text, **kwargs):
    return RecursiveResolver().resolve(text, **kwargs)


# ---------------------------------------------------------------------------
# Closed enum
# ---------------------------------------------------------------------------


def test_blocking_reason_has_exactly_five_values() -> None:
    values = {r.value for r in BlockingReason}
    assert values == {
        "invalid_inference",
        "real_logical_gap",
        "parser_unsupported_form",
        "authority_claim",
        "counterexample_found",
    }


# ---------------------------------------------------------------------------
# Resolved results carry no blocking_reason
# ---------------------------------------------------------------------------


def test_complete_result_has_no_blocking_reason() -> None:
    r = _resolve("All men are mortal. Socrates is a man. "
                  "Therefore Socrates is mortal.")
    assert r.final_state is ResolutionState.RESOLUTION_COMPLETE
    assert r.blocking_reason is None


# ---------------------------------------------------------------------------
# INVALID_INFERENCE
# ---------------------------------------------------------------------------


def test_bad_transitivity_blocks_with_invalid_inference() -> None:
    """B6: a -> b. b -> c. Therefore a -> d. — bad transitivity."""
    r = _resolve("a -> b. b -> c. Therefore a -> d.")
    assert r.final_state is ResolutionState.RESOLUTION_BLOCKED
    assert r.blocking_reason is BlockingReason.INVALID_INFERENCE


# ---------------------------------------------------------------------------
# PARSER_UNSUPPORTED_FORM
# ---------------------------------------------------------------------------


def test_atomic_conclusion_blocks_with_parser_unsupported_form() -> None:
    """A2: "will get wet" is positive future; the parser cannot
    structure it as PARTICULAR. The block reason must reflect
    *parser failure*, not *invalid inference*."""
    r = _resolve("It is raining. Therefore the barbecue will get wet.")
    assert r.final_state is ResolutionState.RESOLUTION_BLOCKED
    assert r.blocking_reason is BlockingReason.PARSER_UNSUPPORTED_FORM


def test_no_explicit_chain_blocks_with_parser_unsupported_form() -> None:
    """Pure statement with no Therefore: parser sees no chain."""
    r = _resolve("Water boils at 100C.")
    assert r.final_state is ResolutionState.RESOLUTION_BLOCKED
    assert r.blocking_reason is BlockingReason.PARSER_UNSUPPORTED_FORM


# ---------------------------------------------------------------------------
# AUTHORITY_CLAIM
# ---------------------------------------------------------------------------


def test_authority_premise_blocks_with_authority_claim() -> None:
    r = _resolve("Professor X says quantum gravity is solved.")
    assert r.final_state is ResolutionState.RESOLUTION_BLOCKED
    assert r.blocking_reason is BlockingReason.AUTHORITY_CLAIM


# ---------------------------------------------------------------------------
# COUNTEREXAMPLE_FOUND — both explicit and v1.6 auto-veto
# ---------------------------------------------------------------------------


def test_explicit_roof_counterexample_blocks_with_counterexample_found() -> None:
    r = _resolve(
        "It is raining. Therefore the street is wet.",
        additional_conditions=("the street has a roof",),
    )
    assert r.final_state is ResolutionState.RESOLUTION_BLOCKED
    assert r.blocking_reason is BlockingReason.COUNTEREXAMPLE_FOUND


def test_generic_fallback_blocks_with_counterexample_found() -> None:
    """v1.6 SKEPTIC auto-veto on GENERIC_FALLBACK bridges also lands
    under COUNTEREXAMPLE_FOUND (the auto-generated adversarial
    conditions are the counterexamples)."""
    r = _resolve(
        "The temperature is freezing. Therefore the water is ice."
    )
    assert r.final_state is ResolutionState.RESOLUTION_BLOCKED
    assert r.blocking_reason is BlockingReason.COUNTEREXAMPLE_FOUND


# ---------------------------------------------------------------------------
# to_dict surfaces blocking_reason
# ---------------------------------------------------------------------------


def test_to_dict_includes_blocking_reason_value() -> None:
    r = _resolve("Professor X says quantum gravity is solved.")
    d = r.to_dict()
    assert d["blocking_reason"] == "authority_claim"


def test_to_dict_blocking_reason_is_none_for_completed_runs() -> None:
    r = _resolve("All men are mortal. Socrates is a man. "
                  "Therefore Socrates is mortal.")
    d = r.to_dict()
    assert d["blocking_reason"] is None
