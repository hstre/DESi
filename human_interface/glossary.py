"""Plain-language translation layer: DESi-internal terms -> what a normal person understands.

The Wild Brother's #1 lazy-user complaint was jargon. Every user-facing string in the human
interface routes through `say()` so no internal term (branch, drift, epistemic state, recovery,
concept gate, replay) is ever shown raw. This is a surface-only mapping; it changes no core code.
"""
from __future__ import annotations

PLAIN = {
    "epistemic state": "what's known so far",
    "epistemic": "knowledge",
    "drift": "the topic quietly wandering off",
    "concept gate": "a yes/no quality check",
    "gate": "check",
    "recoverability": "whether you can still trace things back",
    "recovery": "tracing back to the source",
    "replay hash": "a fingerprint that proves the result is reproducible",
    "replay": "reproducible re-run",
    "branch": "a saved alternative version",
    "anchor": "a pointer back to the exact spot in the text",
    "invariant": "a rule that never changes",
    "trajectory": "the path the work took",
    "governance": "automatic quality control",
    "Class A": "passed all checks",
    "verdict": "result",
    "node reduction": "how much was trimmed",
    "ungrounded token": "a claim with no source",
}


def say(text: str) -> str:
    """Replace internal terms with plain language (longest terms first to avoid partial hits)."""
    out = text
    for term in sorted(PLAIN, key=len, reverse=True):
        for variant in (term, term.capitalize()):
            if variant in out:
                repl = PLAIN[term]
                repl = repl if variant[0].islower() else repl[0].upper() + repl[1:]
                out = out.replace(variant, repl)
    return out


def explain(term: str) -> str:
    return PLAIN.get(term.lower(), term)
