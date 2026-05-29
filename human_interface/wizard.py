"""Jargon-free guided wizard. The user answers plain questions; never sees a DESi-internal term.

Non-interactive by default (deterministic + testable): `plan(goal, **answers)` returns the exact
one-line command to run for a chosen goal. An optional interactive `ask()` is provided for humans.
The wizard maps a plain GOAL to a concrete workflow — no knowledge of branch/drift/state/recovery.
"""
from __future__ import annotations

GOALS = {
    "check a paper or document": {
        "id": "paper",
        "needs": [("file", "Which file do you want checked? (path to a .md/.txt)")],
        "command": "python desi.py check {file}",
        "gives": "a ranked list of problems a reviewer would catch (inconsistent numbers, "
                 "repeated text, contradictions, over-strong claims).",
    },
    "compare options and record a decision": {
        "id": "decide",
        "needs": [("file", "Path to a small JSON file describing your options and what matters.")],
        "command": "python desi.py decide {file}",
        "gives": "a clear recommendation plus the explicit trade-off you're accepting.",
    },
    "see what needs my attention": {
        "id": "memory",
        "needs": [],
        "command": "python desi.py memory",
        "gives": "conflicts, open questions, and recent work — in plain language.",
    },
    "just show me what DESi can do": {
        "id": "home",
        "needs": [],
        "command": "python desi.py home",
        "gives": "a one-screen overview and your first step.",
    },
}


def list_goals() -> list:
    return list(GOALS)


def plan(goal: str, **answers) -> dict:
    if goal not in GOALS:
        # tolerant match on substring so the user can type loosely
        matches = [g for g in GOALS if goal.lower() in g.lower()]
        if len(matches) != 1:
            return {"ok": False, "error": f"pick one of: {list(GOALS)}"}
        goal = matches[0]
    spec = GOALS[goal]
    missing = [q for key, q in spec["needs"] if key not in answers]
    if missing:
        return {"ok": False, "need": missing, "goal": goal}
    cmd = spec["command"]
    for key, _ in spec["needs"]:
        cmd = cmd.replace("{" + key + "}", str(answers[key]))
    return {"ok": True, "goal": goal, "workflow": spec["id"], "command": cmd, "gives": spec["gives"]}


def ask() -> dict:  # pragma: no cover - interactive convenience only
    print("What do you want to do?")
    goals = list_goals()
    for i, g in enumerate(goals, 1):
        print(f"  {i}. {g}")
    choice = input("Pick a number: ").strip()
    goal = goals[int(choice) - 1]
    answers = {}
    for key, q in GOALS[goal]["needs"]:
        answers[key] = input(q + " ").strip()
    result = plan(goal, **answers)
    if result["ok"]:
        print(f"\nRun this:\n  {result['command']}\n\nYou'll get: {result['gives']}")
    return result
