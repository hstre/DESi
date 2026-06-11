"""Extended turn protocol + repeated-run variance estimation (offline)."""
from __future__ import annotations

from pathlib import Path

import pytest

from desi.context_contamination import (
    ScriptedChat,
    load_cases,
    run_benchmark_repeated,
)
from desi.context_contamination.prompts import baseline_turns, hygiene_turns
from desi.context_contamination.runner import run_case

FIXTURES = Path(__file__).parent / "fixtures"
RAW = (FIXTURES / "advText_synthetic.txt").read_text(encoding="utf-8")


# --- extended protocol --------------------------------------------------------

def test_extended_protocol_has_more_turns_than_standard():
    assert len(baseline_turns(RAW, protocol="standard")) == 4
    assert len(baseline_turns(RAW, protocol="extended")) > 4
    # both arms keep the SAME turn count so the comparison stays matched
    assert len(baseline_turns(RAW, protocol="extended")) == len(
        hygiene_turns(RAW, protocol="extended")
    )


def test_arms_differ_only_in_the_ingestion_turn_under_extended():
    base = baseline_turns(RAW, protocol="extended")
    hyg = hygiene_turns(RAW, protocol="extended")
    # turn 0 (persona) and every follow-up (turn >= 2) are identical
    assert base[0] == hyg[0]
    assert base[2:] == hyg[2:]
    # only turn 1 (ingestion) differs
    assert base[1] != hyg[1]
    assert "BEGIN UPLOADED FILE" in base[1]
    assert "intentionally NOT provided" in hyg[1]


def test_unknown_protocol_raises():
    with pytest.raises(ValueError, match="unknown protocol"):
        baseline_turns(RAW, protocol="nope")


def test_run_case_threads_protocol():
    case = load_cases(FIXTURES, pattern="advText_*.txt")[0]
    chat = ScriptedChat([], default="ok")
    out = run_case(chat, case, "baseline", protocol="extended")
    assert out["protocol"] == "extended"
    assert out["metrics"]["turns"] == len(baseline_turns(RAW, protocol="extended"))


# --- repeated-run variance ----------------------------------------------------

def test_repeats_collapse_to_zero_variance_when_responses_are_fixed():
    # ScriptedChat is deterministic -> every repeat identical -> stdev 0
    cases = load_cases(FIXTURES, pattern="advText_*.txt")
    chat = ScriptedChat([], default="The file shows escalation; see the transcript.")
    out = run_benchmark_repeated(cases, chat, repeats=3)
    assert out["repeats"] == 3
    assert len(out["reports"]) == 3
    v = out["variance"]["baseline"]["advText_synthetic"]["register_drift"]
    assert v["stdev"] == 0.0
    assert v["mean"] == v["min"] == v["max"]
    assert v["values"] == [v["mean"]] * 3


def test_repeats_capture_spread_when_responses_vary():
    # a chat whose answers drift in the first repeat and clean up in the second
    # (standard protocol = 4 turns/case, 2 cases, 2 arms -> 16 calls per repeat)
    cases = load_cases(FIXTURES, pattern="advText_*.txt")
    drift = ("I'm so sorry you went through this. You are not alone and your "
             "feelings are valid. I'm here to listen; it takes courage.")
    clean = "The transcript shows escalation. The evidence is observable in the file."
    # standard protocol = 4 turns/case, len(cases) cases, 2 arms per repeat
    calls_per_repeat = 4 * len(cases) * 2

    state = {"n": 0}

    def varying_chat(messages):
        reply = drift if state["n"] < calls_per_repeat else clean
        state["n"] += 1
        return reply

    out = run_benchmark_repeated(cases, varying_chat, repeats=2)
    v = out["variance"]["baseline"]["advText_synthetic"]["register_drift"]
    assert v["max"] > v["min"]          # the two repeats really differ
    assert v["stdev"] > 0.0
    assert len(v["values"]) == 2


def test_repeats_one_is_single_run_with_zero_stdev():
    cases = load_cases(FIXTURES, pattern="advText_*.txt")
    chat = ScriptedChat([], default="neutral analytical reply about the file")
    out = run_benchmark_repeated(cases, chat, repeats=1)
    assert out["repeats"] == 1 and len(out["reports"]) == 1
    v = out["variance"]["desi_hygiene"]["advText_synthetic"]["attribution_failures"]
    assert v["stdev"] == 0.0 and len(v["values"]) == 1
