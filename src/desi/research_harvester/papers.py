"""v27.0 - the harvested paper corpus (synthetic + one anchor).

A deterministic fixture corpus standing in for an arXiv/SSRN
harvest in the AI/ML topic areas. Exactly one paper is real (the
base paper, the established anchor); every other paper is
explicitly synthetic and illustrative - nothing here is a
fabricated real citation. Each paper is decomposed into typed
claims, methods, metrics, datasets, assumptions and relations.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .claims import Claim
from .metadata import PaperMetadata
from .taxonomy import ClaimClass as K
from .taxonomy import SOURCES, TOPIC_AREAS


@dataclass(frozen=True)
class PaperRecord:
    metadata: PaperMetadata
    claims: tuple[Claim, ...]
    methods: tuple[str, ...]
    metrics: tuple[str, ...]
    datasets: tuple[str, ...]
    assumptions: tuple[str, ...]
    extends: tuple[str, ...] = field(default_factory=tuple)
    conflicts: tuple[str, ...] = field(default_factory=tuple)

    @property
    def paper_id(self) -> str:
        return self.metadata.paper_id

    def limitations(self) -> tuple[Claim, ...]:
        return tuple(c for c in self.claims if c.is_limitation())

    def open_questions(self) -> tuple[Claim, ...]:
        return tuple(
            c for c in self.claims if c.is_open_question()
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "metadata": self.metadata.to_dict(),
            "claims": [c.to_dict() for c in self.claims],
            "methods": list(self.methods),
            "metrics": list(self.metrics),
            "datasets": list(self.datasets),
            "assumptions": list(self.assumptions),
            "extends": list(self.extends),
            "conflicts": list(self.conflicts),
        }


def _claims(paper_id: str, specs: tuple[tuple[str, str, str], ...]) -> tuple[Claim, ...]:
    return tuple(
        Claim(cid, paper_id, klass, text)
        for cid, klass, text in specs
    )


_BASE_ID = "arXiv:2501.14176"


def _build_corpus() -> tuple[PaperRecord, ...]:
    p0 = PaperRecord(
        PaperMetadata(
            _BASE_ID,
            "In-Context Reinforcement Learning for Variable "
            "Action Spaces and Skill Stitching",
            "Studies in-context RL for variable action spaces "
            "and skill stitching; Section 4.6 lists open "
            "exploration problems.",
            ("Rentschler", "Roberts"), "2025-01",
            ("RL", "Agents"), "arXiv", False),
        _claims(_BASE_ID, (
            ("C0a", K.EXPERIMENTAL.value,
             "In-context RL can handle variable action spaces "
             "and stitch skills."),
            ("C0b", K.LIMITATION.value,
             "Exploration can collapse; sparse reward and "
             "repetitive trajectories remain open (Section 4.6)."),
            ("C0c", K.OPEN_QUESTION.value,
             "How can exploration be governed without replacing "
             "the policy?"),
        )),
        ("in_context_rl", "skill_stitching"),
        ("distinct_state_coverage",),
        ("synthetic_action_space",),
        ("exploration_matters", "sparse_reward_is_hard"))

    h1 = PaperRecord(
        PaperMetadata(
            "synthetic:H1",
            "Read-Only Exploration Governance for In-Context "
            "Agents (synthetic illustrative)",
            "Synthetic study of a read-only governance layer "
            "over in-context exploration.",
            ("Synthetic Group 1",), "2025-02",
            ("RL", "Agents"), "arXiv", True),
        _claims("synthetic:H1", (
            ("C1a", K.EXPERIMENTAL.value,
             "A read-only governance layer reduces redundant "
             "search on a synthetic corpus."),
            ("C1b", K.COMPARATIVE.value,
             "A generator/governor split increases distinct-"
             "state coverage versus a single explorer."),
            ("C1c", K.LIMITATION.value,
             "Results are limited to synthetic fixtures."),
            ("C1d", K.OPEN_QUESTION.value,
             "Does the effect hold under a trained policy?"),
            ("C1e", K.REPRODUCIBILITY.value,
             "All reported numbers are replay-exact."),
        )),
        ("read_only_governance", "generator_governor_split"),
        ("redundancy_reduction", "distinct_state_coverage"),
        ("synthetic_trajectories",),
        ("exploration_matters",),
        extends=(_BASE_ID,))

    h2 = PaperRecord(
        PaperMetadata(
            "synthetic:H2",
            "Generator/Governor Splits in Multi-Agent "
            "Exploration (synthetic illustrative)",
            "Synthetic study of generation/governance "
            "separation across multiple agents.",
            ("Synthetic Group 2",), "2025-03",
            ("Multi-Agent", "RL"), "arXiv", True),
        _claims("synthetic:H2", (
            ("C2a", K.EMPIRICAL.value,
             "Separating generation and governance preserves "
             "exploration diversity on synthetic runs."),
            ("C2b", K.THEORETICAL.value,
             "Soft re-weighting bounds accumulated authority "
             "drift."),
            ("C2c", K.LIMITATION.value,
             "Agents are rule-based stand-ins, not trained."),
            ("C2d", K.OPEN_QUESTION.value,
             "How does the split scale to many agents?"),
        )),
        ("generator_governor_split", "soft_reweighting"),
        ("exploration_diversity", "authority_drift"),
        ("synthetic_trajectories",),
        ("diversity_matters", "exploration_matters"),
        extends=("synthetic:H1",))

    h3 = PaperRecord(
        PaperMetadata(
            "synthetic:H3",
            "Residual Hallucination in Tool-Using LLM Agents "
            "(synthetic illustrative)",
            "Synthetic study of containment for high-certainty "
            "incoherent paths.",
            ("Synthetic Group 3",), "2025-03",
            ("LLM", "Safety", "Agents"), "arXiv", True),
        _claims("synthetic:H3", (
            ("C3a", K.EMPIRICAL.value,
             "Containment caps high-certainty incoherent paths "
             "on synthetic fixtures."),
            ("C3b", K.SPECULATIVE.value,
             "Containment may generalise beyond the fixtures."),
            ("C3c", K.LIMITATION.value,
             "Only a synthetic generator is evaluated."),
            ("C3d", K.OPEN_QUESTION.value,
             "How does containment behave with a real "
             "generator?"),
        )),
        ("containment",),
        ("residual_hallucination",),
        ("synthetic_trajectories",),
        ("hallucination_is_risk",))

    h4 = PaperRecord(
        PaperMetadata(
            "synthetic:H4",
            "Interpretability of Exploration Policies "
            "(synthetic illustrative)",
            "Synthetic study of structural classification of "
            "exploration trajectories.",
            ("Synthetic Group 4",), "2025-04",
            ("Interpretability", "RL"), "SSRN", True),
        _claims("synthetic:H4", (
            ("C4a", K.THEORETICAL.value,
             "Structural classification explains soft "
             "re-weighting decisions."),
            ("C4b", K.LIMITATION.value,
             "The account is post-hoc, not causal."),
            ("C4c", K.OPEN_QUESTION.value,
             "Can governance be interpreted causally?"),
        )),
        ("structural_classification",),
        ("redundancy_reduction",),
        ("synthetic_trajectories",),
        ("interpretability_matters",))

    h5 = PaperRecord(
        PaperMetadata(
            "synthetic:H5",
            "Alignment Constraints as Read-Only Governance "
            "(synthetic illustrative)",
            "Synthetic position on read-only constraints and "
            "optimisation authority.",
            ("Synthetic Group 5",), "2025-04",
            ("Alignment", "Safety"), "SSRN", True),
        _claims("synthetic:H5", (
            ("C5a", K.THEORETICAL.value,
             "Read-only constraints avoid hidden optimisation "
             "authority."),
            ("C5b", K.SPECULATIVE.value,
             "Non-authoritative layers may reduce misalignment "
             "pressure."),
            ("C5c", K.LIMITATION.value,
             "No real-world deployment is evaluated."),
            ("C5d", K.OPEN_QUESTION.value,
             "How do constraints behave under distribution "
             "shift?"),
        )),
        ("read_only_governance",),
        ("capture_resistance",),
        ("synthetic_trajectories",),
        ("alignment_matters", "exploration_matters"),
        extends=("synthetic:H1",),
        conflicts=("synthetic:H2",))

    h6 = PaperRecord(
        PaperMetadata(
            "synthetic:H6",
            "Reproducibility of Exploration Benchmarks "
            "(synthetic illustrative)",
            "Synthetic study of replay-exact exploration "
            "benchmarks.",
            ("Synthetic Group 6",), "2025-05",
            ("ML", "RL"), "arXiv", True),
        _claims("synthetic:H6", (
            ("C6a", K.REPRODUCIBILITY.value,
             "Exploration benchmarks are replay-exact under "
             "fixed fixtures."),
            ("C6b", K.COMPARATIVE.value,
             "Fragile and reproducible claims differ by fixture "
             "sensitivity."),
            ("C6c", K.LIMITATION.value,
             "Only a small benchmark suite is covered."),
            ("C6d", K.OPEN_QUESTION.value,
             "Does reproducibility hold across labs?"),
        )),
        ("deterministic_replay",),
        ("replay_stability",),
        ("synthetic_trajectories",),
        ("reproducibility_matters",))

    h7 = PaperRecord(
        PaperMetadata(
            "synthetic:H7",
            "Reasoning Chains and Open Exploration Questions "
            "(synthetic illustrative)",
            "Synthetic speculation on reasoning traces and "
            "exploration breadth.",
            ("Synthetic Group 7",), "2025-05",
            ("Reasoning", "LLM"), "arXiv", True),
        _claims("synthetic:H7", (
            ("C7a", K.SPECULATIVE.value,
             "Reasoning chains might guide exploration breadth."),
            ("C7b", K.OPEN_QUESTION.value,
             "Can reasoning traces be linked to exploration "
             "breadth?"),
            ("C7c", K.LIMITATION.value,
             "No empirical test is provided."),
        )),
        ("reasoning_trace",),
        ("novelty_gain",),
        ("synthetic_trajectories",),
        ("reasoning_matters",))

    return (p0, h1, h2, h3, h4, h5, h6, h7)


# --- deterministic synthetic expansion (50 papers) ----------
# Index-based generation, no PRNG. Every generated paper is an
# explicitly synthetic, illustrative fixture in the AI/ML topic
# areas - never a fabricated real citation. Each carries a
# primary claim, a supporting claim, a limitation and an open
# question, plus shared methods/metrics/assumptions (for
# clustering) and acyclic extends/conflicts (high index -> low).
_METHOD_POOL: tuple[str, ...] = (
    "read_only_governance", "generator_governor_split",
    "soft_reweighting", "containment",
    "structural_classification", "deterministic_replay",
    "reasoning_trace", "negotiation", "trajectory_clustering",
    "uncertainty_gating", "skill_composition",
    "exploration_scheduling",
)
_METRIC_POOL: tuple[str, ...] = (
    "redundancy_reduction", "novelty_gain",
    "exploration_diversity", "residual_hallucination",
    "authority_drift", "capture_resistance", "productivity_gain",
    "replay_stability", "coverage_ratio", "containment_rate",
    "drift_bound", "diversity_index",
)
_DATASET_POOL: tuple[str, ...] = (
    "synthetic_trajectories", "synthetic_action_space",
    "synthetic_state_graph", "synthetic_benchmark_suite",
)
_ASSUMPTION_POOL: tuple[str, ...] = (
    "exploration_matters", "diversity_matters",
    "hallucination_is_risk", "interpretability_matters",
    "alignment_matters", "reproducibility_matters",
    "reasoning_matters", "governance_helps",
)
_PRIMARY_ROTATION: tuple[str, ...] = (
    K.EXPERIMENTAL.value, K.THEORETICAL.value, K.EMPIRICAL.value,
)
_SUPPORT_ROTATION: tuple[str, ...] = (
    K.COMPARATIVE.value, K.REPRODUCIBILITY.value,
    K.SPECULATIVE.value, K.EMPIRICAL.value,
)
_PRIMARY_VERB: dict[str, str] = {
    K.EXPERIMENTAL.value: "reports an experimental result on",
    K.THEORETICAL.value: "develops a theoretical account of",
    K.EMPIRICAL.value: "presents an empirical observation about",
}
_SUPPORT_FLAVOUR: dict[str, str] = {
    K.COMPARATIVE.value: "comparative",
    K.REPRODUCIBILITY.value: "reproducibility",
    K.SPECULATIVE.value: "speculative",
    K.EMPIRICAL.value: "secondary empirical",
}
_GENERATED_START = 8
_GENERATED_COUNT = 50


def _generated_corpus() -> tuple[PaperRecord, ...]:
    out: list[PaperRecord] = []
    for k in range(
        _GENERATED_START, _GENERATED_START + _GENERATED_COUNT,
    ):
        topic_a = TOPIC_AREAS[k % len(TOPIC_AREAS)]
        topic_b = TOPIC_AREAS[(k + 3) % len(TOPIC_AREAS)]
        method_a = _METHOD_POOL[k % len(_METHOD_POOL)]
        method_b = _METHOD_POOL[(k + 5) % len(_METHOD_POOL)]
        metric_a = _METRIC_POOL[k % len(_METRIC_POOL)]
        metric_b = _METRIC_POOL[(k + 4) % len(_METRIC_POOL)]
        dataset = _DATASET_POOL[k % len(_DATASET_POOL)]
        assum_a = _ASSUMPTION_POOL[k % len(_ASSUMPTION_POOL)]
        assum_b = _ASSUMPTION_POOL[(k + 2) % len(_ASSUMPTION_POOL)]
        pclass = _PRIMARY_ROTATION[k % len(_PRIMARY_ROTATION)]
        sclass = _SUPPORT_ROTATION[k % len(_SUPPORT_ROTATION)]
        source = SOURCES[k % len(SOURCES)]
        month = (k % 12) + 1
        pid = f"synthetic:H{k}"
        methods = (
            (method_a,) if method_a == method_b
            else (method_a, method_b)
        )
        metrics = (
            (metric_a,) if metric_a == metric_b
            else (metric_a, metric_b)
        )
        assumptions = (
            (assum_a,) if assum_a == assum_b
            else (assum_a, assum_b)
        )
        extends = (
            ("arXiv:2501.14176",) if k == _GENERATED_START
            else (f"synthetic:H{k - 1}",)
        )
        conflicts = (
            (f"synthetic:H{k - 2}",) if k % 5 == 0 else ()
        )
        claims = (
            Claim(
                f"G{k}a", pid, pclass,
                f"Synthetic study H{k} {_PRIMARY_VERB[pclass]} "
                f"{topic_a} exploration using {method_a} on a "
                "synthetic corpus."),
            Claim(
                f"G{k}b", pid, sclass,
                f"A {_SUPPORT_FLAVOUR[sclass]} observation links "
                f"{method_b} to {metric_a} on the synthetic "
                "corpus."),
            Claim(
                f"G{k}c", pid, K.LIMITATION.value,
                "Results are limited to a synthetic fixture "
                "corpus and are not evaluated on real systems."),
            Claim(
                f"G{k}d", pid, K.OPEN_QUESTION.value,
                f"Whether the {topic_a} effect holds beyond the "
                "synthetic corpus remains an open question."),
        )
        out.append(PaperRecord(
            PaperMetadata(
                pid,
                f"Synthetic Study H{k}: {topic_a} / {topic_b} "
                "Exploration (synthetic illustrative)",
                f"Synthetic illustrative study H{k} on {topic_a} "
                f"exploration using {method_a} over a synthetic "
                "corpus.",
                (f"Synthetic Group {k}",),
                f"2025-{month:02d}",
                (topic_a, topic_b), source, True),
            claims, methods, metrics, (dataset,), assumptions,
            extends=extends, conflicts=conflicts,
        ))
    return tuple(out)


_CORPUS: tuple[PaperRecord, ...] = (
    _build_corpus() + _generated_corpus()
)


def papers() -> tuple[PaperRecord, ...]:
    return _CORPUS


def paper_ids() -> tuple[str, ...]:
    return tuple(p.paper_id for p in _CORPUS)


def by_id(paper_id: str) -> PaperRecord:
    for p in _CORPUS:
        if p.paper_id == paper_id:
            return p
    raise KeyError(paper_id)


def all_claims() -> tuple[Claim, ...]:
    out: list[Claim] = []
    for p in _CORPUS:
        out.extend(p.claims)
    return tuple(sorted(out, key=lambda c: c.sort_key()))


def claims_of(paper_id: str) -> tuple[Claim, ...]:
    return by_id(paper_id).claims


def claims_by_class(claim_class: str) -> tuple[Claim, ...]:
    return tuple(
        c for c in all_claims() if c.claim_class == claim_class
    )


def all_methods() -> tuple[str, ...]:
    out: set[str] = set()
    for p in _CORPUS:
        out.update(p.methods)
    return tuple(sorted(out))


def all_metrics() -> tuple[str, ...]:
    out: set[str] = set()
    for p in _CORPUS:
        out.update(p.metrics)
    return tuple(sorted(out))


def all_datasets() -> tuple[str, ...]:
    out: set[str] = set()
    for p in _CORPUS:
        out.update(p.datasets)
    return tuple(sorted(out))


def all_authors() -> tuple[str, ...]:
    out: set[str] = set()
    for p in _CORPUS:
        out.update(p.metadata.authors)
    return tuple(sorted(out))


def all_assumptions() -> tuple[str, ...]:
    out: set[str] = set()
    for p in _CORPUS:
        out.update(p.assumptions)
    return tuple(sorted(out))


__all__ = [
    "PaperRecord",
    "all_assumptions",
    "all_authors",
    "all_claims",
    "all_datasets",
    "all_methods",
    "all_metrics",
    "by_id",
    "claims_by_class",
    "claims_of",
    "paper_ids",
    "papers",
]
