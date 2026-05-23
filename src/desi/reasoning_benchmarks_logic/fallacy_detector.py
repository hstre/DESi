"""v36.2 - deterministic logical-form analyzer.

Classifies a logical form as valid or as a named fallacy. This is a
fixed, deterministic mapping over canonical logical forms (modus
ponens / tollens are valid; affirming the consequent, denying the
antecedent, hasty generalization and false dichotomy are fallacies).
No LLM, no false confidence: an unrecognised form is reported as
'unknown' rather than asserted valid.
"""
from __future__ import annotations

VALID_FORMS: frozenset[str] = frozenset({
    "modus_ponens", "modus_tollens",
})

FALLACY_FORMS: dict[str, str] = {
    "affirming_consequent": "affirming_consequent",
    "denying_antecedent": "denying_antecedent",
    "hasty_generalization": "hasty_generalization",
    "false_dichotomy": "false_dichotomy",
}


def is_valid(form: str) -> bool:
    return form in VALID_FORMS


def detect_fallacy(form: str) -> str:
    """Return the fallacy name, 'none' for a valid form, or 'unknown'
    for an unrecognised form (never silently 'valid')."""
    if form in VALID_FORMS:
        return "none"
    if form in FALLACY_FORMS:
        return FALLACY_FORMS[form]
    return "unknown"


def has_fallacy(form: str) -> bool:
    return form in FALLACY_FORMS


__all__ = [
    "FALLACY_FORMS",
    "VALID_FORMS",
    "detect_fallacy",
    "has_fallacy",
    "is_valid",
]
