"""Tests for step 1 (measured routing table -> policy) and step 2 (tool catalogue)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from desi import engine  # noqa: E402
from desi.policy import ANY, Constraints, classify, decide  # noqa: E402
from desi.providers import load_config  # noqa: E402
from desi.routing_table import measured_score  # noqa: E402
from desi.tool_registry import default_registry  # noqa: E402
from desi.tools import convert_units, make_keyword_search, solve_date  # noqa: E402

CONFIG = REPO_ROOT / "desi" / "config.example.json"


def _reg():
    return load_config(CONFIG)


# ---- step 1: measured routing table feeds the policy ----

def test_table_has_measured_scores():
    assert measured_score("code_audit", "google/gemini-2.5-flash-lite") == 0.967
    assert measured_score("memory_recall", "anthropic/claude-haiku-4.5") == 0.68
    assert measured_score("code_audit", "does/not-exist") is None


def test_decision_uses_measured_score_not_config_hint():
    # gemini flash-lite config hint says 0.967 too, but source must read 'measured'
    d = decide("code_audit", Constraints(privacy=ANY, accuracy_target=0.95),
               _reg(), default_registry())
    assert d.extras["model_id"] == "google/gemini-2.5-flash-lite"
    assert d.extras["score_source"] == "measured"
    assert d.expected_score == 0.967


def test_local_model_not_in_table_falls_back_to_config_hint():
    # llama3.1:8b (local id) is not the measured table id -> config hint used
    d = decide("code_audit", Constraints(privacy="local_only", accuracy_target=0.8),
               _reg(), default_registry())
    assert d.locality == "local"
    assert d.extras["score_source"] == "config_hint"


# ---- step 2: date tool ----

def test_date_tool():
    assert solve_date("days between 2026-01-01 and 2026-06-09") == 159
    assert solve_date("90 days after 2026-03-01") == "2026-05-30"
    assert solve_date("10 days before 2026-01-05") == "2025-12-26"


# ---- step 2: units tool ----

def test_units_tool():
    assert convert_units("convert 5 km to miles") == 3.1069
    assert convert_units("100 celsius to fahrenheit") == 212
    assert convert_units("10 kg to lb") == 22.0462
    assert convert_units("1 mile in km") == 1.6093


# ---- step 2: retrieval tool (over a temp corpus) ----

def test_retrieval_tool(tmp_path):
    (tmp_path / "a.md").write_text("DESi routes to deterministic tools when possible.")
    (tmp_path / "b.txt").write_text("Unrelated note about gardening.")
    search = make_keyword_search(tmp_path)
    out = search("deterministic tools")
    assert "a.md" in out and "gardening" not in out


# ---- classification routes the new task classes ----

def test_classify_new_tasks():
    assert classify("how many days between 2026-01-01 and 2026-06-09?") == "date_math"
    assert classify("convert 5 km to miles") == "unit_conversion"


# ---- engine: new tool paths run offline end-to-end ----

def test_engine_date_and_units_offline():
    d = engine.run("how many days between 2026-01-01 and 2026-06-09?",
                   registry=_reg(), tools=default_registry())
    assert d["task_class"] == "date_math" and d["answer"] == "159" and d["answer_source"] == "tool"
    u = engine.run("convert 5 km to miles", registry=_reg(), tools=default_registry())
    assert u["task_class"] == "unit_conversion" and u["answer"] == "3.1069"


def test_engine_retrieval_with_corpus(tmp_path):
    (tmp_path / "doc.md").write_text("The DESi reviewer port shows the audit hash.")
    reg = _reg()
    tools = default_registry(corpus_dir=tmp_path)
    out = engine.run("audit hash reviewer port", registry=reg, tools=tools,
                     task_class="retrieval")
    assert out["decision"]["kind"] == "tool"
    assert "doc.md" in out["answer"]
