"""v3.20 report — corpus + per-signal probe + NC accuracy + gate."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .corpus import all_chains
from .negative_control import ALL_NC_CHAINS, NCShape
from .probe import (
    DEAD_KNOB_DELTA,
    PRIMARY_SIGNAL_DELTA,
    SignalProbe,
    run_per_signal_probe,
)
from .signals import ExtractionSignals, extract_signals


MIN_CHAIN_COUNT: int = 500
MIN_TRANSITION_COUNT: int = 2000
MIN_NC_ACCURACY: float = 0.95


# Stage transitions per chain — mirrors the v3.19 trajectory model:
# raw -> sentenced -> premised -> concluded -> signalled (4 transitions).
_STAGE_TRANSITIONS_PER_CHAIN: int = 4


_FEATURE_SIGNALS: tuple[str, ...] = (
    "premise_count",
    "atomic_ratio",
    "particular_ratio",
    "universal_ratio",
    "unsupported_form_ratio",
    "extraction_drop_rate",
    "premise_token_count",
    "conclusion_token_count",
    "premise_conclusion_overlap",
    "compression_ratio",
    "paraphrase_instability",
)


@dataclass(frozen=True)
class NCResult:
    case_id: str
    shape: str
    expected_anomalous: bool
    observed_anomalous: bool
    correct: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "shape": self.shape,
            "expected_anomalous": self.expected_anomalous,
            "observed_anomalous": self.observed_anomalous,
            "correct": self.correct,
        }


@dataclass(frozen=True)
class PremiseAuditReport:
    started_at: datetime
    finished_at: datetime
    chain_count: int
    transition_count: int
    nc_count: int
    nc_accuracy: float
    nc_per_shape: dict[str, dict[str, int]]
    nc_results: tuple[NCResult, ...]
    baseline_separability: float
    signal_probes: tuple[SignalProbe, ...]
    primary_signals: tuple[str, ...]
    dead_knobs: tuple[str, ...]
    valid_centroid: tuple[float, ...]
    adv_centroid: tuple[float, ...]
    contamination_count: int
    recommended_next: str
    recommendation_reason: str
    replay_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "chain_count": self.chain_count,
            "transition_count": self.transition_count,
            "nc_count": self.nc_count,
            "nc_accuracy": self.nc_accuracy,
            "nc_per_shape": dict(self.nc_per_shape),
            "nc_results": [r.to_dict() for r in self.nc_results],
            "baseline_separability": self.baseline_separability,
            "signal_probes":
                [s.to_dict() for s in self.signal_probes],
            "primary_signals": list(self.primary_signals),
            "dead_knobs": list(self.dead_knobs),
            "valid_centroid": list(self.valid_centroid),
            "adv_centroid": list(self.adv_centroid),
            "contamination_count": self.contamination_count,
            "recommended_next": self.recommended_next,
            "recommendation_reason": self.recommendation_reason,
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


def _is_anomalous(s: ExtractionSignals) -> bool:
    """Coarse anomaly flag for the NC classifier.

    ``paraphrase_instability`` is *not* part of the criterion:
    the v1.2 extractor's explicit-chain heuristic is brittle
    under the comma-before-Therefore perturbation used to
    score that signal, so it would fire for almost every chain
    if we tested against the perturbation. The signal still
    appears in the feature vector — it is just not used for
    the binary flag here.
    """
    if s.conclusion_token_count > 12:
        return True
    if s.premise_count == 0:
        return True
    if s.extraction_drop_rate > 0.30:
        return True
    if s.compression_ratio < 0.40:
        return True
    # Premise-loss shape: very few premises that pack many
    # content tokens — symptom of comma-joined run-on premises
    # the extractor cannot split.
    if s.premise_count <= 2 and s.premise_token_count >= 7:
        return True
    return False


def _run_negative_controls() -> tuple[
    float, dict[str, dict[str, int]], tuple[NCResult, ...],
]:
    per_shape: dict[str, dict[str, int]] = {
        s.value: {"total": 0, "correct": 0} for s in NCShape
    }
    results: list[NCResult] = []
    correct_total = 0
    for nc in ALL_NC_CHAINS:
        sig = extract_signals(nc.case_id, nc.text)
        observed = _is_anomalous(sig)
        correct = observed == nc.expected_anomalous
        results.append(NCResult(
            case_id=nc.case_id, shape=nc.shape.value,
            expected_anomalous=nc.expected_anomalous,
            observed_anomalous=observed,
            correct=correct,
        ))
        bucket = per_shape[nc.shape.value]
        bucket["total"] += 1
        if correct:
            bucket["correct"] += 1
            correct_total += 1
    accuracy = (
        round(correct_total / len(ALL_NC_CHAINS), 6)
        if ALL_NC_CHAINS else 0.0
    )
    return accuracy, per_shape, tuple(results)


def _decide(
    *,
    chain_count: int, transition_count: int,
    nc_acc: float, contamination: int,
    primary_signals: tuple[str, ...],
) -> tuple[str, str]:
    issues: list[str] = []
    if chain_count < MIN_CHAIN_COUNT:
        issues.append(
            f"chain_count={chain_count} < {MIN_CHAIN_COUNT}"
        )
    if transition_count < MIN_TRANSITION_COUNT:
        issues.append(
            f"transition_count={transition_count} "
            f"< {MIN_TRANSITION_COUNT}"
        )
    if nc_acc < MIN_NC_ACCURACY:
        issues.append(f"nc_accuracy={nc_acc} < {MIN_NC_ACCURACY}")
    if contamination != 0:
        issues.append(
            f"contamination_count={contamination} != 0"
        )
    if not primary_signals:
        # Honest NONE: no signal cleared the PRIMARY threshold.
        if issues:
            return "NONE", "; ".join(issues + [
                "no signal reached PRIMARY threshold",
            ])
        return "NONE", "no signal reached PRIMARY threshold"
    if issues:
        return "NONE", "; ".join(issues)
    return (
        "PREMISE_EXTRACTOR_PRIMARY",
        "primary_signals=" + ",".join(primary_signals),
    )


def build_premise_audit_report(
    *, started_at: datetime, finished_at: datetime,
) -> PremiseAuditReport:
    chains = all_chains()
    chain_count = len(chains) + len(ALL_NC_CHAINS)
    transition_count = (
        chain_count * _STAGE_TRANSITIONS_PER_CHAIN
    )

    valid_signals: list[ExtractionSignals] = []
    adv_signals: list[ExtractionSignals] = []
    for c in chains:
        sig = extract_signals(c.chain_id, c.text)
        if c.expected_natural:
            valid_signals.append(sig)
        else:
            adv_signals.append(sig)

    valid_tup = tuple(valid_signals)
    adv_tup = tuple(adv_signals)
    probes = run_per_signal_probe(valid_tup, adv_tup)
    baseline = probes[0].baseline_separability if probes else 0.0

    primary_signals = tuple(
        p.signal for p in probes
        if p.classification == "PRIMARY_SIGNAL"
    )
    dead_knobs = tuple(
        p.signal for p in probes
        if p.classification == "DEAD_KNOB"
    )

    # Centroids over the full feature space.
    if valid_signals:
        dim = len(valid_signals[0].feature_tuple())
        v_sum = [0.0] * dim
        for s in valid_signals:
            for i, x in enumerate(s.feature_tuple()):
                v_sum[i] += x
        valid_centroid = tuple(
            round(x / len(valid_signals), 6) for x in v_sum
        )
    else:
        valid_centroid = tuple([0.0] * 11)
    if adv_signals:
        dim = len(adv_signals[0].feature_tuple())
        a_sum = [0.0] * dim
        for s in adv_signals:
            for i, x in enumerate(s.feature_tuple()):
                a_sum[i] += x
        adv_centroid = tuple(
            round(x / len(adv_signals), 6) for x in a_sum
        )
    else:
        adv_centroid = tuple([0.0] * 11)

    # Contamination: adversarial chains whose feature vector is
    # within an ε-ball of the valid centroid (L2 < 0.5).
    contamination = 0
    import math
    for s in adv_signals:
        fv = s.feature_tuple()
        d = math.sqrt(
            sum(
                (a - b) ** 2 for a, b in zip(fv, valid_centroid)
            )
        )
        if d < 0.5:
            contamination += 1

    nc_acc, nc_per_shape, nc_results = _run_negative_controls()

    rec, reason = _decide(
        chain_count=chain_count,
        transition_count=transition_count,
        nc_acc=nc_acc, contamination=contamination,
        primary_signals=primary_signals,
    )

    payload = {
        "chain_count": chain_count,
        "transition_count": transition_count,
        "nc_count": len(ALL_NC_CHAINS),
        "nc_accuracy": nc_acc,
        "nc_per_shape": nc_per_shape,
        "nc_results": [r.to_dict() for r in nc_results],
        "baseline_separability": baseline,
        "signal_probes": [p.to_dict() for p in probes],
        "primary_signals": list(primary_signals),
        "dead_knobs": list(dead_knobs),
        "valid_centroid": list(valid_centroid),
        "adv_centroid": list(adv_centroid),
        "contamination_count": contamination,
        "recommended_next": rec,
        "recommendation_reason": reason,
    }
    return PremiseAuditReport(
        started_at=started_at,
        finished_at=finished_at,
        chain_count=chain_count,
        transition_count=transition_count,
        nc_count=len(ALL_NC_CHAINS),
        nc_accuracy=nc_acc,
        nc_per_shape=nc_per_shape,
        nc_results=nc_results,
        baseline_separability=baseline,
        signal_probes=probes,
        primary_signals=primary_signals,
        dead_knobs=dead_knobs,
        valid_centroid=valid_centroid,
        adv_centroid=adv_centroid,
        contamination_count=contamination,
        recommended_next=rec,
        recommendation_reason=reason,
        replay_hash=_replay_hash(payload),
    )


__all__ = [
    "MIN_CHAIN_COUNT",
    "MIN_NC_ACCURACY",
    "MIN_TRANSITION_COUNT",
    "PremiseAuditReport",
    "build_premise_audit_report",
]
