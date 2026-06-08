"""GSM-Symbolic G1 - layered frame-invariance metrics.

Computes the invariance metrics defined in
``docs/gsm_symbolic_experiment_design.md`` (section 5.1) from a set of
*predictions* (task_id -> predicted answer string). A prediction set is
whatever a solver arm produced; this module is solver-agnostic and
deterministic, so the metric definitions can be validated and replayed
without any model call.

Headline vs diagnostic (per the design):

* **strict_group_correctness** (HEADLINE): share of templates for which
  *every* sampled instance is correct.
* **answer_consistency** (diagnostic): share of templates whose instances
  share the same correctness status (all correct OR all wrong) - i.e. the
  arm behaves consistently across surface variants even when jointly
  wrong.
* **error_stability** (diagnostic): among templates that are not
  all-correct, the share whose wrong instances all produced the *same*
  wrong answer (a stable error rather than a drifting one).
* **frame_accuracy**: mean per-instance correctness (reported, not the
  headline).

``template_stability_gain`` is the single comparative number
(strict_group_correctness of one arm minus another). ``noop_gap`` is the
P2 robustness signal: base-instance accuracy minus noop-instance
accuracy.

Compute-cost metrics (design 5.3) are intentionally NOT here: they only
become meaningful with real model calls and belong to the live G2 stage.
"""
from __future__ import annotations

from dataclasses import dataclass

from .groups import TemplateGroup, build_groups
from .normalizer import all_normalized_tasks

# A prediction set maps a task_id to the arm's predicted answer string.
Predictions = dict[str, str]


def _round(x: float) -> float:
    return round(x, 6)


@dataclass(frozen=True)
class InvarianceMetrics:
    total_groups: int
    total_tasks: int
    frame_accuracy: float
    strict_group_correctness: float
    answer_consistency: float
    error_stability: float

    def to_dict(self) -> dict[str, object]:
        return {
            "total_groups": self.total_groups,
            "total_tasks": self.total_tasks,
            "frame_accuracy": self.frame_accuracy,
            "strict_group_correctness": self.strict_group_correctness,
            "answer_consistency": self.answer_consistency,
            "error_stability": self.error_stability,
        }


def _is_correct(predictions: Predictions, task_id: str, gold: str) -> bool:
    return predictions.get(task_id) == gold


def score_predictions(
    predictions: Predictions,
    groups: tuple[TemplateGroup, ...] | None = None,
) -> InvarianceMetrics:
    gs = build_groups() if groups is None else groups
    total_groups = len(gs)
    total_tasks = 0
    correct_tasks = 0
    strict_groups = 0
    consistent_groups = 0
    error_groups = 0
    stable_error_groups = 0

    for g in gs:
        flags: list[bool] = []
        wrong_answers: list[str | None] = []
        for t in g.tasks:
            total_tasks += 1
            ok = _is_correct(predictions, t.task_id, t.answer)
            flags.append(ok)
            if ok:
                correct_tasks += 1
            else:
                wrong_answers.append(predictions.get(t.task_id))
        all_correct = all(flags)
        # "consistent" = every instance shares one correctness status.
        same_status = all(flags) or not any(flags)
        if all_correct:
            strict_groups += 1
        if same_status:
            consistent_groups += 1
        if not all_correct:
            error_groups += 1
            # Stable error iff all wrong instances gave one wrong answer.
            if len(set(wrong_answers)) == 1:
                stable_error_groups += 1

    return InvarianceMetrics(
        total_groups=total_groups,
        total_tasks=total_tasks,
        frame_accuracy=(
            _round(correct_tasks / total_tasks) if total_tasks else 0.0
        ),
        strict_group_correctness=(
            _round(strict_groups / total_groups) if total_groups else 0.0
        ),
        answer_consistency=(
            _round(consistent_groups / total_groups)
            if total_groups else 0.0
        ),
        # No error groups -> errors are vacuously stable.
        error_stability=(
            _round(stable_error_groups / error_groups)
            if error_groups else 1.0
        ),
    )


def template_stability_gain(
    baseline: Predictions, desi: Predictions,
) -> float:
    """strict_group_correctness(desi) - strict_group_correctness(baseline).

    The single comparative number the thesis turns on: a positive gain
    means the DESi arm keeps more whole templates consistent under
    symbolic perturbation than the baseline arm.
    """
    gs = build_groups()
    b = score_predictions(baseline, gs).strict_group_correctness
    d = score_predictions(desi, gs).strict_group_correctness
    return _round(d - b)


def noop_gap(predictions: Predictions) -> float:
    """base-instance accuracy - noop-instance accuracy over P2.

    A noop clause must not change the answer, so a robust arm keeps its
    accuracy (gap ~ 0); a fragile one drops (gap > 0).
    """
    base_total = base_ok = noop_total = noop_ok = 0
    for t in all_normalized_tasks():
        if t.variant != "p2":
            continue
        ok = _is_correct(predictions, t.task_id, t.answer)
        if t.clause_role == "base":
            base_total += 1
            base_ok += int(ok)
        elif t.clause_role == "noop":
            noop_total += 1
            noop_ok += int(ok)
    base_acc = base_ok / base_total if base_total else 0.0
    noop_acc = noop_ok / noop_total if noop_total else 0.0
    return _round(base_acc - noop_acc)


__all__ = [
    "InvarianceMetrics",
    "Predictions",
    "noop_gap",
    "score_predictions",
    "template_stability_gain",
]
