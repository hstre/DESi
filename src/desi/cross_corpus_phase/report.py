"""v3.56 — cross-corpus phase transition transfer
report.

Pflichtmetriken (directive § v3.56):

* ``discontinuity_per_corpus``
* ``saturation_per_corpus``
* ``coupling_strength_per_corpus``
* ``phase_transfer_rate``
* ``replay_stability``

Paper-11 v2 gate #4: ``phase_transfer_rate >= 0.75``.
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from ..cross_corpus.corpus_loader import (
    REFERENCE_CORPORA,
)
from .phase_transfer import (
    per_corpus_summary, transfer_rate,
)
from .transition import (
    MIN_ANCHORS_FOR_DISCONTINUITY, PROBE_RADIUS,
    coupling_strength, discontinuity_score,
    eligible_corpora, ineligible_corpora,
    per_corpus_phase_curve, saturation_point,
)


PAPER11_TRANSFER_FLOOR: float = 0.75


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V356Report:
    probe_radius: float
    eligible_corpora: tuple[str, ...]
    ineligible_corpora: tuple[str, ...]
    per_corpus_summaries: tuple[dict, ...]
    discontinuity_per_corpus: dict[str, float]
    saturation_per_corpus: dict[str, int | None]
    coupling_strength_per_corpus: dict[str, float]
    phase_transfer_rate: float
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "probe_radius": self.probe_radius,
            "eligible_corpora":
                list(self.eligible_corpora),
            "ineligible_corpora":
                list(self.ineligible_corpora),
            "per_corpus_summaries":
                list(self.per_corpus_summaries),
            "discontinuity_per_corpus":
                dict(self.discontinuity_per_corpus),
            "saturation_per_corpus":
                dict(self.saturation_per_corpus),
            "coupling_strength_per_corpus":
                dict(
                    self.coupling_strength_per_corpus,
                ),
            "phase_transfer_rate":
                self.phase_transfer_rate,
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
    a = [
        per_corpus_summary(c)
        for c in eligible_corpora()
    ]
    b = [
        per_corpus_summary(c)
        for c in eligible_corpora()
    ]
    if not a:
        return 1.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return _round(matches / len(a))


def build_report() -> V356Report:
    eligible = eligible_corpora()
    ineligible = ineligible_corpora()
    summaries = tuple(
        per_corpus_summary(c) for c in eligible
    )
    disc: dict[str, float] = {}
    sat: dict[str, int | None] = {}
    coup: dict[str, float] = {}
    for c in eligible:
        curve = per_corpus_phase_curve(c)
        disc[c] = discontinuity_score(curve)
        sat[c] = saturation_point(curve)
        coup[c] = coupling_strength(curve)
    rate = transfer_rate()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif rate >= PAPER11_TRANSFER_FLOOR:
        verdict = "PHASE_TRANSITION_TRANSFERS"
    elif rate > 0:
        verdict = "PHASE_TRANSITION_PARTIAL"
    else:
        verdict = "PHASE_TRANSITION_LOCAL"

    rationale = (
        f"INFO: probe_radius {PROBE_RADIUS}",
        f"INFO: eligible_corpora {list(eligible)} "
        f"(need >= {MIN_ANCHORS_FOR_DISCONTINUITY} "
        f"plateau anchors)",
        f"INFO: ineligible_corpora "
        f"{list(ineligible)}",
        f"INFO: discontinuity_per_corpus "
        f"{sorted(disc.items())}",
        f"INFO: saturation_per_corpus "
        f"{sorted(sat.items(), key=lambda kv: kv[0])}",
        f"INFO: coupling_strength_per_corpus "
        f"{sorted(coup.items())}",
        f"{'PASS' if rate >= PAPER11_TRANSFER_FLOOR else 'FAIL'}: "
        f"phase_transfer_rate {rate} >= "
        f"{PAPER11_TRANSFER_FLOOR}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V356Report(
        probe_radius=PROBE_RADIUS,
        eligible_corpora=eligible,
        ineligible_corpora=ineligible,
        per_corpus_summaries=summaries,
        discontinuity_per_corpus=disc,
        saturation_per_corpus=sat,
        coupling_strength_per_corpus=coup,
        phase_transfer_rate=rate,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_cross_corpus_phase_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v3_56_cross_corpus_phase",
        "probe_radius": PROBE_RADIUS,
        "eligible_corpora":
            list(eligible_corpora()),
        "ineligible_corpora":
            list(ineligible_corpora()),
        "per_corpus_summaries": [
            per_corpus_summary(c)
            for c in REFERENCE_CORPORA
        ],
    }


__all__ = [
    "PAPER11_TRANSFER_FLOOR", "V356Report",
    "build_cross_corpus_phase_artifact",
    "build_report",
]
