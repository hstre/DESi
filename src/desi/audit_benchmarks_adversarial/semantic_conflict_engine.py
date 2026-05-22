"""v37.3 - semantic conflict engine.

Aggregates the adversarial detectors into a set of semantic conflicts
per scenario and emits a preserved warning zone for each. DESi marks
formally-correct-but-suspicious narratives without fabricating a
conflict where none is signalled (the clean control stays empty).
"""
from __future__ import annotations

from dataclasses import dataclass

from .creative_accounting_cases import (
    adversarial_scenarios, creative_accounting_flag,
)
from .footnote_conflict_detection import footnote_conflict_flag
from .management_spin_detection import (
    management_spin_flag, too_smooth_flag,
)

CONFLICT_TYPES: tuple[str, ...] = (
    "creative_accounting",
    "management_spin",
    "too_smooth_narrative",
    "footnote_conflict",
    "semantic_distraction",
)


@dataclass(frozen=True)
class WarningZone:
    scenario_id: str
    conflict_type: str
    preserved: bool
    smoothed: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "conflict_type": self.conflict_type,
            "preserved": self.preserved,
            "smoothed": self.smoothed,
        }


def detect_conflicts(signals: dict) -> tuple[str, ...]:
    out: list[str] = []
    if creative_accounting_flag(signals):
        out.append("creative_accounting")
    if management_spin_flag(signals):
        out.append("management_spin")
    if too_smooth_flag(signals):
        out.append("too_smooth_narrative")
    if footnote_conflict_flag(signals):
        out.append("footnote_conflict")
    if bool(signals.get("semantic_distraction")):
        out.append("semantic_distraction")
    return tuple(out)


def warning_zones() -> tuple[WarningZone, ...]:
    out: list[WarningZone] = []
    for s in adversarial_scenarios():
        for ct in detect_conflicts(s.get("signals", {})):
            out.append(WarningZone(
                scenario_id=s["scenario_id"],
                conflict_type=ct,
                preserved=True,
                smoothed=False,
            ))
    return tuple(out)


__all__ = [
    "CONFLICT_TYPES",
    "WarningZone",
    "detect_conflicts",
    "warning_zones",
]
