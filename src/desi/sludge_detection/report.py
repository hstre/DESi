"""v13.1 — sludge-detection report.

Five Pflichtmetriken:

* ``fake_paper_recall``
* ``false_accusation_rate``
* ``citation_grounding``
* ``diagram_consistency``
* ``replay_stability``

Killerfrage: "Kann DESi epistemischen Muell
erkennen ohne legitime Forschung zu
zerstoeren?"
"""
from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass

from .citation_validation import (
    composite_grounding,
)
from .diagram_consistency import (
    diagram_consistency, stats_consistency,
)
from .hallucinated_references import (
    citation_grounding,
    hallucinated_reference_count,
)
from .sludge import (
    SLUDGE_VERDICTS, classified_papers,
    fake_paper_recall, false_accusation_rate,
)


@dataclass(frozen=True)
class V131Report:
    paper_count: int
    fake_paper_recall: float
    false_accusation_rate: float
    citation_grounding: float
    diagram_consistency: float
    stats_consistency: float
    composite_grounding: float
    hallucinated_reference_count: int
    verdict_distribution: dict[str, int]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "paper_count": self.paper_count,
            "fake_paper_recall":
                self.fake_paper_recall,
            "false_accusation_rate":
                self.false_accusation_rate,
            "citation_grounding":
                self.citation_grounding,
            "diagram_consistency":
                self.diagram_consistency,
            "stats_consistency":
                self.stats_consistency,
            "composite_grounding":
                self.composite_grounding,
            "hallucinated_reference_count":
                self.hallucinated_reference_count,
            "verdict_distribution": dict(
                self.verdict_distribution,
            ),
            "replay_stability":
                self.replay_stability,
            "halt": self.halt,
            "recommendation":
                self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _replay_stability() -> float:
    a = (
        fake_paper_recall(),
        false_accusation_rate(),
        citation_grounding(),
        diagram_consistency(),
        stats_consistency(),
    )
    b = (
        fake_paper_recall(),
        false_accusation_rate(),
        citation_grounding(),
        diagram_consistency(),
        stats_consistency(),
    )
    return 1.0 if a == b else 0.0


def _recommendation(
    *, replay: float, fpr: float,
    far: float, cg: float, dc: float,
) -> str:
    if replay < 1.0:
        return "HALT_REPLAY_DRIFT"
    if far > 0.05:
        return "SLUDGE_FALSE_ACCUSATION"
    if fpr < 0.90:
        return "SLUDGE_DETECTION_WEAK"
    if cg < 0.90:
        return "SLUDGE_CITATION_LEAK"
    if dc < 0.90:
        return "SLUDGE_DIAGRAM_LEAK"
    return "SLUDGE_CONTAINED"


def build_report() -> V131Report:
    fpr = fake_paper_recall()
    far = false_accusation_rate()
    cg = citation_grounding()
    dc = diagram_consistency()
    sc = stats_consistency()
    cgr = composite_grounding()
    hrc = hallucinated_reference_count()
    vd = dict(Counter(
        r.verdict for r in classified_papers()
    ))
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, fpr=fpr, far=far,
        cg=cg, dc=dc,
    )
    rationale = (
        f"INFO: paper_count "
        f"{len(classified_papers())}",
        f"INFO: verdict_distribution {vd}",
        f"INFO: hallucinated_reference_count "
        f"{hrc}",
        f"INFO: composite_grounding {cgr}",
        f"{'PASS' if fpr >= 0.90 else 'FAIL'}: "
        f"fake_paper_recall {fpr} >= 0.90",
        f"{'PASS' if far <= 0.05 else 'FAIL'}: "
        f"false_accusation_rate {far} <= 0.05",
        f"{'PASS' if cg >= 0.90 else 'FAIL'}: "
        f"citation_grounding {cg} >= 0.90",
        f"{'PASS' if dc >= 0.90 else 'FAIL'}: "
        f"diagram_consistency {dc} >= 0.90",
        f"INFO: stats_consistency {sc}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )
    return V131Report(
        paper_count=len(classified_papers()),
        fake_paper_recall=fpr,
        false_accusation_rate=far,
        citation_grounding=cg,
        diagram_consistency=dc,
        stats_consistency=sc,
        composite_grounding=cgr,
        hallucinated_reference_count=hrc,
        verdict_distribution=vd,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_sludge_detection_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v13_1_sludge_detection",
        "sludge_verdicts":
            list(SLUDGE_VERDICTS),
        "paper_count":
            len(classified_papers()),
        "classified_papers": [
            p.to_dict()
            for p in classified_papers()
        ],
        "fake_paper_recall":
            fake_paper_recall(),
        "false_accusation_rate":
            false_accusation_rate(),
        "citation_grounding":
            citation_grounding(),
        "diagram_consistency":
            diagram_consistency(),
        "stats_consistency":
            stats_consistency(),
        "composite_grounding":
            composite_grounding(),
        "hallucinated_reference_count":
            hallucinated_reference_count(),
    }


__all__ = [
    "V131Report",
    "build_report",
    "build_sludge_detection_artifact",
]
