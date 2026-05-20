"""v26 - Rentschler follow-up paper sections.

Renders the 14 mandated sections of the Rentschler follow-up
through the v25 output-port machinery. Shared sections delegate
to the v25.1 arXiv section builder (so claims, numbers and
references are the same provenance-bound content); two sections
are specific to this paper: an explicit, mythology-free
statement of what DESi locally is, and a hedged Discussion of
the core thesis.
"""
from __future__ import annotations

from functools import lru_cache

from desi.icrl_followup_conditions import by_result_id
from desi.output_ports_arxiv import (
    build_section as _arxiv_section, resolve as _resolve_ref,
)
from desi.output_ports import BASE_PAPER_REF

# Section keys in the mandated order. Two keys are local to this
# paper; the rest reuse the v25.1 builder.
SECTION_ORDER: tuple[str, ...] = (
    "title", "abstract", "introduction", "related_work",
    "problem_statement", "desi_governance_layer",
    "experimental_conditions", "metrics", "results",
    "discussion", "limitations", "reproducibility_statement",
    "conclusion", "references",
)

_TITLES: dict[str, str] = {
    "title": "Title",
    "abstract": "Abstract",
    "introduction": "Introduction",
    "related_work": "Related Work",
    "problem_statement": "Problem Statement",
    "desi_governance_layer": "The DESi Governance Layer",
    "experimental_conditions": "Experimental Conditions",
    "metrics": "Metrics",
    "results": "Results",
    "discussion": "Discussion",
    "limitations": "Limitations",
    "reproducibility_statement": "Reproducibility Statement",
    "conclusion": "Conclusion",
    "references": "References",
}

# Markers that must be present in the DESi mechanism section, so
# a reader knows exactly (and only) what DESi is in this paper.
MECHANISM_MARKERS: tuple[str, ...] = (
    "read-only", "generator", "governor", "non-authoritative",
    "does not learn", "local to this", "complementary",
    "not a replacement",
)

# The core thesis, stated verbatim and hedged.
CORE_THESIS = (
    "Controlled exploratory pressure, implemented as a "
    "generator/governor split, may increase exploratory breadth "
    "in synthetic ICRL-style trajectory settings without "
    "increasing residual unsupported certainty, provided that "
    "the governance layer remains read-only, replay-stable, and "
    "non-authoritative."
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _base_cite() -> str:
    r = _resolve_ref(BASE_PAPER_REF)
    return f"[{r.authors}, {r.year}]"


def _title() -> str:
    r = _resolve_ref(BASE_PAPER_REF)
    return (
        "Controlled Exploratory Pressure as a Read-Only "
        "Governance Layer for In-Context Exploration: A "
        f"Synthetic Follow-Up to {r.authors} ({r.year})"
    )


def _desi_governance_layer() -> str:
    return (
        "In this paper, DESi denotes nothing more than a small, "
        "read-only governance layer over a synthetic exploration "
        "process; we use the name only as a local label and make "
        "no broader claim about it. Concretely, DESi is a "
        "generator/governor split: a generator agent proposes "
        "aggressive trajectories, and a governor reads them, "
        "classifies them by structure (not by reward) and "
        "assigns soft priority weights. The governor is "
        "read-only and non-authoritative: it never edits the "
        "policy, never injects reward, never deletes or pins a "
        "trajectory, and does not learn or optimise anything. "
        "DESi here is local to this synthetic study and "
        "complementary to reinforcement learning - not a "
        "replacement for it and not a general-purpose system - "
        "and we make no claim about it beyond this sandbox."
    )


def _discussion() -> str:
    r2 = _round(by_result_id("R2").value)
    r3 = _round(by_result_id("R3").value)
    return (
        "Our reading of these synthetic results is deliberately "
        "narrow. " + CORE_THESIS + " This is a hypothesis "
        "consistent with the sandbox measurements (novelty_gain "
        f"= {r2}, derived in v20.0/v21.0; residual_hallucination "
        f"= {r3}, derived in v20.1), not a demonstrated property "
        "of real reinforcement-learning systems. Whether the "
        "effect holds outside this synthetic corpus, and under a "
        "trained policy, remains an open question that we do not "
        f"address here {_base_cite()}."
    )


_LOCAL_BUILDERS = {
    "title": _title,
    "desi_governance_layer": _desi_governance_layer,
    "discussion": _discussion,
}


def section_title(section: str) -> str:
    if section not in _TITLES:
        raise KeyError(section)
    return _TITLES[section]


@lru_cache(maxsize=None)
def build_section(section: str) -> str:
    if section in _LOCAL_BUILDERS:
        return _LOCAL_BUILDERS[section]()
    # delegate shared sections to the v25.1 arXiv builder
    return _arxiv_section(section)


def build_sections() -> dict[str, str]:
    return {k: build_section(k) for k in SECTION_ORDER}


__all__ = [
    "CORE_THESIS",
    "MECHANISM_MARKERS",
    "SECTION_ORDER",
    "build_section",
    "build_sections",
    "section_title",
]
