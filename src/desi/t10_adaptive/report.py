"""v3.107 — adaptive candidate search report.

Pflichtmetriken (directive § v3.107):

* ``candidate_vocab_size``
* ``reused_candidates``
* ``new_candidate_count``
* ``mean_candidate_auc``
* ``replay_stability``

Killerfrage: "Braucht T10 eine Familie von
Erweiterungen?"
"""
from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass

from .adaptive import (
    ADAPTIVE_CANDIDATES, ALL_CANDIDATES,
)
from .search import (
    AdaptiveOutcome,
    all_adaptive_outcomes,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def candidate_vocab_size() -> int:
    """Number of distinct candidates that were
    selected as ``best_candidate`` (after
    deduplication, excluding the empty
    sentinel)."""
    used = {
        o.best_candidate
        for o in all_adaptive_outcomes()
        if o.best_candidate
    }
    return len(used)


def used_candidates() -> tuple[str, ...]:
    used = {
        o.best_candidate
        for o in all_adaptive_outcomes()
        if o.best_candidate
    }
    return tuple(sorted(used))


def reused_candidates() -> tuple[str, ...]:
    """Candidates that rescue MORE than one
    instance."""
    cnt: Counter = Counter()
    for o in all_adaptive_outcomes():
        if o.best_candidate:
            cnt[o.best_candidate] += 1
    return tuple(sorted(
        c for c, n in cnt.items() if n > 1
    ))


def new_candidate_count() -> int:
    """Adaptive candidates (outside v3.101's
    six) actually used as best_candidate."""
    used = set(used_candidates())
    return sum(
        1 for c in ADAPTIVE_CANDIDATES
        if c in used
    )


def mean_candidate_auc() -> float:
    outs = all_adaptive_outcomes()
    if not outs:
        return 0.0
    aucs = [o.best_auc for o in outs]
    return _round(sum(aucs) / len(aucs))


def rescue_rate() -> float:
    outs = all_adaptive_outcomes()
    if not outs:
        return 0.0
    rescued = sum(1 for o in outs if o.rescued)
    return _round(rescued / len(outs))


@dataclass(frozen=True)
class V3107Report:
    instance_count: int
    all_candidates: tuple[str, ...]
    candidate_vocab_size: int
    used_candidates: tuple[str, ...]
    reused_candidates: tuple[str, ...]
    new_candidate_count: int
    mean_candidate_auc: float
    rescue_rate: float
    adaptive_outcomes: tuple[dict, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "instance_count":
                self.instance_count,
            "all_candidates":
                list(self.all_candidates),
            "candidate_vocab_size":
                self.candidate_vocab_size,
            "used_candidates":
                list(self.used_candidates),
            "reused_candidates":
                list(self.reused_candidates),
            "new_candidate_count":
                self.new_candidate_count,
            "mean_candidate_auc":
                self.mean_candidate_auc,
            "rescue_rate": self.rescue_rate,
            "adaptive_outcomes":
                list(self.adaptive_outcomes),
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
    a = (
        candidate_vocab_size(),
        used_candidates(),
        reused_candidates(),
        mean_candidate_auc(),
        rescue_rate(),
    )
    b = (
        candidate_vocab_size(),
        used_candidates(),
        reused_candidates(),
        mean_candidate_auc(),
        rescue_rate(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V3107Report:
    outs = all_adaptive_outcomes()
    vsize = candidate_vocab_size()
    used = used_candidates()
    reused = reused_candidates()
    ncnt = new_candidate_count()
    mca = mean_candidate_auc()
    rr = rescue_rate()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif vsize == 1:
        verdict = "SINGLE_KEY_SUFFICES"
    elif rr < 0.50:
        verdict = "VOCAB_NEEDED_BUT_INCOMPLETE"
    else:
        verdict = "VOCAB_RESCUES_BROADLY"

    rationale = (
        f"INFO: instance_count {len(outs)}",
        f"INFO: candidate_vocab_size {vsize}",
        f"INFO: used_candidates {list(used)}",
        f"INFO: reused_candidates "
        f"{list(reused)}",
        f"INFO: new_candidate_count {ncnt}",
        f"INFO: mean_candidate_auc {mca}",
        f"INFO: rescue_rate {rr}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V3107Report(
        instance_count=len(outs),
        all_candidates=ALL_CANDIDATES,
        candidate_vocab_size=vsize,
        used_candidates=used,
        reused_candidates=reused,
        new_candidate_count=ncnt,
        mean_candidate_auc=mca,
        rescue_rate=rr,
        adaptive_outcomes=tuple(
            o.to_dict() for o in outs
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_t10_adaptive_candidates_artifact(
) -> dict[str, object]:
    outs = all_adaptive_outcomes()
    return {
        "schema_version":
            "v3_107_t10_adaptive_candidates",
        "instance_count": len(outs),
        "all_candidates": list(ALL_CANDIDATES),
        "candidate_vocab_size":
            candidate_vocab_size(),
        "used_candidates":
            list(used_candidates()),
        "reused_candidates":
            list(reused_candidates()),
        "new_candidate_count":
            new_candidate_count(),
        "mean_candidate_auc":
            mean_candidate_auc(),
        "rescue_rate": rescue_rate(),
        "adaptive_outcomes": [
            o.to_dict() for o in outs
        ],
    }


__all__ = [
    "V3107Report",
    "build_report",
    "build_t10_adaptive_candidates_artifact",
    "candidate_vocab_size",
    "mean_candidate_auc",
    "new_candidate_count",
    "rescue_rate",
    "reused_candidates",
    "used_candidates",
]
