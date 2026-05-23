"""FrameDisambiguatorProbeReport — Aufgaben 9 + 10."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .candidates import (
    CandidateScore,
    generate_candidates,
    score_all,
)
from .contamination import (
    ContaminationResult,
    excluded_polysemy_texts,
    probe,
)
from .extractor import (
    CounterCase,
    TargetCase,
    extract_polysemy_targets,
    extract_thermo_counter_set,
)
from .negative_control import NEGATIVE_CONTROLS, MixedCase


def _hits(text: str, tokens: tuple[str, ...]) -> bool:
    low = text.lower()
    return all(tok in low for tok in tokens)


@dataclass(frozen=True)
class NegativeControlOutcome:
    nc_id: str
    expected_frame: str
    absorbed: bool   # True iff the candidate's tokens all appear

    def to_dict(self) -> dict[str, Any]:
        return {
            "nc_id": self.nc_id,
            "expected_frame": self.expected_frame,
            "absorbed": self.absorbed,
        }


@dataclass(frozen=True)
class CandidateAssessment:
    score: CandidateScore
    contamination: ContaminationResult
    negative_control_outcomes: tuple[NegativeControlOutcome, ...]
    negative_control_precision: float
    safe: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score.to_dict(),
            "contamination": self.contamination.to_dict(),
            "negative_control_outcomes":
                [n.to_dict() for n in self.negative_control_outcomes],
            "negative_control_precision":
                self.negative_control_precision,
            "safe": self.safe,
            "reason": self.reason,
        }


def _run_negative_controls_for(
    tokens: tuple[str, ...],
) -> tuple[tuple[NegativeControlOutcome, ...], float]:
    outcomes: list[NegativeControlOutcome] = []
    safe_count = 0
    for nc in NEGATIVE_CONTROLS:
        absorbed = _hits(nc.text, tokens)
        outcomes.append(NegativeControlOutcome(
            nc_id=nc.nc_id,
            expected_frame=nc.expected_frame.value,
            absorbed=absorbed,
        ))
        # The candidate is safe wrt this NC iff it does NOT absorb
        # the text (because absorbing it would mis-promote to
        # information-theoretic).
        if not absorbed:
            safe_count += 1
    precision = round(safe_count / len(outcomes), 6) if outcomes else 0.0
    return tuple(outcomes), precision


@dataclass(frozen=True)
class FrameDisambiguatorProbeReport:
    started_at: datetime
    finished_at: datetime
    target_count: int
    counter_count: int
    candidate_count: int
    targets: tuple[TargetCase, ...]
    counters: tuple[CounterCase, ...]
    assessments: tuple[CandidateAssessment, ...]
    recommended_next: str
    recommended_tokens: tuple[str, ...]
    replay_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "target_count": self.target_count,
            "counter_count": self.counter_count,
            "candidate_count": self.candidate_count,
            "targets": [t.to_dict() for t in self.targets],
            "counters": [c.to_dict() for c in self.counters],
            "assessments": [a.to_dict() for a in self.assessments],
            "recommended_next": self.recommended_next,
            "recommended_tokens": list(self.recommended_tokens),
            "replay_hash": self.replay_hash,
        }


def _replay_hash(payload: dict[str, Any]) -> str:
    cleaned = {
        k: v for k, v in payload.items()
        if k not in ("started_at", "finished_at", "replay_hash")
    }
    raw = json.dumps(
        cleaned, sort_keys=True, separators=(",", ":"), default=str,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def _assess_candidate(score: CandidateScore) -> CandidateAssessment:
    cont = probe(
        score.candidate,
        excluded_case_ids=excluded_polysemy_texts(),
    )
    nc_outcomes, nc_precision = _run_negative_controls_for(
        score.candidate.tokens,
    )

    issues: list[str] = []
    if score.info_precision != 1.0:
        issues.append(f"info_precision={score.info_precision} != 1.0")
    if score.coverage < 0.30:
        issues.append(f"coverage={score.coverage} < 0.30")
    if cont.contamination_risk > 0.0:
        issues.append(
            f"contamination_risk={cont.contamination_risk} > 0.0"
        )
    if nc_precision != 1.0:
        issues.append(
            f"negative_control_precision={nc_precision} != 1.0"
        )
    safe = not issues
    reason = "all four gates passed" if safe else "; ".join(issues)

    return CandidateAssessment(
        score=score,
        contamination=cont,
        negative_control_outcomes=nc_outcomes,
        negative_control_precision=nc_precision,
        safe=safe,
        reason=reason,
    )


def build_disambiguator_report(
    *,
    started_at: datetime,
    finished_at: datetime,
) -> FrameDisambiguatorProbeReport:
    targets = extract_polysemy_targets()
    counters = extract_thermo_counter_set()
    if len(targets) != 15:
        raise RuntimeError(
            f"expected exactly 15 polysemy targets, got {len(targets)}"
        )
    if len(counters) < 5:
        raise RuntimeError(
            f"thermo counter set has {len(counters)}, need >= 5"
        )
    candidates = generate_candidates(targets)
    if len(candidates) < 10:
        raise RuntimeError(
            f"only {len(candidates)} candidates generated, need >= 10"
        )
    scores = score_all(candidates, targets, counters)
    assessments = tuple(_assess_candidate(s) for s in scores)

    safe = [a for a in assessments if a.safe]
    if safe:
        # Deterministic tie-break: highest coverage first, then
        # smallest token-set, then candidate_id sort.
        safe.sort(key=lambda a: (
            -a.score.coverage,
            len(a.score.candidate.tokens),
            a.score.candidate.candidate_id,
        ))
        chosen = safe[0]
        recommended_id = chosen.score.candidate.candidate_id
        recommended_tokens = chosen.score.candidate.tokens
    else:
        recommended_id = "NONE"
        recommended_tokens = ()

    payload = {
        "target_count": len(targets),
        "counter_count": len(counters),
        "candidate_count": len(candidates),
        "targets": [t.to_dict() for t in targets],
        "counters": [c.to_dict() for c in counters],
        "assessments": [a.to_dict() for a in assessments],
        "recommended_next": recommended_id,
        "recommended_tokens": list(recommended_tokens),
    }
    return FrameDisambiguatorProbeReport(
        started_at=started_at,
        finished_at=finished_at,
        target_count=len(targets),
        counter_count=len(counters),
        candidate_count=len(candidates),
        targets=targets,
        counters=counters,
        assessments=assessments,
        recommended_next=recommended_id,
        recommended_tokens=recommended_tokens,
        replay_hash=_replay_hash(payload),
    )


__all__ = [
    "CandidateAssessment",
    "FrameDisambiguatorProbeReport",
    "NegativeControlOutcome",
    "build_disambiguator_report",
]
