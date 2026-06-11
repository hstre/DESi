"""GSM-Symbolic G2 - two-arm solver harness tests.

Covers the deterministic plumbing (prompts, answer parsing, runner,
report wiring) and the honesty boundaries: the offline default solves
nothing, the scripted fake returns only what is injected, and the live
solver fails cleanly without a key. No network, no model.
"""
from __future__ import annotations

from desi.gsm_symbolic import (
    ScriptedSolver,
    SolverConfigError,
    all_correct_predictions,
    all_normalized_tasks,
    baseline_prompt,
    build_openai_solver,
    desi_prompt,
    noop_fragile_predictions,
    parse_answer,
    run_arm,
    run_comparison,
    score_predictions,
)
from desi.gsm_symbolic.__main__ import main
from desi.gsm_symbolic.report import VERDICT_IMPROVED, VERDICT_UNCHANGED


def _task(instance_id: str):
    for t in all_normalized_tasks():
        if t.instance_id == instance_id:
            return t
    raise AssertionError(instance_id)


# --- answer parsing ---------------------------------------------------
def test_parse_answer_takes_last_number_and_normalises() -> None:
    assert parse_answer("The answer is 89.", "integer") == "89"
    assert parse_answer("= 113", "integer") == "113"
    assert parse_answer("89.0", "integer") == "89"  # integral float -> int
    assert parse_answer("no number here", "integer") == ""
    assert parse_answer("", "integer") == ""


def test_parse_answer_handles_thousands_separators() -> None:
    # "1,234" must be one token, not ['1', '234'] with '234' as the answer
    assert parse_answer("The total is 1,234", "integer") == "1234"
    assert parse_answer("It comes to 12,345,678.", "integer") == "12345678"
    assert parse_answer("price: 1,234.50", "decimal") == "1234.50"
    # a list of numbers still yields the LAST one
    assert parse_answer("we have 1, 2 and 3", "integer") == "3"


# --- prompts: the structuring shows up in the DESi prompt --------------
def test_desi_prompt_drops_noop_clause_baseline_keeps_it() -> None:
    task = _task("gsm_p2_t01_i1")  # noop clause: "painted blue"
    base = baseline_prompt(task)
    desi = desi_prompt(task)
    assert "painted blue" in base                 # baseline sees everything
    assert "Ignore these irrelevant statements" in desi
    assert "painted blue" in desi.split("Ignore")[1]   # only as ignored
    assert "Known quantities:" in desi
    # No gold answer ever leaks into a prompt (operands yes, result no).
    assert task.answer == "89"
    assert "89" not in desi


# --- scripted solver: injected answers, nothing solved ----------------
def test_scripted_solver_returns_injected_then_default() -> None:
    s = ScriptedSolver({"a": "7"}, default="x")
    assert s.solve("anything", task_id="a") == "7"
    assert s.solve("anything", task_id="missing") == "x"


def test_run_arm_with_gold_script_scores_all_correct() -> None:
    gold = {t.task_id: t.answer for t in all_normalized_tasks()}
    preds = run_arm(ScriptedSolver(gold), baseline_prompt)
    assert score_predictions(preds).strict_group_correctness == 1.0


# --- full two-arm comparison via the runner ---------------------------
def test_run_comparison_improved_on_fragile_vs_robust() -> None:
    baseline = ScriptedSolver(noop_fragile_predictions())
    desi = ScriptedSolver(all_correct_predictions())
    report = run_comparison(baseline, desi)
    assert report.verdict == VERDICT_IMPROVED
    assert report.supports_thesis is True


def test_empty_solver_solves_nothing() -> None:
    report = run_comparison(ScriptedSolver())
    assert report.verdict == VERDICT_UNCHANGED
    assert report.baseline_metrics["frame_accuracy"] == 0.0
    assert report.desi_metrics["frame_accuracy"] == 0.0


def test_run_arm_is_deterministic() -> None:
    solver = ScriptedSolver(all_correct_predictions())
    assert run_arm(solver, desi_prompt) == run_arm(solver, desi_prompt)


# --- live solver fails cleanly without a key --------------------------
def test_live_solver_without_key_raises(monkeypatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    try:
        build_openai_solver(model="gpt-4o")
    except SolverConfigError as exc:
        assert "API key" in str(exc)
    else:
        raise AssertionError("expected SolverConfigError")


# --- CLI smoke (offline) ----------------------------------------------
def test_cli_default_offline(capsys) -> None:
    assert main([]) == 0
    out = capsys.readouterr().out
    assert "OFFLINE" in out
    assert "Verdict:" in out
    assert "NoOp-clause detection" in out


def test_cli_demo_populates_report(capsys) -> None:
    assert main(["--demo"]) == 0
    out = capsys.readouterr().out
    assert "OFFLINE DEMO" in out
    assert VERDICT_IMPROVED in out


def test_cli_live_without_key_reports_unavailable(monkeypatch, capsys) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert main(["--live"]) == 2
    assert "live mode unavailable" in capsys.readouterr().out
