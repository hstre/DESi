"""v37.3 - Adversarial Financial Semantics report.

Pflichtmetriken (directive § v37.3):

* semantic_conflict_visibility
* management_spin_detection
* footnote_conflict_detection
* warning_zone_preservation
* replay_stability

Killerfrage: "Kann DESi formell korrekte, aber epistemisch
fragwuerdige Finanznarrative erkennen?"

Surfaces semantic conflicts in formally-correct-but-suspicious
narratives: creative accounting, management spin, 'too smooth'
narratives, footnote conflicts and semantic distraction. Warning
zones are preserved (never smoothed) and the clean control case
raises no conflict (no hallucination).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from desi.reasoning_benchmarks import (
    core_identity, core_replay_stable, governance_identity,
)
from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .creative_accounting_cases import (
    adversarial_scenarios, provenance,
)
from .semantic_conflict_engine import detect_conflicts, warning_zones

VERDICT_PASSED = "ADVERSARIAL_SEMANTICS_RUN_PASSED"
VERDICT_PARTIAL = "ADVERSARIAL_SEMANTICS_RUN_PARTIAL"
VERDICT_HALT = "ADVERSARIAL_SEMANTICS_RUN_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_PASSED, VERDICT_PARTIAL, VERDICT_HALT,
)

_FLOOR = 0.85


def _detected(s: dict) -> set[str]:
    return set(detect_conflicts(s.get("signals", {})))


def _expected(s: dict) -> set[str]:
    return set(s.get("expected_conflicts", []))


def semantic_conflict_visibility() -> float:
    """Recall of expected conflicts across all scenarios."""
    total = 0
    found = 0
    for s in adversarial_scenarios():
        exp = _expected(s)
        total += len(exp)
        found += len(exp & _detected(s))
    return round(found / total, 6) if total else 0.0


def _typed_detection(conflict_type: str) -> float:
    relevant = [
        s for s in adversarial_scenarios()
        if conflict_type in _expected(s)
    ]
    if not relevant:
        return 1.0
    ok = sum(1 for s in relevant if conflict_type in _detected(s))
    return round(ok / len(relevant), 6)


def management_spin_detection() -> float:
    return _typed_detection("management_spin")


def footnote_conflict_detection() -> float:
    return _typed_detection("footnote_conflict")


def no_false_conflicts() -> bool:
    """The clean control scenarios raise no conflict (no
    hallucination)."""
    for s in adversarial_scenarios():
        if not _expected(s) and _detected(s):
            return False
    return True


def warning_zone_preservation() -> float:
    zones = warning_zones()
    if not zones:
        return 0.0
    ok = sum(1 for z in zones if z.preserved and not z.smoothed)
    return round(ok / len(zones), 6)


def replay_stability() -> float:
    a = [(s["scenario_id"], tuple(sorted(_detected(s))))
         for s in adversarial_scenarios()]
    b = [(s["scenario_id"], tuple(sorted(_detected(s))))
         for s in adversarial_scenarios()]
    if a != b:
        return 0.0
    return 1.0 if core_replay_stable() else 0.0


def adversarial_metrics() -> dict[str, float]:
    return {
        "semantic_conflict_visibility": semantic_conflict_visibility(),
        "management_spin_detection": management_spin_detection(),
        "footnote_conflict_detection": footnote_conflict_detection(),
        "warning_zone_preservation": warning_zone_preservation(),
        "replay_stability": replay_stability(),
    }


def _signature() -> str:
    m = adversarial_metrics()
    parts = [f"{k}={m[k]}" for k in sorted(m)]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def _recommendation() -> str:
    m = adversarial_metrics()
    if m["replay_stability"] < 1.0 or governance_identity() < 1.0:
        return VERDICT_HALT
    if not no_false_conflicts():
        return VERDICT_HALT
    if all(v >= _FLOOR for v in m.values()):
        return VERDICT_PASSED
    return VERDICT_PARTIAL


@dataclass(frozen=True)
class V373Report:
    scenario_count: int
    warning_zone_count: int
    semantic_conflict_visibility: float
    management_spin_detection: float
    footnote_conflict_detection: float
    warning_zone_preservation: float
    replay_stability: float
    no_false_conflicts: bool
    governance_identity: float
    core_identity: float
    human_approval_required: bool
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "scenario_count": self.scenario_count,
            "warning_zone_count": self.warning_zone_count,
            "semantic_conflict_visibility":
                self.semantic_conflict_visibility,
            "management_spin_detection": self.management_spin_detection,
            "footnote_conflict_detection":
                self.footnote_conflict_detection,
            "warning_zone_preservation": self.warning_zone_preservation,
            "replay_stability": self.replay_stability,
            "no_false_conflicts": self.no_false_conflicts,
            "governance_identity": self.governance_identity,
            "core_identity": self.core_identity,
            "human_approval_required": self.human_approval_required,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True, separators=(",", ":"),
        )


def build_report() -> V373Report:
    m = adversarial_metrics()
    replay = m["replay_stability"]
    halt = replay < 1.0 or not no_false_conflicts()
    rationale = (
        f"INFO: scanned {len(adversarial_scenarios())} adversarial "
        f"scenarios (provenance {provenance()}); "
        f"{len(warning_zones())} preserved warning zones; clean "
        f"control raises no conflict: {no_false_conflicts()}",
        f"{'PASS' if m['semantic_conflict_visibility'] >= _FLOOR else 'FAIL'}"
        f": semantic_conflict_visibility "
        f"{m['semantic_conflict_visibility']} >= 0.85",
        f"{'PASS' if m['management_spin_detection'] >= _FLOOR else 'FAIL'}"
        f": management_spin_detection {m['management_spin_detection']}"
        f" >= 0.85",
        f"{'PASS' if m['footnote_conflict_detection'] >= _FLOOR else 'FAIL'}"
        f": footnote_conflict_detection "
        f"{m['footnote_conflict_detection']} >= 0.85",
        f"{'PASS' if m['warning_zone_preservation'] >= _FLOOR else 'FAIL'}"
        f": warning_zone_preservation "
        f"{m['warning_zone_preservation']} >= 0.85 (never smoothed)",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: replay_stability "
        f"{replay} == 1.0; governance_identity "
        f"{governance_identity()}; core_identity {core_identity()}; "
        f"HUMAN_APPROVAL_REQUIRED={HUMAN_APPROVAL_REQUIRED}",
    )
    return V373Report(
        scenario_count=len(adversarial_scenarios()),
        warning_zone_count=len(warning_zones()),
        semantic_conflict_visibility=m["semantic_conflict_visibility"],
        management_spin_detection=m["management_spin_detection"],
        footnote_conflict_detection=m["footnote_conflict_detection"],
        warning_zone_preservation=m["warning_zone_preservation"],
        replay_stability=replay,
        no_false_conflicts=no_false_conflicts(),
        governance_identity=governance_identity(),
        core_identity=core_identity(),
        human_approval_required=HUMAN_APPROVAL_REQUIRED,
        halt=halt,
        recommendation=_recommendation(),
        rationale=rationale,
    )


def build_adversarial_artifact() -> dict[str, object]:
    m = adversarial_metrics()
    return {
        "schema_version": "v37_3_adversarial_semantics_run",
        "disclaimer": (
            "Adversarial financial-semantics run over "
            "locally-vendored synthetic scenarios that are formally "
            "correct but semantically suspicious. DESi surfaces "
            "creative accounting, management spin, 'too smooth' "
            "narratives, footnote conflicts and semantic "
            "distraction as preserved warning zones (never smoothed "
            "over), and a clean control case raises no conflict so "
            "DESi does not hallucinate. Warning zones are epistemic "
            "markers, not accusations; NOT official exam content; NO "
            "official results claimed; does not replace auditors. "
            "Human approval is mandatory."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "warning_zones": [z.to_dict() for z in warning_zones()],
        "no_false_conflicts": no_false_conflicts(),
        "semantic_conflict_visibility": m["semantic_conflict_visibility"],
        "management_spin_detection": m["management_spin_detection"],
        "footnote_conflict_detection": m["footnote_conflict_detection"],
        "warning_zone_preservation": m["warning_zone_preservation"],
        "replay_stability": m["replay_stability"],
        "governance_identity": governance_identity(),
        "core_identity": core_identity(),
        "human_approval_required": HUMAN_APPROVAL_REQUIRED,
        "signature": _signature(),
        "recommendation": _recommendation(),
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_PARTIAL",
    "VERDICT_PASSED",
    "V373Report",
    "adversarial_metrics",
    "build_adversarial_artifact",
    "build_report",
    "footnote_conflict_detection",
    "management_spin_detection",
    "no_false_conflicts",
    "replay_stability",
    "semantic_conflict_visibility",
    "warning_zone_preservation",
]
