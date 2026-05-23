"""v23.1 - explicit metric definitions.

Every metric named in the document carries a definition, a
range, and the sprint it is reported from - so no number
appears without being defined.
"""
from __future__ import annotations

from dataclasses import dataclass

from .conditions import results


@dataclass(frozen=True)
class MetricDefinition:
    name: str
    definition: str
    range_lo: float
    range_hi: float
    source: str

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "definition": self.definition,
            "range": [self.range_lo, self.range_hi],
            "source": self.source,
        }


_DEFINITIONS: tuple[MetricDefinition, ...] = (
    MetricDefinition(
        "redundancy_reduction",
        "Fraction of redundant search weight the governor "
        "re-weights away (1 - governed/baseline).", 0.0, 1.0,
        "v19.1"),
    MetricDefinition(
        "novelty_gain",
        "Share of distinct states reached only with the Wild "
        "Explorer, beyond the DESi-alone baseline.", 0.0, 1.0,
        "v20.0/v21.0"),
    MetricDefinition(
        "exploration_diversity",
        "Fraction of distinct explored regions preserved after "
        "negotiation (no homogenisation).", 0.0, 1.0, "v20.2"),
    MetricDefinition(
        "residual_hallucination",
        "Hallucination pressure that leaks past containment "
        "(pressure * (1 - containment)).", 0.0, 1.0, "v20.1"),
    MetricDefinition(
        "authority_drift",
        "Governed accumulation of optimisation authority over "
        "the long horizon (bounded, saturating).", 0.0, 1.0,
        "v20.3"),
    MetricDefinition(
        "capture_resistance",
        "One minus the mean governance capture across the "
        "run.", 0.0, 1.0, "v20.3"),
    MetricDefinition(
        "productivity_gain",
        "Extra distinct-state coverage of the dual-agent "
        "design relative to DESi-alone, as a ratio.", 0.0,
        100.0, "v21.0"),
    MetricDefinition(
        "replay_stability",
        "1.0 iff every metric is bit-identical on a second "
        "computation and the hash chain matches.", 0.0, 1.0,
        "v19-v22"),
)


def definitions() -> tuple[MetricDefinition, ...]:
    return _DEFINITIONS


def defined_names() -> frozenset[str]:
    return frozenset(d.name for d in _DEFINITIONS)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def metric_visibility() -> float:
    """Fraction of the metrics cited in results that have an
    explicit definition, in [0, 1]."""
    used = {r.metric_name for r in results()}
    if not used:
        return 1.0
    defined = defined_names()
    covered = sum(1 for m in used if m in defined)
    return _round(covered / len(used))


def undefined_metrics() -> tuple[str, ...]:
    used = {r.metric_name for r in results()}
    defined = defined_names()
    return tuple(sorted(m for m in used if m not in defined))


__all__ = [
    "MetricDefinition",
    "defined_names",
    "definitions",
    "metric_visibility",
    "undefined_metrics",
]
