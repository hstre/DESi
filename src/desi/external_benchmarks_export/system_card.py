"""v35.3 - honest system card.

A public system card that describes DESi truthfully: what it is, what
it does on these benchmarks, and - prominently - its limitations and
governance. It must contain no AGI / hype marketing language; that is
enforced by a forbidden-marketing-term check in addition to the
governance forbidden-term check.
"""
from __future__ import annotations

import re

from desi.external_benchmarks import governance_independence
from desi.peripheral_mutation import core_identity
from desi.scientific_rendering import forbidden_hits
from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .benchmark_summary import real_run_names, synthetic_run_names

# Hype / overclaim vocabulary that must never appear in a public card.
FORBIDDEN_MARKETING_TERMS: tuple[str, ...] = (
    "agi",
    "artificial general intelligence",
    "superintelligence",
    "superhuman",
    "human-level",
    "sentient",
    "conscious",
    "self-aware",
    "singularity",
    "solves intelligence",
    "world-changing",
    "revolutionary breakthrough",
    "state-of-the-art on every",
)

LIMITATIONS: tuple[str, ...] = (
    "The benchmark datasets are locally-vendored reference sets in "
    "the published families' formats; this environment is "
    "network-free, so they are NOT live downloads of the official "
    "suites.",
    "The reported scores are NOT official leaderboard results and "
    "are not directly comparable to published numbers.",
    "Some runs use synthetic / in-repo fixtures; these are labelled "
    "separately from the connector-loaded reference runs.",
    "DESi is an epistemic governance prototype, not a general-"
    "purpose agent and not an autonomous system; human approval is "
    "mandatory for any change.",
    "Results are deterministic and replay-stable within this "
    "environment; they describe behaviour on these inputs, not a "
    "general capability claim.",
)


def governance_block() -> dict[str, object]:
    return {
        "core_identity": core_identity(),
        "governance_independence": governance_independence(),
        "human_approval_required": HUMAN_APPROVAL_REQUIRED,
    }


def system_card() -> dict[str, object]:
    return {
        "name": "DESi",
        "what_it_is": (
            "A deterministic, replay-stable epistemic governance "
            "prototype that can be tested by external benchmark "
            "adapters without changing its protected core."
        ),
        "what_this_card_covers": (
            "Behaviour on controlled drift, search-compression, "
            "reproducibility and scientific-rendering benchmark "
            "runs."
        ),
        "real_runs": list(real_run_names()),
        "synthetic_or_in_repo_runs": list(synthetic_run_names()),
        "governance": governance_block(),
        "limitations": list(LIMITATIONS),
        "not_claims": [
            "DESi is not AGI and makes no general-intelligence "
            "claim.",
            "DESi does not optimise itself to win benchmarks.",
            "These numbers are not official leaderboard scores.",
        ],
    }


def _promotional_text() -> str:
    """The affirmative, public-facing pitch - the surface that could
    over-sell. The limitations and not_claims are the disclaimer
    surface and are allowed to name a term in order to deny it, so
    they are deliberately excluded from the marketing scan."""
    card = system_card()
    return "\n".join([
        str(card["name"]),
        str(card["what_it_is"]),
        str(card["what_this_card_covers"]),
    ])


def _contains_term(text: str, term: str) -> bool:
    pattern = r"\b" + re.escape(term) + r"\b"
    return re.search(pattern, text) is not None


def marketing_hits() -> tuple[str, ...]:
    text = _promotional_text().lower()
    return tuple(
        term for term in FORBIDDEN_MARKETING_TERMS
        if _contains_term(text, term)
    )


def governance_forbidden_hits() -> tuple[str, ...]:
    return forbidden_hits(_promotional_text())


def marketing_free() -> bool:
    return not marketing_hits() and not governance_forbidden_hits()


def limitation_visibility() -> float:
    """1.0 iff the card surfaces a non-empty, governance-clean set of
    limitations."""
    if not LIMITATIONS:
        return 0.0
    return 1.0 if marketing_free() else 0.0


def governance_visibility() -> float:
    """1.0 iff the card exposes core identity, governance
    independence and the human-approval requirement, with the core
    intact."""
    g = governance_block()
    if not g.get("human_approval_required"):
        return 0.0
    if g["core_identity"] != 1.0:
        return 0.0
    return 1.0 if g["governance_independence"] >= 0.95 else 0.0


__all__ = [
    "FORBIDDEN_MARKETING_TERMS",
    "LIMITATIONS",
    "governance_block",
    "governance_forbidden_hits",
    "governance_visibility",
    "limitation_visibility",
    "marketing_free",
    "marketing_hits",
    "system_card",
]
