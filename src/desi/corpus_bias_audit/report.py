"""Aufgabe 10 — v5.3 bias-audit report and recommendation
gate.

The recommendation cascade:

* ``CORPUS_UNBIASED``         — every bias threshold and
  every counterfactual threshold passes,
  ``nc_accuracy >= 0.95``.
* ``CORPUS_PARTIALLY_BIASED`` — ``coverage_gain <= 0.20``
  but at least one threshold fails.
* ``CORPUS_FIT_TO_TAXONOMY``  — ``coverage_gain > 0.20``
  OR ``probe_gain > 0.20`` OR ``false_activation_reduction
  > 0`` (probes were hidden by the rewrites).
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from .bias_metrics import (
    BiasMetrics, compute_bias_metrics,
)
from .diff import ChainAudit, audit_pair
from .enums import BiasRecommendation
from .negative_controls import (
    all_rewrite_ncs, classification_accuracy,
)
from .raw_corpus import (
    all_pairs, raw_recovery_rate,
)
from .replay import (
    ReplayOutcome, RewriteInfluence,
    compute_rewrite_influence, replay_final, replay_raw,
)


# ---------------------------------------------------------------------------
# Gate thresholds (closed)
# ---------------------------------------------------------------------------


MAX_REWRITE_FRACTION              = 0.25
MAX_VALID_PROBE_AVOIDANCE         = 0.20
MAX_INVALID_PROBE_ALIGNMENT       = 0.20
MAX_DOMAIN_BIAS_VARIANCE          = 0.15
MAX_SEMANTIC_SHIFT_MEAN           = 0.10
MAX_SEMANTIC_SHIFT_MAX            = 0.25
MAX_DELTA_COVERAGE                = 0.10
MAX_DELTA_PROBE                   = 0.10
MAX_COVERAGE_GAIN                 = 0.10
MAX_PROBE_GAIN                    = 0.10
MIN_NC_ACCURACY                   = 0.95
PARTIAL_FLOOR_COVERAGE_GAIN       = 0.20
FIT_TRIGGER_COVERAGE_GAIN         = 0.20
FIT_TRIGGER_PROBE_GAIN            = 0.20


# ---------------------------------------------------------------------------
# Report dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class V53Report:
    corpus_size: int
    rewritten_count: int
    raw_recovery_rate: float
    label_preservation_rate: float
    bias_metrics: BiasMetrics
    raw_replay: ReplayOutcome
    final_replay: ReplayOutcome
    rewrite_influence: RewriteInfluence
    delta_coverage: float
    delta_probe_transfer: float
    nc_count: int
    nc_accuracy: float
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "corpus_size": self.corpus_size,
            "rewritten_count": self.rewritten_count,
            "raw_recovery_rate": self.raw_recovery_rate,
            "label_preservation_rate":
                self.label_preservation_rate,
            "bias_metrics": self.bias_metrics.to_dict(),
            "raw_replay": self.raw_replay.to_dict(),
            "final_replay": self.final_replay.to_dict(),
            "rewrite_influence":
                self.rewrite_influence.to_dict(),
            "delta_coverage": self.delta_coverage,
            "delta_probe_transfer":
                self.delta_probe_transfer,
            "nc_count": self.nc_count,
            "nc_accuracy": self.nc_accuracy,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


# ---------------------------------------------------------------------------
# Gate
# ---------------------------------------------------------------------------


def _decide(
    *, bias: BiasMetrics,
    raw: ReplayOutcome, final: ReplayOutcome,
    influence: RewriteInfluence, nc_accuracy: float,
    delta_coverage: float, delta_probe: float,
    label_preservation_rate: float,
    raw_recovery: float,
) -> tuple[str, tuple[str, ...]]:
    checks = (
        (
            raw_recovery >= 1.0,
            f"raw_recovery_rate {raw_recovery} == 1.00",
        ),
        (
            label_preservation_rate >= 1.0,
            f"label_preservation_rate "
            f"{label_preservation_rate} == 1.00",
        ),
        (
            bias.rewrite_fraction
            <= MAX_REWRITE_FRACTION,
            f"rewrite_fraction "
            f"{bias.rewrite_fraction} <= "
            f"{MAX_REWRITE_FRACTION}",
        ),
        (
            bias.valid_probe_avoidance_rate
            <= MAX_VALID_PROBE_AVOIDANCE,
            f"valid_probe_avoidance_rate "
            f"{bias.valid_probe_avoidance_rate} <= "
            f"{MAX_VALID_PROBE_AVOIDANCE}",
        ),
        (
            bias.invalid_probe_alignment_rate
            <= MAX_INVALID_PROBE_ALIGNMENT,
            f"invalid_probe_alignment_rate "
            f"{bias.invalid_probe_alignment_rate} <= "
            f"{MAX_INVALID_PROBE_ALIGNMENT}",
        ),
        (
            bias.domain_bias_variance
            <= MAX_DOMAIN_BIAS_VARIANCE,
            f"domain_bias_variance "
            f"{bias.domain_bias_variance} <= "
            f"{MAX_DOMAIN_BIAS_VARIANCE}",
        ),
        (
            bias.semantic_shift_mean
            <= MAX_SEMANTIC_SHIFT_MEAN,
            f"semantic_shift_mean "
            f"{bias.semantic_shift_mean} <= "
            f"{MAX_SEMANTIC_SHIFT_MEAN}",
        ),
        (
            bias.semantic_shift_max
            <= MAX_SEMANTIC_SHIFT_MAX,
            f"semantic_shift_max "
            f"{bias.semantic_shift_max} <= "
            f"{MAX_SEMANTIC_SHIFT_MAX}",
        ),
        (
            abs(delta_coverage) <= MAX_DELTA_COVERAGE,
            f"delta_coverage |{delta_coverage}| <= "
            f"{MAX_DELTA_COVERAGE}",
        ),
        (
            abs(delta_probe) <= MAX_DELTA_PROBE,
            f"delta_probe_transfer |{delta_probe}| <= "
            f"{MAX_DELTA_PROBE}",
        ),
        (
            raw.safe_probe_false_activation == 0,
            f"raw safe_probe_false_activation "
            f"{raw.safe_probe_false_activation} == 0",
        ),
        (
            influence.coverage_gain_from_rewrites
            <= MAX_COVERAGE_GAIN,
            f"coverage_gain_from_rewrites "
            f"{influence.coverage_gain_from_rewrites} "
            f"<= {MAX_COVERAGE_GAIN}",
        ),
        (
            influence.probe_gain_from_rewrites
            <= MAX_PROBE_GAIN,
            f"probe_gain_from_rewrites "
            f"{influence.probe_gain_from_rewrites} <= "
            f"{MAX_PROBE_GAIN}",
        ),
        (
            nc_accuracy >= MIN_NC_ACCURACY,
            f"nc_accuracy {nc_accuracy} >= "
            f"{MIN_NC_ACCURACY}",
        ),
    )
    reasons: list[str] = []
    passed = 0
    for ok, msg in checks:
        if ok:
            passed += 1
            reasons.append(f"PASS: {msg}")
        else:
            reasons.append(f"FAIL: {msg}")
    # FIT_TO_TAXONOMY triggers
    coverage_gain = influence.coverage_gain_from_rewrites
    probe_gain = influence.probe_gain_from_rewrites
    if (
        coverage_gain > FIT_TRIGGER_COVERAGE_GAIN
        or probe_gain > FIT_TRIGGER_PROBE_GAIN
        or influence.false_activation_reduction > 0
    ):
        return (
            BiasRecommendation.FIT_TO_TAXONOMY.value,
            tuple(reasons),
        )
    if passed == len(checks):
        return (
            BiasRecommendation.UNBIASED.value,
            tuple(reasons),
        )
    if coverage_gain <= PARTIAL_FLOOR_COVERAGE_GAIN:
        return (
            BiasRecommendation.PARTIALLY_BIASED.value,
            tuple(reasons),
        )
    return (
        BiasRecommendation.FIT_TO_TAXONOMY.value,
        tuple(reasons),
    )


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------


def build_report() -> V53Report:
    pairs = all_pairs()
    audits = tuple(audit_pair(p) for p in pairs)
    bias = compute_bias_metrics(audits)
    raw = replay_raw()
    final = replay_final()
    influence = compute_rewrite_influence(raw, final)
    delta_coverage = round(
        final.taxonomy_coverage - raw.taxonomy_coverage, 6,
    )
    delta_probe = round(
        final.probe_transfer_rate
        - raw.probe_transfer_rate, 6,
    )
    label_pres = (
        sum(1 for a in audits if a.label_preservation)
        / len(audits)
    ) if audits else 0.0
    nc_acc = classification_accuracy()
    nc_count = len(all_rewrite_ncs())
    verdict, rationale = _decide(
        bias=bias, raw=raw, final=final,
        influence=influence, nc_accuracy=nc_acc,
        delta_coverage=delta_coverage,
        delta_probe=delta_probe,
        label_preservation_rate=label_pres,
        raw_recovery=raw_recovery_rate(),
    )
    return V53Report(
        corpus_size=len(pairs),
        rewritten_count=sum(
            1 for a in audits if a.was_rewritten
        ),
        raw_recovery_rate=raw_recovery_rate(),
        label_preservation_rate=round(label_pres, 6),
        bias_metrics=bias,
        raw_replay=raw, final_replay=final,
        rewrite_influence=influence,
        delta_coverage=delta_coverage,
        delta_probe_transfer=delta_probe,
        nc_count=nc_count, nc_accuracy=nc_acc,
        recommendation=verdict, rationale=rationale,
    )


def build_diff_artifact() -> dict[str, object]:
    pairs = all_pairs()
    audits = tuple(audit_pair(p) for p in pairs)
    return {
        "pairs": [
            {
                "chain_id": p.chain_id,
                "domain": p.domain,
                "ground_truth": p.ground_truth,
                "was_rewritten": p.was_rewritten,
                "raw_text": p.raw_text,
                "final_text": p.final_text,
            }
            for p in pairs
        ],
        "audits": [a.to_dict() for a in audits],
    }


__all__ = [
    "FIT_TRIGGER_COVERAGE_GAIN",
    "FIT_TRIGGER_PROBE_GAIN",
    "MAX_COVERAGE_GAIN",
    "MAX_DELTA_COVERAGE",
    "MAX_DELTA_PROBE",
    "MAX_DOMAIN_BIAS_VARIANCE",
    "MAX_INVALID_PROBE_ALIGNMENT",
    "MAX_PROBE_GAIN",
    "MAX_REWRITE_FRACTION",
    "MAX_SEMANTIC_SHIFT_MAX",
    "MAX_SEMANTIC_SHIFT_MEAN",
    "MAX_VALID_PROBE_AVOIDANCE",
    "MIN_NC_ACCURACY",
    "PARTIAL_FLOOR_COVERAGE_GAIN",
    "V53Report", "build_diff_artifact", "build_report",
]
