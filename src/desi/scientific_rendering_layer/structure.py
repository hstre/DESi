"""v22.2 - the small paper-like document structure.

DESi assembles a short, sober, technically scoped document
from the v19-v21 results: Abstract, Motivation, Experimental
Setup, Results, Limitations, Conclusion. Every section is
fixed text (deterministic / replay-exact) and is written to
contain no forbidden term and no hype, with claims scoped to
the synthetic sandbox.
"""
from __future__ import annotations

# Closed, ordered section list (paper-compatible skeleton).
SECTION_ORDER: tuple[str, ...] = (
    "Abstract", "Motivation", "Experimental Setup",
    "Results", "Limitations", "Conclusion",
)

_SECTIONS: dict[str, str] = {
    "Abstract": (
        "We study a read-only epistemic governance layer over "
        "an in-context reinforcement-learning-style "
        "exploration process on a small synthetic state space. "
        "On this sandbox, soft re-weighting of redundant "
        "trajectories reduced search redundancy while "
        "preserving reachability of novel states, and a "
        "generator/governor split increased distinct-state "
        "coverage relative to a single conservative explorer. "
        "All reported numbers are deterministic and "
        "replay-exact. We make no claims beyond the sandbox."
    ),
    "Motivation": (
        "In-context exploration can collapse into repetitive "
        "loops and redundant search under sparse reward. We ask "
        "a narrow question: can a separate, read-only "
        "governance layer mark redundancy and contain "
        "unsupported certainty without replacing the policy or "
        "injecting reward? This is an engineering study on a "
        "synthetic corpus, not a claim about learning systems "
        "in general."
    ),
    "Experimental Setup": (
        "The exploration corpus is a synthetic, fixed set of "
        "trajectories over a discrete state space. The "
        "governance layer reads trajectories, classifies them "
        "by structure (not by reward), assigns soft priority "
        "weights, and never deletes or pins a trajectory. A "
        "second configuration adds a generator agent that "
        "proposes aggressive trajectories which the governance "
        "layer scores. Every metric is computed twice and "
        "compared, and a deterministic hash chain is recorded "
        "for replay."
    ),
    "Results": (
        "On the synthetic corpus, redundancy reduction reached "
        "0.90 with novel-state reachability preserved at 1.0. "
        "Adding the generator agent raised distinct-state "
        "coverage from 8 to 30 states while the uncontained "
        "hallucination rate stayed at 0.0 and authority drift "
        "stayed bounded. All configurations were replay-exact."
    ),
    "Limitations": (
        "These observations are limited to a small synthetic "
        "state space and a fixed trajectory set. We do not "
        "evaluate on real environments, we do not compare "
        "against trained reinforcement-learning baselines, and "
        "we make no claim that the behaviour generalises beyond "
        "the sandbox. The governance layer is optional and "
        "read-only; it neither learns nor optimises a reward."
    ),
    "Conclusion": (
        "On a small synthetic corpus, a read-only governance "
        "layer reduced redundant search and contained "
        "unsupported certainty while preserving novelty and "
        "remaining replay-exact, and a generator/governor split "
        "increased coverage without raising the uncontained "
        "hallucination rate. We present this as a narrow, "
        "reproducible engineering result and leave evaluation "
        "beyond the sandbox to future work."
    ),
}


def sections() -> dict[str, str]:
    return dict(_SECTIONS)


def section(name: str) -> str:
    return _SECTIONS[name]


def full_document(title: str | None = None) -> str:
    head = title or (
        "A Read-Only Governance Layer for In-Context "
        "Exploration: A Small Synthetic Study"
    )
    parts = [f"# {head}", ""]
    for name in SECTION_ORDER:
        parts.append(f"## {name}")
        parts.append("")
        parts.append(_SECTIONS[name])
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def all_sections_present() -> bool:
    return all(name in _SECTIONS for name in SECTION_ORDER)


__all__ = [
    "SECTION_ORDER",
    "all_sections_present",
    "full_document",
    "section",
    "sections",
]
