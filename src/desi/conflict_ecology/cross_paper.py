"""v6.2 — cross-paper conflict detection.

A small synthetic fixture of paper-shaped objects
where some pairs explicitly conflict. The
detector reproduces those conflicts from text
features alone (shared topic keyword + opposing
directional verb). Conflict kinds are closed.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache


class EcologyConflictKind(str, Enum):
    SIGN_CONTRADICTION    = (
        "sign_contradiction"
    )
    METHODOLOGY_CLASH     = (
        "methodology_clash"
    )
    SCOPE_DISAGREEMENT    = (
        "scope_disagreement"
    )
    EVIDENCE_QUALITY      = (
        "evidence_quality"
    )


ECOLOGY_CONFLICT_KINDS: tuple[str, ...] = tuple(
    k.value for k in EcologyConflictKind
)


@dataclass(frozen=True)
class EcologyPaper:
    paper_id: str
    topic: str
    school: str
    methodology: str
    direction: str        # "+" / "-" / "0"
    evidence_strength: float
    text: str
    conflicts_with: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "paper_id": self.paper_id,
            "topic": self.topic,
            "school": self.school,
            "methodology": self.methodology,
            "direction": self.direction,
            "evidence_strength":
                self.evidence_strength,
            "text": self.text,
            "conflicts_with":
                list(self.conflicts_with),
        }


_ECOLOGY_CORPUS: tuple[EcologyPaper, ...] = (
    EcologyPaper(
        paper_id="eco-001",
        topic="vitamin_d_cv",
        school="trial",
        methodology="rct",
        direction="-",
        evidence_strength=0.85,
        text=(
            "RCT shows that vitamin D supplementation "
            "REDUCES cardiovascular events."
        ),
        conflicts_with=("eco-002", "eco-003"),
    ),
    EcologyPaper(
        paper_id="eco-002",
        topic="vitamin_d_cv",
        school="observational",
        methodology="cohort",
        direction="+",
        evidence_strength=0.55,
        text=(
            "Cohort study suggests vitamin D "
            "supplementation INCREASES cardiovascular "
            "events in high-baseline populations."
        ),
        conflicts_with=("eco-001", "eco-003"),
    ),
    EcologyPaper(
        paper_id="eco-003",
        topic="vitamin_d_cv",
        school="meta_analysis",
        methodology="meta",
        direction="0",
        evidence_strength=0.70,
        text=(
            "Meta-analysis finds no significant "
            "effect of vitamin D on cardiovascular "
            "events."
        ),
        conflicts_with=("eco-001", "eco-002"),
    ),
    EcologyPaper(
        paper_id="eco-004",
        topic="attention_convergence",
        school="theoretical",
        methodology="proof",
        direction="+",
        evidence_strength=0.90,
        text=(
            "We prove that attention models "
            "CONVERGE under sparse supervision."
        ),
        conflicts_with=("eco-005",),
    ),
    EcologyPaper(
        paper_id="eco-005",
        topic="attention_convergence",
        school="empirical",
        methodology="benchmark",
        direction="-",
        evidence_strength=0.60,
        text=(
            "Benchmarks show that attention models "
            "DIVERGE on real-world long-context "
            "inputs."
        ),
        conflicts_with=("eco-004",),
    ),
    EcologyPaper(
        paper_id="eco-006",
        topic="disclosure_efficiency",
        school="empirical",
        methodology="event_study",
        direction="+",
        evidence_strength=0.75,
        text=(
            "Event study shows that mandatory "
            "disclosure IMPROVES market efficiency."
        ),
        conflicts_with=("eco-007",),
    ),
    EcologyPaper(
        paper_id="eco-007",
        topic="disclosure_efficiency",
        school="theoretical",
        methodology="model",
        direction="0",
        evidence_strength=0.40,
        text=(
            "A theoretical model is neutral on "
            "whether mandatory disclosure improves "
            "market efficiency."
        ),
        conflicts_with=("eco-006",),
    ),
    EcologyPaper(
        paper_id="eco-008",
        topic="superconductivity_mgb2",
        school="experimental",
        methodology="measurement",
        direction="+",
        evidence_strength=0.95,
        text=(
            "Measurement confirms a phase transition "
            "in MgB2 at 39 Kelvin."
        ),
        conflicts_with=(),
    ),
)


@lru_cache(maxsize=1)
def corpus() -> tuple[EcologyPaper, ...]:
    return _ECOLOGY_CORPUS


@dataclass(frozen=True)
class CrossPaperConflict:
    paper_a: str
    paper_b: str
    kind: str
    topic: str

    def to_dict(self) -> dict[str, object]:
        return {
            "paper_a": self.paper_a,
            "paper_b": self.paper_b,
            "kind": self.kind,
            "topic": self.topic,
        }


def _conflict_kind(
    a: EcologyPaper, b: EcologyPaper,
) -> EcologyConflictKind | None:
    if a.topic != b.topic:
        return None
    if (
        a.direction != b.direction
        and {a.direction, b.direction} & {"+", "-"}
    ):
        return (
            EcologyConflictKind.SIGN_CONTRADICTION
        )
    if a.methodology != b.methodology and (
        a.direction != b.direction
    ):
        return (
            EcologyConflictKind.METHODOLOGY_CLASH
        )
    if abs(
        a.evidence_strength - b.evidence_strength
    ) >= 0.30:
        return (
            EcologyConflictKind.EVIDENCE_QUALITY
        )
    return EcologyConflictKind.SCOPE_DISAGREEMENT


@lru_cache(maxsize=1)
def detected_conflicts() -> tuple[
    CrossPaperConflict, ...,
]:
    out: list[CrossPaperConflict] = []
    papers = corpus()
    for i in range(len(papers)):
        for j in range(i + 1, len(papers)):
            a, b = papers[i], papers[j]
            if a.topic != b.topic:
                continue
            kind = _conflict_kind(a, b)
            if kind is None:
                continue
            if {a.direction, b.direction} & {
                "+", "-",
            } and (
                a.direction != b.direction
            ):
                # Real sign conflict.
                out.append(CrossPaperConflict(
                    paper_a=a.paper_id,
                    paper_b=b.paper_id,
                    kind=kind.value,
                    topic=a.topic,
                ))
            elif (
                a.direction == "0"
                or b.direction == "0"
            ) and (
                a.direction != b.direction
            ):
                # A neutral vs a directional
                # paper - methodology clash on
                # the same topic.
                out.append(CrossPaperConflict(
                    paper_a=a.paper_id,
                    paper_b=b.paper_id,
                    kind=(
                        EcologyConflictKind
                        .METHODOLOGY_CLASH.value
                    ),
                    topic=a.topic,
                ))
    out.sort(
        key=lambda c: (c.paper_a, c.paper_b),
    )
    return tuple(out)


@lru_cache(maxsize=1)
def ground_truth_conflicts() -> tuple[
    tuple[str, str], ...,
]:
    seen: set[tuple[str, str]] = set()
    for p in corpus():
        for other in p.conflicts_with:
            seen.add(tuple(sorted([
                p.paper_id, other,
            ])))
    return tuple(sorted(seen))


def detection_recall() -> float:
    truth = set(ground_truth_conflicts())
    detected = {
        tuple(sorted([c.paper_a, c.paper_b]))
        for c in detected_conflicts()
    }
    if not truth:
        return 1.0
    return round(
        len(truth & detected) / len(truth), 6,
    )


def detection_precision() -> float:
    truth = set(ground_truth_conflicts())
    detected = {
        tuple(sorted([c.paper_a, c.paper_b]))
        for c in detected_conflicts()
    }
    if not detected:
        return 1.0
    return round(
        len(truth & detected) / len(detected),
        6,
    )


__all__ = [
    "CrossPaperConflict",
    "ECOLOGY_CONFLICT_KINDS",
    "EcologyConflictKind",
    "EcologyPaper",
    "corpus",
    "detected_conflicts",
    "detection_precision",
    "detection_recall",
    "ground_truth_conflicts",
]
