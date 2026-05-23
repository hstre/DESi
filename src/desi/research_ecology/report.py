"""v27.3 - Long-Horizon Research Ecology report.

Pflichtmetriken (directive § v27.3):

* plurality_preservation
* hype_visibility
* fragility_visibility
* open_question_preservation
* replay_stability

Killerfrage: "Kann DESi langfristige Forschungsevolution
modellieren ohne selbst Forschungsautoritaet zu werden?"

Over 5200 deterministic steps, method trends drift and hype
waves rise and fall, yet nothing is deleted: plurality, fragile
claims, open questions and conflicts are all preserved, and the
hash chain makes the run replay-exact.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .citation_waves import hype_amplitude, hype_visibility
from .ecology import run
from .research_memory import (
    conflict_preservation, forgotten_events, fragility_visibility,
    lineage_preserved, open_question_preservation,
    rediscovery_events,
)
from .trend_drift import plurality_preservation

VERDICT_PLURAL = "RESEARCH_EVOLUTION_PLURAL_STABLE"
VERDICT_COLLAPSED = "RESEARCH_PLURALITY_COLLAPSED"
VERDICT_HALT = "ECOLOGY_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_PLURAL, VERDICT_COLLAPSED, VERDICT_HALT,
)

_FLOOR = 0.90


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def replay_stability() -> float:
    return 1.0 if run().chain_head == run().chain_head else 0.0


def _recommendation(
    *, replay: float, plurality: float, hype: float,
    fragility: float, open_q: float,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if plurality < _FLOOR:
        return VERDICT_COLLAPSED
    if (
        hype < _FLOOR
        or fragility < _FLOOR
        or open_q < _FLOOR
    ):
        return VERDICT_HALT
    return VERDICT_PLURAL


@dataclass(frozen=True)
class V273Report:
    steps: int
    method_count: int
    plurality_preservation: float
    hype_visibility: float
    fragility_visibility: float
    open_question_preservation: float
    replay_stability: float
    conflict_preservation: float
    forgotten_events: int
    rediscovery_events: int
    lineage_preserved: bool
    hype_amplitude: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "steps": self.steps,
            "method_count": self.method_count,
            "plurality_preservation": self.plurality_preservation,
            "hype_visibility": self.hype_visibility,
            "fragility_visibility": self.fragility_visibility,
            "open_question_preservation":
                self.open_question_preservation,
            "replay_stability": self.replay_stability,
            "conflict_preservation": self.conflict_preservation,
            "forgotten_events": self.forgotten_events,
            "rediscovery_events": self.rediscovery_events,
            "lineage_preserved": self.lineage_preserved,
            "hype_amplitude": self.hype_amplitude,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V273Report:
    plurality = plurality_preservation()
    hype = hype_visibility()
    fragility = fragility_visibility()
    open_q = open_question_preservation()
    replay = replay_stability()
    halt = replay < 1.0
    r = run()
    verdict = _recommendation(
        replay=replay, plurality=plurality, hype=hype,
        fragility=fragility, open_q=open_q,
    )
    rationale = (
        f"INFO: {r.steps}-step deterministic research ecology "
        f"over {r.method_count} method lines and "
        f"{r.topic_count} topics; hash chain "
        f"{r.chain_head[:12]}",
        f"INFO: forgetting is soft - {r.forgotten_events} "
        f"dormancy events and {r.rediscovery_events} "
        f"rediscoveries, but no line is ever deleted "
        f"(lineage_preserved={lineage_preserved()})",
        f"{'PASS' if plurality >= _FLOOR else 'FAIL'}: "
        f"plurality_preservation {plurality} >= 0.90 (research "
        f"plurality does not collapse)",
        f"{'PASS' if hype >= _FLOOR else 'FAIL'}: "
        f"hype_visibility {hype} >= 0.90 (wave amplitude "
        f"{hype_amplitude()})",
        f"{'PASS' if fragility >= _FLOOR else 'FAIL'}: "
        f"fragility_visibility {fragility} >= 0.90",
        f"{'PASS' if open_q >= _FLOOR else 'FAIL'}: "
        f"open_question_preservation {open_q} >= 0.90",
        f"INFO: conflict_preservation {conflict_preservation()}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay} (chain {r.chain_head[:12]})",
    )
    return V273Report(
        steps=r.steps,
        method_count=r.method_count,
        plurality_preservation=plurality,
        hype_visibility=hype,
        fragility_visibility=fragility,
        open_question_preservation=open_q,
        replay_stability=replay,
        conflict_preservation=conflict_preservation(),
        forgotten_events=r.forgotten_events,
        rediscovery_events=r.rediscovery_events,
        lineage_preserved=lineage_preserved(),
        hype_amplitude=hype_amplitude(),
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_ecology_artifact() -> dict[str, object]:
    r = run()
    return {
        "schema_version": "v27_3_research_ecology",
        "disclaimer": (
            "A 5200-step deterministic research ecology over the "
            "corpus: method trends drift and hype waves rise and "
            "fall, computed by fixed arithmetic (no PRNG). "
            "Forgetting is soft - dormant lines stay present at "
            "low strength and are never deleted - so research "
            "plurality, fragile claims, open questions and "
            "conflicts are all preserved. DESi models research "
            "evolution without becoming a research authority. A "
            "hash chain makes the run replay-exact; a 200-step "
            "sample is recorded."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "plurality_preservation": plurality_preservation(),
        "hype_visibility": hype_visibility(),
        "fragility_visibility": fragility_visibility(),
        "open_question_preservation":
            open_question_preservation(),
        "conflict_preservation": conflict_preservation(),
        "replay_stability": replay_stability(),
        "forgotten_events": r.forgotten_events,
        "rediscovery_events": r.rediscovery_events,
        "lineage_preserved": lineage_preserved(),
        "hype_amplitude": hype_amplitude(),
        "run": r.to_dict(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_COLLAPSED",
    "VERDICT_HALT",
    "VERDICT_PLURAL",
    "V273Report",
    "build_ecology_artifact",
    "build_report",
    "replay_stability",
]
