"""GSM-Symbolic G3 - two-arm comparison report tests.

Pins the closed-set verdict logic - especially the honesty guard:
an accuracy gain with no invariance gain must classify as
ACCURACY_WITHOUT_INVARIANCE and must NOT count as thesis support.
"""
from __future__ import annotations

from desi.gsm_symbolic import (
    VERDICTS,
    all_correct_predictions,
    build_report,
    classify,
    constant_wrong_predictions,
    first_only_correct_predictions,
    noop_fragile_predictions,
    render_markdown,
)


def test_verdict_closed_set() -> None:
    assert len(VERDICTS) == 4
    assert classify(
        first_only_correct_predictions(), all_correct_predictions(),
    ) in VERDICTS


# --- improvement --------------------------------
def test_invariance_gain_is_improvement() -> None:
    r = build_report(
        baseline=first_only_correct_predictions(),
        desi=all_correct_predictions(),
    )
    assert r.verdict == "STABILITY_IMPROVED"
    assert r.supports_thesis is True
    assert r.template_stability_gain == 1.0


# --- honesty guard ------------------------------
def test_accuracy_without_invariance_does_not_support_thesis() -> None:
    """baseline all-wrong (acc 0, strict 0); desi first-only-correct
    (acc > 0 but strict still 0). Accuracy rose, invariance did not ->
    the guard must fire and thesis support must be False."""
    r = build_report(
        baseline=constant_wrong_predictions(),
        desi=first_only_correct_predictions(),
    )
    assert r.template_stability_gain == 0.0
    assert r.desi_metrics["frame_accuracy"] > (
        r.baseline_metrics["frame_accuracy"]
    )
    assert r.verdict == "ACCURACY_WITHOUT_INVARIANCE"
    assert r.supports_thesis is False


# --- unchanged ----------------------------------
def test_equal_arms_are_unchanged() -> None:
    p = all_correct_predictions()
    r = build_report(baseline=p, desi=p)
    assert r.verdict == "STABILITY_UNCHANGED"
    assert r.supports_thesis is False
    assert r.template_stability_gain == 0.0


# --- regression ---------------------------------
def test_invariance_loss_is_regression() -> None:
    r = build_report(
        baseline=all_correct_predictions(),
        desi=first_only_correct_predictions(),
    )
    assert r.verdict == "STABILITY_REGRESSED"
    assert r.supports_thesis is False
    assert r.template_stability_gain == -1.0


# --- noop gap reduction -------------------------
def test_noop_gap_reduction_is_signed_difference() -> None:
    # baseline drops on noop clauses; desi is perfect -> positive
    # reduction (DESi shrank the noop-induced accuracy drop).
    r = build_report(
        baseline=noop_fragile_predictions(),
        desi=all_correct_predictions(),
    )
    assert r.baseline_noop_gap == 1.0
    assert r.desi_noop_gap == 0.0
    assert r.noop_gap_reduction == 1.0


# --- determinism / rendering --------------------
def test_report_is_deterministic() -> None:
    a = build_report(
        baseline=first_only_correct_predictions(),
        desi=all_correct_predictions(),
    )
    b = build_report(
        baseline=first_only_correct_predictions(),
        desi=all_correct_predictions(),
    )
    assert a.to_dict() == b.to_dict()


def test_markdown_is_deterministic_and_labelled() -> None:
    r = build_report(
        baseline=first_only_correct_predictions(),
        desi=all_correct_predictions(),
    )
    md1 = render_markdown(r)
    md2 = render_markdown(r)
    assert md1 == md2
    assert "STABILITY_IMPROVED" in md1
    assert "Template Stability Gain" in md1
    # honesty label must travel with the rendered report
    assert "NOT model outputs" in md1
