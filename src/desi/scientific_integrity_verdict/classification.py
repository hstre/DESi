"""v13.4 — Scientific Integrity Concept Gate.

Six conditions per directive:

1. fake_paper_recall      >= 0.90
2. false_accusation_rate  <= 0.05
3. citation_grounding     >= 0.90
4. epistemic_integrity    >= 0.90
5. sludge_propagation     <= 0.10
6. replay_stability       == 1.0
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from ..adversarial_research.report import (
    build_report as v132_build,
)
from ..paper_integrity.report import (
    build_report as v130_build,
)
from ..scientific_ecology.report import (
    build_report as v133_build,
)
from ..sludge_detection.report import (
    build_report as v131_build,
)
from .taxonomy import ScientificIntegrityClass


_FAKE_PAPER_RECALL_FLOOR:    float = 0.90
_FALSE_ACCUSATION_CEIL:      float = 0.05
_CITATION_GROUNDING_FLOOR:   float = 0.90
_EPISTEMIC_INTEGRITY_FLOOR:  float = 0.90
_SLUDGE_PROPAGATION_CEIL:    float = 0.10
_REPLAY_FLOOR:               float = 1.0


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class AggregatedScientificMetrics:
    fake_paper_recall: float
    false_accusation_rate: float
    citation_grounding: float
    epistemic_integrity: float
    sludge_propagation: float
    sludge_resistance: float
    scientific_integrity_score: float
    replay_stability: float

    def to_dict(self) -> dict[str, object]:
        return {
            "fake_paper_recall":
                self.fake_paper_recall,
            "false_accusation_rate":
                self.false_accusation_rate,
            "citation_grounding":
                self.citation_grounding,
            "epistemic_integrity":
                self.epistemic_integrity,
            "sludge_propagation":
                self.sludge_propagation,
            "sludge_resistance":
                self.sludge_resistance,
            "scientific_integrity_score":
                (
                    self
                    .scientific_integrity_score
                ),
            "replay_stability":
                self.replay_stability,
        }


@lru_cache(maxsize=1)
def aggregate() -> (
    AggregatedScientificMetrics
):
    v130 = v130_build()
    v131 = v131_build()
    v132 = v132_build()
    v133 = v133_build()

    fpr = v131.fake_paper_recall
    far = v131.false_accusation_rate
    cg = v131.citation_grounding
    sp = v133.sludge_propagation

    # epistemic_integrity: composite of v13.0
    # structural soundness + v13.2 manipulation
    # detection.
    ei = (
        v130.causal_overreach_detection
        + v132.manipulation_detection
        + v132.overclaim_detection
    ) / 3.0

    # sludge_resistance: 1 - sludge_propagation
    # clipped at 0.
    sr = max(0.0, 1.0 - sp)

    # scientific_integrity_score: composite of
    # the four positive signals.
    sis = (
        fpr
        + (1.0 - far)
        + cg
        + ei
    ) / 4.0

    replay = (
        1.0 if (
            v130.replay_stability == 1.0
            and v131.replay_stability == 1.0
            and v132.replay_stability == 1.0
            and v133.replay_stability == 1.0
        ) else 0.0
    )

    return AggregatedScientificMetrics(
        fake_paper_recall=_round(fpr),
        false_accusation_rate=_round(far),
        citation_grounding=_round(cg),
        epistemic_integrity=_round(ei),
        sludge_propagation=_round(sp),
        sludge_resistance=_round(sr),
        scientific_integrity_score=_round(sis),
        replay_stability=replay,
    )


def _gate_results() -> tuple[
    tuple[str, bool], ...,
]:
    m = aggregate()
    return (
        (
            "fake_paper_recall",
            m.fake_paper_recall
            >= _FAKE_PAPER_RECALL_FLOOR,
        ),
        (
            "false_accusation_rate",
            m.false_accusation_rate
            <= _FALSE_ACCUSATION_CEIL,
        ),
        (
            "citation_grounding",
            m.citation_grounding
            >= _CITATION_GROUNDING_FLOOR,
        ),
        (
            "epistemic_integrity",
            m.epistemic_integrity
            >= _EPISTEMIC_INTEGRITY_FLOOR,
        ),
        (
            "sludge_propagation",
            m.sludge_propagation
            <= _SLUDGE_PROPAGATION_CEIL,
        ),
        (
            "replay_stability",
            m.replay_stability
            >= _REPLAY_FLOOR,
        ),
    )


def gate_passes_all() -> bool:
    return all(
        ok for _, ok in _gate_results()
    )


def gate_failing_conditions() -> tuple[
    str, ...,
]:
    return tuple(
        name for name, ok in _gate_results()
        if not ok
    )


def classify() -> ScientificIntegrityClass:
    """Priority: replay collapse outranks
    sludge tolerance, sludge tolerance outranks
    false accusation, false accusation outranks
    epistemic thinness, epistemic thinness
    outranks partial reliability."""
    m = aggregate()
    if m.replay_stability < _REPLAY_FLOOR:
        return (
            ScientificIntegrityClass
            .SLUDGE_COMPATIBLE_SYSTEM
        )
    if (
        m.fake_paper_recall
        < _FAKE_PAPER_RECALL_FLOOR
        or m.sludge_propagation
        > _SLUDGE_PROPAGATION_CEIL
    ):
        return (
            ScientificIntegrityClass
            .SLUDGE_COMPATIBLE_SYSTEM
        )
    if (
        m.false_accusation_rate
        > _FALSE_ACCUSATION_CEIL
    ):
        return (
            ScientificIntegrityClass
            .EPISTEMICALLY_THIN
        )
    if (
        m.epistemic_integrity
        < _EPISTEMIC_INTEGRITY_FLOOR
    ):
        return (
            ScientificIntegrityClass
            .PARTIALLY_RELIABLE
        )
    if (
        m.citation_grounding
        < _CITATION_GROUNDING_FLOOR
    ):
        return (
            ScientificIntegrityClass
            .STRUCTURALLY_TRUSTWORTHY
        )
    return (
        ScientificIntegrityClass
        .EPISTEMICALLY_RIGOROUS
    )


__all__ = [
    "AggregatedScientificMetrics",
    "aggregate",
    "classify",
    "gate_failing_conditions",
    "gate_passes_all",
]
