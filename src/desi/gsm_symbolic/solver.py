"""GSM-Symbolic G2 - two-arm solver harness (LLM for language).

This is the live-stage harness that turns tasks into *predictions* for
the two arms the thesis compares, then hands them to the existing,
solver-agnostic scoring/report stack (``scoring.py`` / ``report.py``).
It draws the boundary the project insists on - **LLM for language, rules
for logic**:

* the deterministic ``state.py`` structuring decides *what* is relevant
  (which clauses, which quantities) - that is the "rules" part;
* the model is only asked to read language and return a number - that is
  the "language" part. No scoring, ranking, or relevance decision is
  delegated to the model.

The model is reached through a tiny ``Solver`` seam so the whole pipeline
is exercisable offline: ``ScriptedSolver`` returns injected answers (it
solves nothing - what you inject is what you get), while
``build_openai_solver`` is the live swap-in (OpenAI-compatible, needs an
API key + network). Tests drive the scripted path; the live path is
import-clean (``openai`` is imported lazily) and raises a clear
``SolverConfigError`` when no key is configured.

Determinism: no built-in ``hash``; the live solver pins ``temperature=0``
to make a real run as reproducible as the provider allows. Compute-cost
metrics (design 5.3) still belong to a fuller live run and are not
fabricated here.
"""
from __future__ import annotations

import os
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from .normalizer import NormalizedGsmTask, all_normalized_tasks
from .report import ComparisonReport, build_report
from .scoring import Predictions
from .state import extract_state

# Thousands-separated numbers ("1,234.5") must match as ONE token — otherwise
# "1,234" splits into ['1', '234'] and the last-token rule returns '234'.
_NUMBER = re.compile(r"-?\d{1,3}(?:,\d{3})+(?:\.\d+)?|-?\d+(?:\.\d+)?")


class SolverConfigError(RuntimeError):
    """The requested solver cannot be built (e.g. no API key / no SDK)."""


def parse_answer(text: str, answer_type: str = "integer") -> str:
    """Extract the final answer from raw model text, deterministically.

    Takes the *last* numeric token (models put the final answer last) and
    normalises it to match the gold representation (gold answers are
    strings; integers carry no decimal point). Returns ``""`` when no
    number is present, which can never equal a gold value.
    """
    matches = _NUMBER.findall(text or "")
    if not matches:
        return ""
    token = matches[-1].replace(",", "")
    if answer_type == "integer":
        try:
            value = float(token)
        except ValueError:
            return token
        if value.is_integer():
            return str(int(value))
    return token


# --- prompts: the only place the model sees the task -------------------
def baseline_prompt(task: NormalizedGsmTask) -> str:
    """Raw arm: the unstructured question, as a baseline model sees it."""
    return (
        "Solve the math word problem. "
        "Reply with only the final number.\n\n"
        f"Problem: {task.question}\n"
        "Answer:"
    )


def desi_prompt(task: NormalizedGsmTask) -> str:
    """DESi arm: the same task, framed by the deterministic Level-A/B
    structuring - relevant clauses kept, suspected-irrelevant clauses
    named and set aside, quantities surfaced. The relevance decision is
    made by rules (``state.py``), never by the model."""
    state = extract_state(task)
    relevant = [c.text for c in state.relevant_clauses()]
    dropped = [c.text for c in state.irrelevant_clauses()]
    quantities = state.quantities()

    lines = [
        "Solve the math word problem using only the relevant "
        "information below. Reply with only the final number.",
        "",
        "Relevant statements:",
    ]
    lines += [f"  - {c}" for c in relevant]
    if quantities:
        lines += ["", f"Known quantities: {', '.join(quantities)}"]
    if dropped:
        lines += ["", "Ignore these irrelevant statements:"]
        lines += [f"  - {c}" for c in dropped]
    lines += ["", f"Answer type: {task.answer_type}", "Answer:"]
    return "\n".join(lines)


def relevant_only_prompt(task: NormalizedGsmTask) -> str:
    """Ablation arm: the DESi structuring with the irrelevant clauses
    *silently removed* instead of being named in an ignore-list.

    This deconfounds the two things ``desi_prompt`` changes at once:
    a shorter context (irrelevant content gone) and the explicit
    irrelevance *marking*. Everything else - intro line, relevant
    statements, quantities, answer-type footer - is byte-identical to
    ``desi_prompt``, so baseline→relevant_only isolates the pruning
    effect and relevant_only→desi isolates the marking effect."""
    state = extract_state(task)
    relevant = [c.text for c in state.relevant_clauses()]
    quantities = state.quantities()

    lines = [
        "Solve the math word problem using only the relevant "
        "information below. Reply with only the final number.",
        "",
        "Relevant statements:",
    ]
    lines += [f"  - {c}" for c in relevant]
    if quantities:
        lines += ["", f"Known quantities: {', '.join(quantities)}"]
    lines += ["", f"Answer type: {task.answer_type}", "Answer:"]
    return "\n".join(lines)


# --- the solver seam --------------------------------------------------
@runtime_checkable
class Solver(Protocol):
    def solve(self, prompt: str, *, task_id: str) -> str: ...


@dataclass
class ScriptedSolver:
    """Offline, deterministic fake: returns an injected answer per
    task_id (default for misses). It solves nothing - what you inject is
    what you get - so it can never smuggle in a real result."""

    answers: Mapping[str, str] = field(default_factory=dict)
    default: str = ""

    def solve(self, prompt: str, *, task_id: str) -> str:
        return self.answers.get(task_id, self.default)


@dataclass
class CallableSolver:
    """Wraps any ``prompt -> text`` callable (the live seam). Keeps this
    module free of a hard ``openai`` import dependency."""

    complete: Callable[[str], str]

    def solve(self, prompt: str, *, task_id: str) -> str:
        return self.complete(prompt)


def build_openai_solver(
    *,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
) -> CallableSolver:
    """Live swap-in: an OpenAI-compatible chat solver.

    Mirrors the AleXiona convention - a ``DEEPSEEK_API_KEY`` selects the
    DeepSeek endpoint/model, otherwise OpenAI. Raises ``SolverConfigError``
    (never a bare crash) when no key is configured or the SDK is missing,
    so the CLI can report the live path as unavailable cleanly. Not
    exercised by the offline test suite.
    """
    deepseek = os.environ.get("DEEPSEEK_API_KEY")
    key = api_key or deepseek or os.environ.get("OPENAI_API_KEY")
    if not key:
        raise SolverConfigError(
            "No LLM API key configured: set DEEPSEEK_API_KEY or "
            "OPENAI_API_KEY (or pass api_key=...) to run the live arm.",
        )
    if api_key is None and deepseek:
        base_url = base_url or "https://api.deepseek.com"
        model = model or "deepseek-chat"
    else:
        model = model or "gpt-4o"

    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover - env-dependent
        raise SolverConfigError(
            "The 'openai' package is required for the live solver "
            "(pip install openai).",
        ) from exc

    client = OpenAI(api_key=key, base_url=base_url)

    def complete(prompt: str) -> str:  # pragma: no cover - needs network
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        return response.choices[0].message.content or ""

    return CallableSolver(complete=complete)


# --- runner: tasks -> predictions -> report ---------------------------
def run_arm(
    solver: Solver,
    prompt_fn: Callable[[NormalizedGsmTask], str],
    tasks: Sequence[NormalizedGsmTask] | None = None,
) -> Predictions:
    """Produce one arm's prediction set by solving every task's prompt."""
    items = all_normalized_tasks() if tasks is None else tuple(tasks)
    predictions: Predictions = {}
    for task in items:
        raw = solver.solve(prompt_fn(task), task_id=task.task_id)
        predictions[task.task_id] = parse_answer(raw, task.answer_type)
    return predictions


def run_comparison(
    baseline_solver: Solver,
    desi_solver: Solver | None = None,
    tasks: Sequence[NormalizedGsmTask] | None = None,
) -> ComparisonReport:
    """Run both arms and build the deterministic comparison report.

    The usual live setup passes one model as both arms (``desi_solver``
    defaults to ``baseline_solver``): same model, two prompt strategies,
    so any difference is attributable to the structuring, not the model.
    """
    desi = desi_solver if desi_solver is not None else baseline_solver
    baseline_preds = run_arm(baseline_solver, baseline_prompt, tasks)
    desi_preds = run_arm(desi, desi_prompt, tasks)
    return build_report(baseline_preds, desi_preds)


def run_decomposition(
    baseline_solver: Solver,
    relevant_only_solver: Solver | None = None,
    desi_solver: Solver | None = None,
    tasks: Sequence[NormalizedGsmTask] | None = None,
) -> dict:
    """Three-arm ablation: decompose the DESi effect into pruning + marking.

    The two-arm comparison confounds two interventions, because the DESi
    prompt simultaneously *removes* irrelevant content (shorter context)
    and *names* it in an ignore-list (explicit marking). The middle arm
    (``relevant_only_prompt``) applies only the removal, so the headline
    metric decomposes exactly:

        pruning  = relevant_only - baseline   (shorter context alone)
        marking  = desi - relevant_only       (the ignore-list on top)
        total    = desi - baseline            (= pruning + marking)

    Solvers default to the baseline solver (same model, three prompt
    strategies), mirroring ``run_comparison``. Deterministic given the
    solvers; offline with ``ScriptedSolver``.
    """
    from .scoring import score_predictions

    rel = relevant_only_solver if relevant_only_solver is not None else baseline_solver
    desi = desi_solver if desi_solver is not None else baseline_solver
    preds = {
        "baseline": run_arm(baseline_solver, baseline_prompt, tasks),
        "relevant_only": run_arm(rel, relevant_only_prompt, tasks),
        "desi": run_arm(desi, desi_prompt, tasks),
    }
    metrics = {arm: score_predictions(p).to_dict() for arm, p in preds.items()}

    def _effects(key: str) -> dict[str, float]:
        b = float(metrics["baseline"][key])
        r = float(metrics["relevant_only"][key])
        d = float(metrics["desi"][key])
        # rounded from the same raw values so pruning + marking == total
        return {
            "pruning": round(r - b, 6),
            "marking": round(d - r, 6),
            "total": round(d - b, 6),
        }

    return {
        "arms": metrics,
        "effects": {
            "strict_group_correctness": _effects("strict_group_correctness"),
            "frame_accuracy": _effects("frame_accuracy"),
        },
        "predictions": preds,
    }


__all__ = [
    "CallableSolver",
    "ScriptedSolver",
    "Solver",
    "SolverConfigError",
    "baseline_prompt",
    "build_openai_solver",
    "desi_prompt",
    "parse_answer",
    "relevant_only_prompt",
    "run_arm",
    "run_comparison",
    "run_decomposition",
]
