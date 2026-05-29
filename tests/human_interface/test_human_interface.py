"""Tests for the DESi human-interface campaign (deterministic, offline)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO / "human_interface"))

import fitness  # noqa: E402
import glossary  # noqa: E402
import wizard  # noqa: E402
import wild_brother  # noqa: E402


# ---- Wild Brother + fitness governance ----------------------------------------------------
def test_wild_brother_covers_four_roles():
    by_role = wild_brother.critiques_by_role()
    assert set(by_role) == {"confused", "lazy", "heretical", "visionary"}
    assert all(len(v) >= 1 for v in by_role.values())
    assert len(wild_brother.IDEAS) >= 12


def test_fitness_is_replay_deterministic():
    a = fitness.run_fitness()
    b = fitness.run_fitness()
    assert a["replay_hash"] == b["replay_hash"]
    assert a["n"] == len(fitness.SCORES)


def test_absurd_ideas_are_rejected_not_built():
    by_id = {r["idea_id"]: r for r in fitness.run_fitness()["ledger"]}
    for absurd in ("desi_voice_assistant", "desi_mobile_app", "desi_llm_memory"):
        assert by_id[absurd]["decision"] == "REJECT"
        assert by_id[absurd]["reject_reason"]


def test_usable_frontdoors_build():
    by_id = {r["idea_id"]: r for r in fitness.run_fitness()["ledger"]}
    for win in ("home_landing", "one_click_workflows", "plain_cli", "run_on_my_file"):
        assert by_id[win]["decision"] == "BUILD"


def test_fitness_formula_matches_components():
    s = fitness.SCORES["home_landing"]
    expected = (sum(getattr(s, d) for d in fitness.POS) - sum(getattr(s, d) for d in fitness.NEG))
    assert fitness.fitness(s) == expected


# ---- glossary (no jargon at the surface) --------------------------------------------------
def test_glossary_translates_internal_terms():
    assert "drift" not in glossary.say("watch for drift in the topic").lower()
    assert glossary.explain("recoverability").startswith("whether you can")
    # untouched plain text is unchanged
    assert glossary.say("a plain sentence") == "a plain sentence"


# ---- wizard (plain questions -> exact command, no internal terms) -------------------------
def test_wizard_plans_each_goal():
    for g in wizard.list_goals():
        needs = wizard.GOALS[g]["needs"]
        answers = {k: "x.md" for k, _ in needs}
        res = wizard.plan(g, **answers)
        assert res["ok"] and res["command"].startswith("python desi.py")


def test_wizard_reports_missing_answer():
    res = wizard.plan("check a paper or document")  # missing 'file'
    assert not res["ok"] and "need" in res


def test_wizard_has_no_internal_jargon_in_questions():
    banned = ("epistemic", "drift", "concept gate", "recoverability", "replay", "branch ")
    for g, spec in wizard.GOALS.items():
        for _key, q in spec["needs"]:
            low = q.lower()
            assert not any(b in low for b in banned)


# ---- memory explorer (real state, plain language) -----------------------------------------
def test_memory_explorer_builds_and_renders():
    import memory_explorer as me
    state = me.build()
    assert set(state) == {"conflicts", "open_questions", "recent_changes"}
    out = me.render(state)
    assert "Memory Explorer" in out and "drift" not in out.lower()


# ---- the desi.py entry point (subprocess: no setup, runs as a user would) -----------------
def test_desi_home_runs():
    r = subprocess.run([sys.executable, "desi.py"], cwd=str(_REPO), capture_output=True, text=True)
    assert r.returncode == 0 and "WHAT IT DOES" in r.stdout


def test_desi_check_runs_on_paper():
    r = subprocess.run([sys.executable, "desi.py", "check", "README.md"],
                       cwd=str(_REPO), capture_output=True, text=True)
    assert r.returncode == 0 and "Paper audit" in r.stdout


def test_desi_decide_runs_on_example():
    ex = _REPO / "human_interface" / "examples" / "decision_example.json"
    r = subprocess.run([sys.executable, "desi.py", "decide", str(ex)],
                       cwd=str(_REPO), capture_output=True, text=True)
    assert r.returncode == 0 and "Recommended" in r.stdout


def test_desi_unknown_command_is_friendly():
    r = subprocess.run([sys.executable, "desi.py", "frobnicate"],
                       cwd=str(_REPO), capture_output=True, text=True)
    assert r.returncode == 2 and "unknown command" in r.stdout
