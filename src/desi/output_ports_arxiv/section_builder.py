"""v25.1 - arXiv section builder.

Builds the body of each required section from the epistemic
state: claims and provenance from the v24 query layer, derived
result values and metric definitions from the v23 conditions
layer, sandbox limits and replay hashes. Every reported number
carries its sprint source, so no result is naked.
"""
from __future__ import annotations

from dataclasses import dataclass

from desi.icrl_followup_conditions import (
    definitions, results, sandbox_limits,
)
from desi.epistemic_graph_queries import scientific_traceability
from desi.output_ports import BASE_PAPER_REF

from .citation_rules import external_claims
from .reference_manager import references_body, resolve


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class ResultLine:
    metric_name: str
    value: float
    sprint_source: str

    def is_derived(self) -> bool:
        return bool(self.sprint_source)


def result_lines() -> tuple[ResultLine, ...]:
    return tuple(
        ResultLine(r.metric_name, _round(r.value), r.sprint_source)
        for r in results()
    )


def _base_cite() -> str:
    r = resolve(BASE_PAPER_REF)
    return f"[{r.authors}, {r.year}]"


def _title() -> str:
    return (
        "A Read-Only Governance Layer for In-Context "
        "Exploration: A Small Synthetic Follow-Up Study"
    )


def _abstract() -> str:
    return (
        "We report a small, fully synthetic follow-up study on "
        "a read-only epistemic governance layer over an "
        "in-context reinforcement-learning-style exploration "
        f"process, complementary to the base paper {_base_cite()}. "
        "On a closed synthetic state space, soft re-weighting of "
        "redundant trajectories reduced search redundancy while "
        "preserving novel-state reachability, and a "
        "generator/governor split increased distinct-state "
        "coverage. Every reported number is derived from a named "
        "sprint and is replay-exact. We make no claim beyond the "
        "sandbox."
    )


def _introduction() -> str:
    return (
        f"The base paper {_base_cite()} studies in-context "
        "reinforcement learning for variable action spaces and "
        "skill stitching. We follow up one narrow question from "
        "its Section 4.6 discussion of limitations: can a "
        "separate, read-only governance layer mark redundancy "
        "and contain unsupported certainty without replacing the "
        "policy? This is an engineering study on a synthetic "
        "corpus, not a claim about learning systems in general."
    )


def _related_work() -> str:
    lines = [
        f"This work is a complementary follow-up to the base "
        f"paper {_base_cite()}, which identifies several open "
        "in-context exploration problems in its Section 4.6 "
        "limitations. We address them with a read-only "
        "governance layer rather than a replacement for "
        "reinforcement learning.",
        "",
    ]
    for c in external_claims():
        keys = ", ".join(c.reference_keys)
        lines.append(f"- {c.text} ({keys})")
    return "\n".join(lines)


def _problem_statement() -> str:
    return (
        f"Following the base paper {_base_cite()}, we target "
        "three open exploration problems on a synthetic corpus: "
        "exploration collapse into repeated suboptimal "
        "behaviour, sparse-reward failure where the goal stays "
        "undiscovered, and repetitive trajectories that provide "
        "little new information."
    )


def _method() -> str:
    return (
        "A read-only governance layer reads trajectories, "
        "classifies them by structure (not reward), assigns soft "
        "priority weights and never deletes or pins a trajectory. "
        "A second configuration adds a generator agent whose "
        "aggressive trajectories the governor scores. The layer "
        "is complementary and read-only; it neither learns nor "
        "optimises a reward."
    )


def _experimental_conditions() -> str:
    lines = [
        "All trajectories, states and rewards are synthetic "
        "fixtures. Provenance of each result is named below "
        "(DESi-only baseline = v19, DESi + Wild Explorer = v20, "
        "comparison = v21).",
        "",
    ]
    for r in results():
        lines.append(
            f"- {r.metric_name} (source {r.sprint_source}): "
            f"{r.conditions}"
        )
    return "\n".join(lines)


def _metrics() -> str:
    lines = [
        "Every metric reported below carries an explicit "
        "definition and range:",
        "",
    ]
    for d in definitions():
        lines.append(
            f"- **{d.name}** [{d.range_lo}, {d.range_hi}] "
            f"(source {d.source}): {d.definition}"
        )
    return "\n".join(lines)


def _results() -> str:
    lines = [
        "On the synthetic corpus, with each number derived from "
        "its named sprint:",
        "",
    ]
    for line in result_lines():
        lines.append(
            f"- {line.metric_name} = {line.value} "
            f"(derived in {line.sprint_source})"
        )
    return "\n".join(lines)


def _limitations() -> str:
    lines = [
        "These observations are limited to a small synthetic "
        "state space and a fixed trajectory set:",
        "",
    ]
    for limit in sandbox_limits():
        lines.append(f"- {limit.statement}")
    return "\n".join(lines)


def _reproducibility_statement() -> str:
    rl = result_lines()
    traceable = _round(scientific_traceability())
    return (
        "Every metric is computed by deterministic arithmetic "
        "over fixed synthetic fixtures (no PRNG, no learned "
        f"model). All {len(rl)} reported numbers are derived "
        "from a named sprint and recomputed bit-identically, "
        "with a deterministic hash chain recorded across phases "
        f"(claim traceability {traceable}). The study is "
        "replay-exact and scoped to the sandbox."
    )


def _conclusion() -> str:
    return (
        "As a complementary follow-up to the base paper's "
        f"Section 4.6 open problems {_base_cite()}, a read-only "
        "governance layer reduced redundant search and contained "
        "unsupported certainty while preserving novelty and "
        "remaining replay-exact on a small synthetic corpus. We "
        "present this as a narrow, reproducible engineering "
        "result and leave evaluation beyond the sandbox to "
        "future work."
    )


_BUILDERS = {
    "title": _title,
    "abstract": _abstract,
    "introduction": _introduction,
    "related_work": _related_work,
    "problem_statement": _problem_statement,
    "method": _method,
    "experimental_conditions": _experimental_conditions,
    "metrics": _metrics,
    "results": _results,
    "limitations": _limitations,
    "reproducibility_statement": _reproducibility_statement,
    "conclusion": _conclusion,
    "references": references_body,
}


def build_section(section_key: str) -> str:
    builder = _BUILDERS.get(section_key)
    if builder is None:
        return ""
    return builder()


def build_sections() -> dict[str, str]:
    return {k: build_section(k) for k in _BUILDERS}


__all__ = [
    "ResultLine",
    "build_section",
    "build_sections",
    "result_lines",
]
