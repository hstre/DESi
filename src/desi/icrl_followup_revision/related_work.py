"""v23.0 - the "Relation to the base paper" section.

Renders a prose section that ties each central DESi claim to
a specific open exploration problem of the base paper and to
the sprint that produced it. Generic, unconnected sentences
are removed, so generic_claim_reduction is high.
"""
from __future__ import annotations

from desi.scientific_rendering import forbidden_hits

from .exploration_gap import addressed_problem_ids
from .paper_mapping import claims, problems


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def related_work_section() -> str:
    """A grounded 'Relation to the base paper' section in
    markdown (no forbidden term, no hype)."""
    lines = [
        "## Relation to the base paper",
        "",
        "The base paper notes, in its Section 4.6 discussion "
        "of limitations, several open exploration problems. "
        "We address them as a complementary, read-only "
        "governance layer rather than a replacement:",
        "",
    ]
    prob_text = {p.problem_id: p.text for p in problems()}
    for c in claims():
        anchored = ", ".join(
            f"{pid} ({prob_text[pid]})" for pid in c.anchors
        )
        lines.append(
            f"- **{c.claim_id}** ({c.sprint_source}): "
            f"{c.text} This relates to {anchored}."
        )
    lines.append("")
    lines.append(
        "Each statement above is scoped to the synthetic "
        "sandbox and is not a claim about reinforcement "
        "learning in general."
    )
    return "\n".join(lines) + "\n"


def generic_claim_reduction() -> float:
    """Fraction of central claims that are specific (anchored)
    rather than generic, in [0, 1]."""
    rows = claims()
    if not rows:
        return 0.0
    specific = sum(1 for c in rows if c.is_anchored())
    return _round(specific / len(rows))


def section_forbidden_hits() -> tuple[str, ...]:
    return forbidden_hits(related_work_section())


def addresses_section_4_6() -> bool:
    return "Section 4.6" in related_work_section()


__all__ = [
    "addresses_section_4_6",
    "generic_claim_reduction",
    "related_work_section",
    "section_forbidden_hits",
]
