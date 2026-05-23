"""v22.0 - Scientific Hypothesis Exploration report.

Pflichtmetriken (directive § v22.0):

* paper_candidate_quality
* speculative_drift
* technical_grounding
* overreach_detection
* replay_stability

Killerfrage: "Kann DESi produktive wissenschaftliche
Hypothesen von Hype unterscheiden?"

DESi separates technically grounded, paper-grade follow-up
hypotheses from speculative drift and forbidden hype. The
Wild Explorer may speculate; DESi must not adopt it.
"""
from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass

from .bridge_generation import (
    bridged_candidate_ids, paper_candidate_quality,
)
from .novelty import (
    forbidden_in_candidates, overreach_detection,
    speculative_drift,
)
from .trajectory_ideas import (
    anchored_fraction, fantasy_ideas, technical_grounding,
)
from .wild_hypotheses import (
    hypotheses, overreach_hypotheses, paper_candidates,
)

VERDICT_SEPARATED = "HYPOTHESES_TRIAGED"
VERDICT_DRIFTED = "HYPOTHESES_HYPE_DRIFTED"
VERDICT_HALT = "REPLAY_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_SEPARATED, VERDICT_DRIFTED, VERDICT_HALT,
)

_QUALITY_FLOOR = 0.90
_GROUNDING_FLOOR = 0.90
_OVERREACH_FLOOR = 0.90


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _signature() -> str:
    parts = [
        f"{h.hyp_id}:{h.technical_grounding}:"
        f"{h.speculative_drift}:{int(h.is_paper_candidate())}"
        for h in hypotheses()
    ]
    return hashlib.sha256(
        "|".join(parts).encode("utf-8"),
    ).hexdigest()


def _metric_tuple() -> tuple[object, ...]:
    return (
        paper_candidate_quality(), speculative_drift(),
        technical_grounding(), overreach_detection(),
    )


def _replay_stability() -> float:
    if _signature() != _signature():
        return 0.0
    return 1.0 if _metric_tuple() == _metric_tuple() else 0.0


def _recommendation(
    *, replay: float, quality: float, grounding: float,
    overreach: float, forbidden_leak: bool,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if (
        forbidden_leak
        or quality < _QUALITY_FLOOR
        or grounding < _GROUNDING_FLOOR
        or overreach < _OVERREACH_FLOOR
    ):
        return VERDICT_DRIFTED
    return VERDICT_SEPARATED


@dataclass(frozen=True)
class V220Report:
    hypothesis_count: int
    paper_candidate_count: int
    overreach_count: int
    paper_candidate_quality: float
    speculative_drift: float
    technical_grounding: float
    overreach_detection: float
    anchored_fraction: float
    paper_candidate_ids: tuple[str, ...]
    overreach_ids: tuple[str, ...]
    fantasy_ids: tuple[str, ...]
    forbidden_in_candidates: bool
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "hypothesis_count": self.hypothesis_count,
            "paper_candidate_count": self.paper_candidate_count,
            "overreach_count": self.overreach_count,
            "paper_candidate_quality":
                self.paper_candidate_quality,
            "speculative_drift": self.speculative_drift,
            "technical_grounding": self.technical_grounding,
            "overreach_detection": self.overreach_detection,
            "anchored_fraction": self.anchored_fraction,
            "paper_candidate_ids":
                list(self.paper_candidate_ids),
            "overreach_ids": list(self.overreach_ids),
            "fantasy_ids": list(self.fantasy_ids),
            "forbidden_in_candidates":
                self.forbidden_in_candidates,
            "replay_stability": self.replay_stability,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V220Report:
    pcq = paper_candidate_quality()
    sd = speculative_drift()
    tg = technical_grounding()
    od = overreach_detection()
    fic = forbidden_in_candidates()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, quality=pcq, grounding=tg, overreach=od,
        forbidden_leak=fic,
    )
    rationale = (
        f"INFO: hypotheses {len(hypotheses())}; "
        f"paper_candidates {len(paper_candidates())}; "
        f"overreach {len(overreach_hypotheses())}",
        "INFO: the Wild Explorer may speculate; DESi accepts "
        "only grounded, low-drift, forbidden-term-free "
        "hypotheses as paper-grade",
        f"{'PASS' if pcq >= 0.90 else 'FAIL'}: "
        f"paper_candidate_quality {pcq} >= 0.90",
        f"INFO: speculative_drift {sd} (in the wild output)",
        f"{'PASS' if tg >= 0.90 else 'FAIL'}: "
        f"technical_grounding {tg} >= 0.90 "
        f"(anchored_fraction {anchored_fraction()})",
        f"{'PASS' if od >= 0.90 else 'FAIL'}: "
        f"overreach_detection {od} >= 0.90",
        f"{'PASS' if not fic else 'FAIL'}: "
        f"forbidden_in_candidates {fic} (must be False)",
        f"INFO: fantasy_ideas {list(fantasy_ideas())}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay} (signature "
        f"{_signature()[:12]})",
    )
    return V220Report(
        hypothesis_count=len(hypotheses()),
        paper_candidate_count=len(paper_candidates()),
        overreach_count=len(overreach_hypotheses()),
        paper_candidate_quality=pcq,
        speculative_drift=sd,
        technical_grounding=tg,
        overreach_detection=od,
        anchored_fraction=anchored_fraction(),
        paper_candidate_ids=tuple(
            h.hyp_id for h in paper_candidates()
        ),
        overreach_ids=tuple(
            h.hyp_id for h in overreach_hypotheses()
        ),
        fantasy_ids=fantasy_ideas(),
        forbidden_in_candidates=fic,
        replay_stability=replay,
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_hypotheses_artifact() -> dict[str, object]:
    return {
        "schema_version":
            "v22_0_scientific_hypothesis_exploration",
        "disclaimer": (
            "The Wild Scientific Explorer proposes follow-up "
            "hypotheses over the v19-v21 results; DESi accepts "
            "only technically grounded, low-drift, forbidden-"
            "term-free ones as paper-grade. No breakthrough / "
            "AGI / world-model language is ever adopted. DESi "
            "makes no global intelligence claim, replaces no "
            "RL, and claims no truth authority. Replay-exact."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "hypotheses": [h.to_dict() for h in hypotheses()],
        "paper_candidate_ids": [
            h.hyp_id for h in paper_candidates()
        ],
        "bridged_candidate_ids": list(bridged_candidate_ids()),
        "overreach_ids": [
            h.hyp_id for h in overreach_hypotheses()
        ],
        "fantasy_ids": list(fantasy_ideas()),
        "paper_candidate_quality": paper_candidate_quality(),
        "speculative_drift": speculative_drift(),
        "technical_grounding": technical_grounding(),
        "overreach_detection": overreach_detection(),
        "anchored_fraction": anchored_fraction(),
        "forbidden_in_candidates": forbidden_in_candidates(),
        "signature": _signature(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_DRIFTED",
    "VERDICT_HALT",
    "VERDICT_SEPARATED",
    "V220Report",
    "build_hypotheses_artifact",
    "build_report",
]
