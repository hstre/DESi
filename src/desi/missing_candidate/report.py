"""v3.75 — candidate reconstruction report.

Pflichtmetriken (directive § v3.75):

* ``candidate_match_score``
* ``expected_region_overlap``
* ``role_reconstruction_accuracy``
* ``replay_stability``

Neptun concept gate #3:
``candidate_match_score >= 0.70``.
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from .candidate import CandidateMatch
from .reconstruct import all_candidate_matches


NEPTUN_MATCH_FLOOR: float = 0.70


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V375Report:
    candidate_count: int
    matches: tuple[dict, ...]
    candidate_match_score: float
    expected_region_overlap: float
    role_reconstruction_accuracy: float
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "candidate_count":
                self.candidate_count,
            "matches": list(self.matches),
            "candidate_match_score":
                self.candidate_match_score,
            "expected_region_overlap":
                self.expected_region_overlap,
            "role_reconstruction_accuracy":
                self.role_reconstruction_accuracy,
            "replay_stability":
                self.replay_stability,
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
    a = [m.to_dict() for m in all_candidate_matches()]
    b = [m.to_dict() for m in all_candidate_matches()]
    if not a:
        return 1.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return _round(matches / len(a))


def build_report() -> V375Report:
    matches = all_candidate_matches()
    if matches:
        avg_match = _round(
            sum(m.match_score for m in matches)
            / len(matches),
        )
        avg_overlap = _round(
            sum(
                m.expected_region_overlap
                for m in matches
            ) / len(matches),
        )
        role_acc = _round(
            sum(
                1 for m in matches if m.bridge_match
            ) / len(matches),
        )
    else:
        avg_match = 0.0
        avg_overlap = 0.0
        role_acc = 0.0
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif avg_match >= NEPTUN_MATCH_FLOOR:
        verdict = "CANDIDATE_RECONSTRUCTION_USABLE"
    elif avg_match > 0:
        verdict = "CANDIDATE_RECONSTRUCTION_WEAK"
    else:
        verdict = "CANDIDATE_RECONSTRUCTION_FAILED"

    rationale = (
        f"INFO: candidate_count {len(matches)}",
        f"INFO: matches "
        f"{[m.to_dict() for m in matches]}",
        f"{'PASS' if avg_match >= NEPTUN_MATCH_FLOOR else 'FAIL'}: "
        f"candidate_match_score {avg_match} >= "
        f"{NEPTUN_MATCH_FLOOR}",
        f"INFO: expected_region_overlap "
        f"{avg_overlap}",
        f"INFO: role_reconstruction_accuracy "
        f"{role_acc}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V375Report(
        candidate_count=len(matches),
        matches=tuple(
            m.to_dict() for m in matches
        ),
        candidate_match_score=avg_match,
        expected_region_overlap=avg_overlap,
        role_reconstruction_accuracy=role_acc,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_missing_candidate_reconstruction_artifact(
) -> dict[str, object]:
    matches = all_candidate_matches()
    return {
        "schema_version":
            "v3_75_missing_candidate_reconstruction",
        "matches":
            [m.to_dict() for m in matches],
    }


__all__ = [
    "NEPTUN_MATCH_FLOOR", "V375Report",
    "build_missing_candidate_reconstruction_artifact",
    "build_report",
]
