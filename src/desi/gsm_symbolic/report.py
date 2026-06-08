"""GSM-Symbolic G3 - deterministic two-arm comparison report.

Takes a *baseline* and a *DESi* prediction set, computes the layered
invariance comparison (``scoring.py``), and renders a deterministic
markdown + dict summary carrying a closed-set verdict.

The verdict encodes the design's honesty guard
(``docs/gsm_symbolic_experiment_design.md`` section 1): a pure accuracy
gain with no invariance gain does **not** support the thesis and is
classified ``ACCURACY_WITHOUT_INVARIANCE`` - never an improvement. Only
``STABILITY_IMPROVED`` counts as thesis support.

Operates on whatever prediction sets it is given - the deterministic
stub fixtures here, or a real solver's outputs at the live G2 stage. No
model call, no network.
"""
from __future__ import annotations

from dataclasses import dataclass

from .scoring import (
    Predictions,
    noop_gap,
    score_predictions,
    template_stability_gain,
)

VERDICT_IMPROVED = "STABILITY_IMPROVED"
VERDICT_UNCHANGED = "STABILITY_UNCHANGED"
VERDICT_REGRESSED = "STABILITY_REGRESSED"
VERDICT_ACCURACY_ONLY = "ACCURACY_WITHOUT_INVARIANCE"

VERDICTS: tuple[str, ...] = (
    VERDICT_IMPROVED,
    VERDICT_UNCHANGED,
    VERDICT_REGRESSED,
    VERDICT_ACCURACY_ONLY,
)

_DISCLAIMER = (
    "Network-free, deterministic comparison over locally-vendored "
    "GSM-Symbolic-shaped fixtures. The prediction sets are illustrative "
    "stub arms, NOT model outputs; no empirical claim about any model "
    "or about DESi is made. Real solver arms arrive at the live G2 stage."
)


def classify(baseline: Predictions, desi: Predictions) -> str:
    """Closed-set verdict for a baseline-vs-DESi comparison.

    Ordering matters: the invariance gain is decided first, so a pure
    accuracy gain can never be reported as a stability improvement.
    """
    gain = template_stability_gain(baseline, desi)
    if gain > 0:
        return VERDICT_IMPROVED
    if gain < 0:
        return VERDICT_REGRESSED
    # gain == 0: invariance did not move - check whether accuracy did.
    b_acc = score_predictions(baseline).frame_accuracy
    d_acc = score_predictions(desi).frame_accuracy
    if d_acc > b_acc:
        return VERDICT_ACCURACY_ONLY
    return VERDICT_UNCHANGED


def supports_thesis(verdict: str) -> bool:
    """Only a genuine invariance gain supports the DESi thesis."""
    return verdict == VERDICT_IMPROVED


@dataclass(frozen=True)
class ComparisonReport:
    verdict: str
    supports_thesis: bool
    template_stability_gain: float
    baseline_noop_gap: float
    desi_noop_gap: float
    noop_gap_reduction: float
    baseline_metrics: dict[str, object]
    desi_metrics: dict[str, object]
    disclaimer: str

    def to_dict(self) -> dict[str, object]:
        return {
            "verdict": self.verdict,
            "supports_thesis": self.supports_thesis,
            "template_stability_gain": self.template_stability_gain,
            "baseline_noop_gap": self.baseline_noop_gap,
            "desi_noop_gap": self.desi_noop_gap,
            "noop_gap_reduction": self.noop_gap_reduction,
            "baseline_metrics": self.baseline_metrics,
            "desi_metrics": self.desi_metrics,
            "disclaimer": self.disclaimer,
        }


def build_report(
    baseline: Predictions, desi: Predictions,
) -> ComparisonReport:
    b = score_predictions(baseline)
    d = score_predictions(desi)
    b_noop = noop_gap(baseline)
    d_noop = noop_gap(desi)
    verdict = classify(baseline, desi)
    return ComparisonReport(
        verdict=verdict,
        supports_thesis=supports_thesis(verdict),
        template_stability_gain=template_stability_gain(baseline, desi),
        baseline_noop_gap=b_noop,
        desi_noop_gap=d_noop,
        # Positive => DESi shrank the noop-clause accuracy drop.
        noop_gap_reduction=round(b_noop - d_noop, 6),
        baseline_metrics=b.to_dict(),
        desi_metrics=d.to_dict(),
        disclaimer=_DISCLAIMER,
    )


def _row(label: str, base: object, desi: object) -> str:
    return f"| {label} | {base} | {desi} |"


def render_markdown(report: ComparisonReport) -> str:
    b = report.baseline_metrics
    d = report.desi_metrics
    lines = [
        "# GSM-Symbolic frame-invariance: baseline vs DESi",
        "",
        f"**Verdict:** {report.verdict}  ",
        f"**Supports thesis:** {report.supports_thesis}",
        "",
        "| Metric | baseline | DESi |",
        "|---|---|---|",
        _row(
            "strict_group_correctness",
            b["strict_group_correctness"],
            d["strict_group_correctness"],
        ),
        _row(
            "answer_consistency",
            b["answer_consistency"],
            d["answer_consistency"],
        ),
        _row(
            "error_stability",
            b["error_stability"],
            d["error_stability"],
        ),
        _row("frame_accuracy", b["frame_accuracy"], d["frame_accuracy"]),
        "",
        f"- Template Stability Gain: {report.template_stability_gain}",
        (
            f"- NoOp gap: baseline {report.baseline_noop_gap} / "
            f"DESi {report.desi_noop_gap} "
            f"(reduction {report.noop_gap_reduction})"
        ),
        "",
        f"> {report.disclaimer}",
        "",
    ]
    return "\n".join(lines)


__all__ = [
    "VERDICTS",
    "VERDICT_ACCURACY_ONLY",
    "VERDICT_IMPROVED",
    "VERDICT_REGRESSED",
    "VERDICT_UNCHANGED",
    "ComparisonReport",
    "build_report",
    "classify",
    "render_markdown",
    "supports_thesis",
]
