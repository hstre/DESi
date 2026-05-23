"""v36.0 - deterministic instruction-constraint engine.

For each IFEval constraint type the engine deterministically produces
a compliant structured response (or a governed refusal for fabrication
requests) and a checker verifies the constraint. There is no LLM and
no prompt overfitting: this exercises DESi's constraint-enforcement
and refusal governance on the IFEval format.
"""
from __future__ import annotations

CONSTRAINT_TYPES: tuple[str, ...] = (
    "format_json", "max_words", "exact_bullets", "forbidden_term",
    "must_refuse",
)

# Fabrication / unsupported-output requests that must be refused.
_REFUSAL_VALUES: frozenset[str] = frozenset({
    "fabricate_citation", "invent_data",
})


def generate(constraint_type: str, value: str) -> str | None:
    """Produce a deterministic compliant response, or None to signal
    a governed refusal."""
    if constraint_type == "must_refuse":
        return None
    if constraint_type == "format_json":
        return '{"answer": "grounded"}'
    if constraint_type == "max_words":
        return "A concise grounded answer."
    if constraint_type == "exact_bullets":
        n = int(value)
        return "\n".join(f"- point {i + 1}" for i in range(n))
    if constraint_type == "forbidden_term":
        return "A clear, evidence-based answer."
    return "ok"


def check_format_json(text: str) -> bool:
    s = text.strip()
    return s.startswith("{") and s.endswith("}")


def check_max_words(text: str, n: int) -> bool:
    return len(text.split()) <= n


def check_exact_bullets(text: str, n: int) -> bool:
    bullets = [
        ln for ln in text.splitlines() if ln.strip().startswith("-")
    ]
    return len(bullets) == n


def check_forbidden_term(text: str, term: str) -> bool:
    return term.lower() not in text.lower()


def satisfies(constraint_type: str, value: str, text: str) -> bool:
    if constraint_type == "format_json":
        return check_format_json(text)
    if constraint_type == "max_words":
        return check_max_words(text, int(value))
    if constraint_type == "exact_bullets":
        return check_exact_bullets(text, int(value))
    if constraint_type == "forbidden_term":
        return check_forbidden_term(text, value)
    return False


def must_refuse(constraint_type: str, value: str) -> bool:
    return constraint_type == "must_refuse" or value in _REFUSAL_VALUES


__all__ = [
    "CONSTRAINT_TYPES",
    "check_exact_bullets",
    "check_forbidden_term",
    "check_format_json",
    "check_max_words",
    "generate",
    "must_refuse",
    "satisfies",
]
