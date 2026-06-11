"""Tests for the local DESi router app (v0.1) — deterministic parts only.

Covers config loading, task classification, the tool/local/API policy with the
privacy axis, the engine's offline tool path (runs live, no model), and audit
determinism. The model-execution edge is not exercised here (no network/keys);
it is isolated behind the adapter by design.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from desi_router import engine  # noqa: E402
from desi_router.policy import (  # noqa: E402
    ANY,
    LOCAL_ONLY,
    PREFER_LOCAL,
    Constraints,
    classify,
    decide,
)
from desi_router.providers import load_config  # noqa: E402
from desi_router.tool_registry import default_registry  # noqa: E402

CONFIG = REPO_ROOT / "desi_router" / "config.example.json"


def _reg():
    return load_config(CONFIG)


# ---- config ----

def test_config_loads_local_and_api():
    reg = _reg()
    names = {p.name for p in reg.providers}
    assert names == {"ollama-local", "openrouter-api"}
    locs = {m.locality for _, m in reg.all_models()}
    assert locs == {"local", "api"}


# ---- classification (deterministic heuristic) ----

def test_classify():
    assert classify("what is (9*4)-6 ?") == "math_arithmetic"
    assert classify("find the bug in this function") == "code_audit"
    assert classify("what did you say earlier about my visa?") == "memory_recall"
    assert classify("evaluate the evidence for this study claim") == "scientific_claim"
    assert classify("hello there, who are you") == "general"


def test_classify_hyphen_ranges_are_not_arithmetic():
    # a bare hyphen between digits is a range, not subtraction
    assert classify("What happened in 2020-2021") != "math_arithmetic"
    assert classify("book rooms 5-10 for the visit") != "math_arithmetic"
    # real subtraction still classifies: spaced operator or an explicit cue
    assert classify("what is 12 - 4") == "math_arithmetic"
    assert classify("what is 12-4") == "math_arithmetic"
    assert classify("calculate 2026-1989") == "math_arithmetic"


# ---- policy: tool wins; privacy & accuracy steer model choice ----

def test_math_routes_to_tool():
    d = decide("math_arithmetic", Constraints(), _reg(), default_registry())
    assert d.kind == "tool" and d.target == "calculator"
    assert d.locality == "tool" and d.expected_cost_usd == 0.0


def test_local_only_never_picks_api():
    d = decide("code_audit", Constraints(privacy=LOCAL_ONLY), _reg(), default_registry())
    assert d.kind == "model" and d.locality == "local"


def test_prefer_local_keeps_it_local_when_adequate():
    d = decide("code_audit", Constraints(privacy=PREFER_LOCAL, accuracy_target=0.8),
               _reg(), default_registry())
    assert d.locality == "local"          # llama3.1:8b @0.83 clears 0.8 locally


def test_high_accuracy_any_picks_cheapest_qualifying_model():
    d = decide("code_audit", Constraints(privacy=ANY, accuracy_target=0.95),
               _reg(), default_registry())
    assert d.kind == "model"
    assert d.extras["model_id"] == "google/gemini-2.5-flash-lite"   # 0.967 @ $0.00013
    assert d.below_target is False


# ---- engine: tool path runs live and offline ----

def test_engine_tool_path_computes_offline():
    out = engine.run("please compute (9*4)-6 for me",
                     registry=_reg(), tools=default_registry())
    assert out["task_class"] == "math_arithmetic"
    assert out["answer"] == "30"
    assert out["answer_source"] == "tool"
    assert len(out["audit"]["decision_hash"]) == 64


def test_engine_model_decision_without_calling(monkeypatch=None):
    out = engine.run("refactor this function to remove the bug",
                     registry=_reg(), tools=default_registry(),
                     constraints=Constraints(privacy=LOCAL_ONLY),
                     execute_model=False)
    assert out["decision"]["kind"] == "model"
    assert out["decision"]["locality"] == "local"
    assert out["answer"] is None and out["answer_source"] == "none"


# ---- audit determinism / replay ----

def test_audit_decision_hash_is_replay_stable():
    a = engine.run("what is 2+2*3", registry=_reg(), tools=default_registry())
    b = engine.run("what is 2+2*3", registry=_reg(), tools=default_registry())
    assert a["audit"]["decision_hash"] == b["audit"]["decision_hash"]


# ---- epistemic router: decision reasons are per-call, never cached in the table ----

def test_route_reason_is_not_stale_across_calls():
    from desi_router.router import EpistemicRouter, RouteRequest

    r = EpistemicRouter()
    d1 = r.route(RouteRequest(task_class="memory_recall", accuracy_target=0.5))
    assert "Hand-curated default" in d1.reason

    # same cell may win again via the cost-constrained Pareto branch — its
    # reason must describe THIS call, not the earlier default-rule pick
    d2 = r.route(RouteRequest(task_class="memory_recall",
                              cost_budget_usd=0.0005, accuracy_target=0.5))
    assert "Hand-curated default" not in d2.reason

    # and the shared table must not be polluted with derived keys
    for cells in (c["cells"] for c in r.table["tasks"].values()):
        assert all("_reason_hint" not in cell for cell in cells)
