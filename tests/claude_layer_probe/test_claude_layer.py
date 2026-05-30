"""Tests for the DESi Claude-Layer Probe — deterministic, offline."""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "claude_layer_probe"))
sys.path.insert(0, str(_REPO / "claude_compression"))
sys.path.insert(0, str(_REPO / "src"))

import ab_test_design as ab  # noqa: E402
import inventory as inv  # noqa: E402
import mcp_layer as layer  # noqa: E402


# ---- Inventory layer ------------------------------------------------------------------

def test_inventory_has_expected_state_types():
    summary = inv.collect()
    types = set(summary["per_state_type"])
    assert types >= {"wiki_compact_state_v1", "wiki_dual_layer_anchors",
                     "wiki_dual_layer_v2", "driftbench_state_summary"}


def test_inventory_n_matches_known_artifact_sizes():
    summary = inv.collect()
    n = {k: v["n"] for k, v in summary["per_state_type"].items()}
    assert n["wiki_compact_state_v1"] == 10
    assert n["wiki_dual_layer_anchors"] == 10
    assert n["wiki_dual_layer_v2"] == 10
    assert n["driftbench_state_summary"] == 1525
    assert summary["overall"]["n"] == 1555


def test_inventory_correlation_raw_savings_is_strong():
    """The central testable claim: state grows much slower than input. corr(raw, savings) > 0.95."""
    summary = inv.collect()
    assert summary["overall"]["corr_raw_vs_savings"] > 0.95


def test_inventory_long_tail_bins_documented_as_empty():
    """Honest gap: <1k and >=50k bins MUST be reported as empty (not silently averaged away)."""
    bins = {b["bin"]: b for b in inv.collect()["overall_bins"]}
    assert bins["<1k"]["n"] == 0 and "note" in bins["<1k"]
    assert bins[">=50k"]["n"] == 0 and "note" in bins[">=50k"]


# ---- MCP-layer five tool functions ----------------------------------------------------

def test_observe_step_appends_and_advances_chain():
    layer._reset_run("r1")
    a = layer.observe_step("r1", input="goal: build X", model_output="ok",
                           metadata={"kind": "decision", "body": "build X"})
    b = layer.observe_step("r1", input="need: constraint Y", model_output="noted",
                           metadata={"kind": "constraint", "body": "Y must hold"})
    assert a["chain_head"] != b["chain_head"]
    s = layer.current_state("r1")
    assert any(d["what"] == "build X" for d in s["decisions"])
    assert any(c["what"] == "Y must hold" for c in s["constraints"])


def test_state_categories_are_brief_compliant():
    layer._reset_run("r2")
    layer.observe_step("r2", "i", "o", metadata={"kind": "claim", "body": "c", "evidence": "likely"})
    s = layer.current_state("r2")
    assert set(s) - {"run_id"} == {"claims", "constraints", "decisions", "conflicts", "open_questions"}


def test_retrieve_cold_anchor_returns_exact_input():
    layer._reset_run("r3")
    r = layer.observe_step("r3", input="EXACT INPUT SPAN", model_output="ok", metadata={})
    a = layer.retrieve_cold_anchor("r3", r["anchor_id"])
    assert a["found"] and a["input"] == "EXACT INPUT SPAN"


def test_retrieve_cold_anchor_handles_misses():
    layer._reset_run("r4")
    miss = layer.retrieve_cold_anchor("r4", "a-9999-deadbeef")
    assert not miss["found"]


def test_replay_verify_passes_on_genuine_chain():
    layer._reset_run("r5")
    for i in range(5):
        layer.observe_step("r5", f"i{i}", f"o{i}", metadata={})
    v = layer.replay_verify("r5")
    assert v["verified"] and v["recomputed"] == v["stored"]
    assert v["n_steps"] == 5


def test_replay_verify_is_unforgeable():
    """If anyone tampers with a step's input after the fact, replay must FAIL — the chain head
    was computed over the original input."""
    layer._reset_run("r6")
    layer.observe_step("r6", "original", "o", metadata={})
    layer.observe_step("r6", "second", "o", metadata={})
    rec = layer._RUNS["r6"]
    rec.steps[0].input = "tampered"
    v = layer.replay_verify("r6")
    assert v["verified"] is False


def test_export_rehydration_prompt_has_state_block_no_chat_history():
    layer._reset_run("r7")
    layer.observe_step("r7", "i", "o", metadata={"kind": "constraint", "body": "Y must hold"})
    p = layer.export_rehydration_prompt("r7")
    assert "system" in p and "state_block" in p and p["token_size"] > 0
    # the state block must not contain raw chat-history markers
    low = p["state_block"].lower()
    for forbidden in ("user said", "assistant said", "the chat", "we discussed earlier"):
        assert forbidden not in low


# ---- A/B test design --------------------------------------------------------------------

def test_ab_design_emits_both_variants_for_each_fixture():
    _FX = _REPO / "state_discovery" / "fixtures_v3"
    fid = "research_architecture"
    chat = json.loads((_FX / f"chat_{fid}.json").read_text())["chat"]
    gt = json.loads((_FX / f"groundtruth_{fid}.json").read_text())["expected"]
    out = ab.design_one_pair(fid, chat, gt)
    assert out["variant_A"]["variant"] == "A_full_context"
    assert out["variant_B"]["variant"] == "B_desi_state"
    assert out["token_size_A"] > 0 and out["token_size_B"] > 0
    assert out["replay_verified"] is True


def test_ab_design_marks_workability_as_untested():
    """Brief mandate: if no second Claude session is possible, status must be UNTESTED."""
    _FX = _REPO / "state_discovery" / "fixtures_v3"
    fid = "research_architecture"
    chat = json.loads((_FX / f"chat_{fid}.json").read_text())["chat"]
    gt = json.loads((_FX / f"groundtruth_{fid}.json").read_text())["expected"]
    out = ab.design_one_pair(fid, chat, gt)
    assert out["workability_status"].startswith("UNTESTED_in_this_env")
