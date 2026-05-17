"""v3.54 — cross-corpus pair resonance report.

Pflichtmetriken (directive § v3.54):

* ``resonance_pairs_per_corpus``    — per-corpus
  plateau resonant_pair_count
* ``control_pairs_per_corpus``      — per-corpus
  control resonant_pair_count
* ``subadditivity_per_corpus``      — per-corpus
  plateau subadditivity_score
* ``pair_transfer_rate``            — fraction of
  ELIGIBLE (>= 2 anchors) corpora whose plateau
  resonant_pair_count exceeds the control count
* ``replay_stability``              — deterministic
  two-run equality

Paper-11 v2 gate #2: ``pair_transfer_rate >= 0.75``.
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from .matrix import all_corpora_pair_matrices
from .pair_transfer import (
    CorpusPairSummary, MIN_ANCHORS_FOR_PAIRS,
    PROBE_RADIUS, eligible_corpora,
    ineligible_corpora,
    per_corpus_control_summary,
    per_corpus_plateau_summary, triple_max_extra,
)


PAPER11_TRANSFER_FLOOR: float = 0.75


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V354Report:
    probe_radius: float
    eligible_corpora: tuple[str, ...]
    ineligible_corpora: tuple[str, ...]
    plateau_summaries: tuple[dict, ...]
    control_summaries: tuple[dict, ...]
    resonance_pairs_per_corpus: dict[str, int]
    control_pairs_per_corpus: dict[str, int]
    subadditivity_per_corpus: dict[str, float]
    triple_max_extra_per_corpus: dict[str, int]
    pair_transfer_rate: float
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
            "plateau_summaries":
                list(self.plateau_summaries),
            "control_summaries":
                list(self.control_summaries),
            "resonance_pairs_per_corpus":
                dict(self.resonance_pairs_per_corpus),
            "control_pairs_per_corpus":
                dict(self.control_pairs_per_corpus),
            "subadditivity_per_corpus":
                dict(self.subadditivity_per_corpus),
            "triple_max_extra_per_corpus":
                dict(self.triple_max_extra_per_corpus),
            "pair_transfer_rate":
                self.pair_transfer_rate,
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


def _gather_summaries() -> tuple[
    tuple[CorpusPairSummary, ...],
    tuple[CorpusPairSummary, ...],
]:
    plat = tuple(
        per_corpus_plateau_summary(c)
        for c in eligible_corpora()
    )
    ctrl = tuple(
        per_corpus_control_summary(c)
        for c in eligible_corpora()
    )
    return plat, ctrl


def _replay_stability() -> float:
    a = [
        s.to_dict() for s in _gather_summaries()[0]
    ] + [
        s.to_dict() for s in _gather_summaries()[1]
    ]
    b = [
        s.to_dict() for s in _gather_summaries()[0]
    ] + [
        s.to_dict() for s in _gather_summaries()[1]
    ]
    if not a:
        return 1.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return _round(matches / len(a))


def build_report() -> V354Report:
    plat, ctrl = _gather_summaries()
    eligible = eligible_corpora()
    ineligible = ineligible_corpora()
    plat_by = {s.corpus: s for s in plat}
    ctrl_by = {s.corpus: s for s in ctrl}
    res_pairs = {
        c: plat_by[c].resonant_pair_count
        for c in eligible
    }
    ctrl_pairs = {
        c: ctrl_by[c].resonant_pair_count
        for c in eligible
    }
    subadds = {
        c: plat_by[c].subadditivity_score
        for c in eligible
    }
    triples = {
        c: triple_max_extra(c) for c in eligible
    }
    if eligible:
        transfers = sum(
            1 for c in eligible
            if plat_by[c].resonant_pair_count
                > ctrl_by[c].resonant_pair_count
        )
        rate = _round(transfers / len(eligible))
    else:
        rate = 0.0
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif rate >= PAPER11_TRANSFER_FLOOR:
        verdict = "PAIR_RESONANCE_TRANSFERS"
    elif rate > 0:
        verdict = "PAIR_RESONANCE_PARTIAL"
    else:
        verdict = "PAIR_RESONANCE_LOCAL"

    rationale = (
        f"INFO: probe_radius {PROBE_RADIUS}",
        f"INFO: eligible_corpora {list(eligible)} "
        f"(need >= {MIN_ANCHORS_FOR_PAIRS} plateau "
        f"anchors)",
        f"INFO: ineligible_corpora {list(ineligible)} "
        f"(too few anchors for pair analysis)",
        f"INFO: resonance_pairs_per_corpus "
        f"{sorted(res_pairs.items())}",
        f"INFO: control_pairs_per_corpus "
        f"{sorted(ctrl_pairs.items())}",
        f"INFO: subadditivity_per_corpus "
        f"{sorted(subadds.items())}",
        f"INFO: triple_max_extra_per_corpus "
        f"{sorted(triples.items())}",
        f"{'PASS' if rate >= PAPER11_TRANSFER_FLOOR else 'FAIL'}: "
        f"pair_transfer_rate {rate} >= "
        f"{PAPER11_TRANSFER_FLOOR}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V354Report(
        probe_radius=PROBE_RADIUS,
        eligible_corpora=eligible,
        ineligible_corpora=ineligible,
        plateau_summaries=tuple(
            s.to_dict() for s in plat
        ),
        control_summaries=tuple(
            s.to_dict() for s in ctrl
        ),
        resonance_pairs_per_corpus=res_pairs,
        control_pairs_per_corpus=ctrl_pairs,
        subadditivity_per_corpus=subadds,
        triple_max_extra_per_corpus=triples,
        pair_transfer_rate=rate,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_cross_corpus_resonance_artifact(
) -> dict[str, object]:
    plat, ctrl = _gather_summaries()
    matrices = all_corpora_pair_matrices()
    return {
        "schema_version":
            "v3_54_cross_corpus_resonance",
        "probe_radius": PROBE_RADIUS,
        "eligible_corpora":
            list(eligible_corpora()),
        "ineligible_corpora":
            list(ineligible_corpora()),
        "plateau_summaries": [
            s.to_dict() for s in plat
        ],
        "control_summaries": [
            s.to_dict() for s in ctrl
        ],
        "pair_matrices": matrices,
    }


__all__ = [
    "PAPER11_TRANSFER_FLOOR", "V354Report",
    "build_cross_corpus_resonance_artifact",
    "build_report",
]
