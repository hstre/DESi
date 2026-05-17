"""v3.46 — GAP_DETECTED census report.

Pflichtmetriken (directive):

* ``gap_detected_count``     — total trajectories
  visiting GAP_DETECTED (transient + terminal)
* ``terminal_gap_count``     — final state at 1.0
* ``transient_gap_count``    — visits 1.0 but ends
  elsewhere
* ``gap_outside_non_rescued`` — GAP cases not in the
  v3.30 controller's non-rescued set
* ``gap_replay_stability``   — deterministic replay

Stop rule: ``terminal_gap_count < 2`` → hypothesis
weak, document and continue (per directive).
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from .extractor import (
    collect_gap_cases, gap_cases_outside_non_rescued,
    source_corpus_distribution, terminal_gap_cases,
    transient_gap_cases,
)
from .state import PAPER10_TERMINAL_GAP_COUNT


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V346Report:
    gap_detected_count: int
    terminal_gap_count: int
    transient_gap_count: int
    gap_outside_non_rescued: int
    source_corpus_distribution: dict[str, int]
    paper10_terminal_count: int
    matches_paper10: bool
    gap_replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "gap_detected_count":
                self.gap_detected_count,
            "terminal_gap_count":
                self.terminal_gap_count,
            "transient_gap_count":
                self.transient_gap_count,
            "gap_outside_non_rescued":
                self.gap_outside_non_rescued,
            "source_corpus_distribution":
                dict(self.source_corpus_distribution),
            "paper10_terminal_count":
                self.paper10_terminal_count,
            "matches_paper10":
                self.matches_paper10,
            "gap_replay_stability":
                self.gap_replay_stability,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _replay_stability() -> float:
    a = [c.to_dict() for c in collect_gap_cases()]
    b = [c.to_dict() for c in collect_gap_cases()]
    if not a:
        return 1.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return _round(matches / len(a))


def build_report() -> V346Report:
    cases = collect_gap_cases()
    terminal = terminal_gap_cases()
    transient = transient_gap_cases()
    outside = gap_cases_outside_non_rescued()
    sources = source_corpus_distribution()
    replay = _replay_stability()

    matches = (
        len(terminal) == PAPER10_TERMINAL_GAP_COUNT
    )
    halt = len(terminal) < PAPER10_TERMINAL_GAP_COUNT
    if halt:
        verdict = "HALT_TERMINAL_GAP_BELOW_PAPER10"
    elif matches and len(outside) == 0:
        verdict = "GAP_CENSUS_MATCHES_PAPER10"
    elif len(outside) > 0:
        verdict = "GAP_CENSUS_EXCEEDS_NON_RESCUED"
    else:
        verdict = "GAP_CENSUS_EXCEEDS_PAPER10"

    rationale = (
        f"INFO: gap_detected_count {len(cases)}",
        f"{'PASS' if matches else 'WARN'}: "
        f"terminal_gap_count {len(terminal)} "
        f"(Paper-10 reported {PAPER10_TERMINAL_GAP_COUNT})",
        f"INFO: transient_gap_count {len(transient)}",
        f"INFO: gap_outside_non_rescued {len(outside)}",
        f"INFO: source_corpus_distribution "
        f"{sorted(sources.items())}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"gap_replay_stability {replay}",
    )

    return V346Report(
        gap_detected_count=len(cases),
        terminal_gap_count=len(terminal),
        transient_gap_count=len(transient),
        gap_outside_non_rescued=len(outside),
        source_corpus_distribution=sources,
        paper10_terminal_count=PAPER10_TERMINAL_GAP_COUNT,
        matches_paper10=matches,
        gap_replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_gap_inventory_artifact() -> dict[str, object]:
    cases = collect_gap_cases()
    return {
        "schema_version": "v3_46_gap_inventory",
        "cases": [c.to_dict() for c in cases],
        "case_count": len(cases),
    }


__all__ = [
    "V346Report", "build_gap_inventory_artifact",
    "build_report",
]
