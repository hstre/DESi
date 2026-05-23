"""v23.1 - fixture provenance.

For every reported number, names the upstream fixture and the
derivation, so a reader can follow value -> fixture -> sprint
rather than taking the number on faith.
"""
from __future__ import annotations

from dataclasses import dataclass

from .conditions import results


@dataclass(frozen=True)
class FixtureNote:
    result_id: str
    fixture: str
    derivation: str

    def to_dict(self) -> dict[str, object]:
        return {
            "result_id": self.result_id,
            "fixture": self.fixture,
            "derivation": self.derivation,
        }


_NOTES: tuple[FixtureNote, ...] = (
    FixtureNote(
        "R1", "icrl_governed baseline/governed weight vectors",
        "1 - governed_redundant_weight / baseline_redundant_"
        "weight over the fixed synthetic trajectory set."),
    FixtureNote(
        "R2", "comparative_exploration state sets",
        "distinct states reached only via the Wild Explorer, "
        "divided by the dual-agent distinct-state total."),
    FixtureNote(
        "R3", "dual_agent hallucinated-path fixture",
        "hallucination_pressure * (1 - containment); the "
        "governor caps high-certainty incoherent paths."),
    FixtureNote(
        "R4", "dual_agent_negotiation region partition",
        "distinct regions surviving negotiation divided by "
        "distinct regions before negotiation."),
    FixtureNote(
        "R5", "dual_agent_ecology 5600-step hash chain",
        "bounded saturating drift CAP*t/(t+HALF) sampled at "
        "the final governed step."),
    FixtureNote(
        "R6", "dual_agent_ecology capture series",
        "1 - mean(governance_capture) across the long-horizon "
        "run; capture stayed at zero."),
    FixtureNote(
        "R7", "comparative_exploration coverage counts",
        "dual-agent distinct-state coverage divided by DESi-"
        "alone coverage, reported as a ratio."),
    FixtureNote(
        "R8", "cross-phase replay signatures",
        "each metric recomputed and compared bit-for-bit; the "
        "hash chain matched, so stability is 1.0."),
)


def fixture_notes() -> tuple[FixtureNote, ...]:
    return _NOTES


def documented_result_ids() -> frozenset[str]:
    return frozenset(n.result_id for n in _NOTES)


def synthetic_share() -> float:
    """Fraction of reported results explicitly flagged as
    synthetic, in [0, 1]."""
    rows = results()
    if not rows:
        return 1.0
    synthetic = sum(1 for r in rows if r.is_synthetic)
    return round(synthetic / len(rows), 6)


def undocumented_results() -> tuple[str, ...]:
    documented = documented_result_ids()
    return tuple(
        sorted(
            r.result_id for r in results()
            if r.result_id not in documented
        )
    )


__all__ = [
    "FixtureNote",
    "documented_result_ids",
    "fixture_notes",
    "synthetic_share",
    "undocumented_results",
]
