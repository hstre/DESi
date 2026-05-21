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


_CORPUS: tuple[PaperRecord, ...] = _build_corpus()


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
