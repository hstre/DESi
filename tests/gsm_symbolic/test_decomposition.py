"""Three-arm ablation: deconfounding pruning from marking.

The two-arm comparison attributes any difference to "the structuring" — but the
DESi prompt changes two things at once: it removes irrelevant content (shorter
context) and it names the removed clauses in an ignore-list (explicit marking).
``relevant_only_prompt`` applies only the removal, so the effect decomposes and
each test pins one piece of that decomposition.
"""
from __future__ import annotations

from desi.gsm_symbolic.normalizer import all_normalized_tasks
from desi.gsm_symbolic.predictions import (
    all_correct_predictions,
    noop_fragile_predictions,
)
from desi.gsm_symbolic.solver import (
    ScriptedSolver,
    desi_prompt,
    relevant_only_prompt,
    run_decomposition,
)
from desi.gsm_symbolic.state import extract_state


def _task(task_id: str):
    for t in all_normalized_tasks():
        if t.task_id == task_id:
            return t
    raise AssertionError(task_id)


# --- the middle prompt: removal without marking -------------------------

def test_relevant_only_prompt_has_no_ignore_block():
    task = _task("gsm_p2_t01_i1")  # has a noop clause ("painted blue")
    rel = relevant_only_prompt(task)
    assert "Ignore these irrelevant statements" not in rel
    assert "painted blue" not in rel              # silently removed, not named


def test_relevant_only_differs_from_desi_only_by_the_ignore_block():
    # the ablation is clean only if the middle arm is byte-identical to the
    # DESi arm minus the ignore-list lines — nothing else may vary
    task = _task("gsm_p2_t01_i1")
    desi_lines = desi_prompt(task).splitlines()
    rel_lines = relevant_only_prompt(task).splitlines()
    dropped = [c.text for c in extract_state(task).irrelevant_clauses()]
    assert dropped                                 # the task really has one
    extra = [ln for ln in desi_lines if ln not in rel_lines]
    assert "Ignore these irrelevant statements:" in extra
    assert all(
        ln == "Ignore these irrelevant statements:" or
        any(d in ln for d in dropped)
        for ln in extra
    )
    # and the middle arm adds nothing of its own
    assert [ln for ln in rel_lines if ln not in desi_lines] == []


def test_relevant_only_equals_desi_when_nothing_is_dropped():
    # on a task with no irrelevant clause the two prompts must coincide,
    # so any marking effect can only come from tasks that have one
    for t in all_normalized_tasks():
        if not extract_state(t).irrelevant_clauses():
            assert relevant_only_prompt(t) == desi_prompt(t)
            break
    else:
        raise AssertionError("no task without irrelevant clauses in fixtures")


# --- the decomposition arithmetic ---------------------------------------

def test_effects_decompose_additively():
    dec = run_decomposition(
        ScriptedSolver(noop_fragile_predictions()),
        ScriptedSolver(noop_fragile_predictions()),
        ScriptedSolver(all_correct_predictions()),
    )
    for key in ("strict_group_correctness", "frame_accuracy"):
        eff = dec["effects"][key]
        assert round(eff["pruning"] + eff["marking"], 6) == eff["total"]


def test_marking_effect_isolated_when_middle_arm_equals_baseline():
    # baseline and relevant_only identical -> pruning 0, everything is marking
    dec = run_decomposition(
        ScriptedSolver(noop_fragile_predictions()),
        ScriptedSolver(noop_fragile_predictions()),
        ScriptedSolver(all_correct_predictions()),
    )
    eff = dec["effects"]["strict_group_correctness"]
    assert eff["pruning"] == 0.0
    assert eff["marking"] == eff["total"] > 0


def test_pruning_effect_isolated_when_middle_arm_equals_desi():
    # relevant_only already fixes everything -> marking adds nothing
    dec = run_decomposition(
        ScriptedSolver(noop_fragile_predictions()),
        ScriptedSolver(all_correct_predictions()),
        ScriptedSolver(all_correct_predictions()),
    )
    eff = dec["effects"]["strict_group_correctness"]
    assert eff["marking"] == 0.0
    assert eff["pruning"] == eff["total"] > 0


def test_single_solver_defaults_apply_to_all_three_arms():
    dec = run_decomposition(ScriptedSolver(all_correct_predictions()))
    assert dec["effects"]["strict_group_correctness"] == {
        "pruning": 0.0, "marking": 0.0, "total": 0.0,
    }
    assert set(dec["arms"]) == {"baseline", "relevant_only", "desi"}


def test_decomposition_is_deterministic():
    args = (
        ScriptedSolver(noop_fragile_predictions()),
        ScriptedSolver(all_correct_predictions()),
        ScriptedSolver(all_correct_predictions()),
    )
    assert run_decomposition(*args) == run_decomposition(*args)


# --- CLI -----------------------------------------------------------------

def test_cli_decompose_demo(capsys) -> None:
    from desi.gsm_symbolic.__main__ import main

    assert main(["--demo", "--decompose"]) == 0
    out = capsys.readouterr().out
    assert "Three-arm ablation: pruning vs marking" in out
    assert "pruning (relevant_only − baseline)" in out
    assert "marking (desi − relevant_only)" in out
