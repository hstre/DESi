"""Density levels ("k" for this task family), the sweep, and ledger recording."""
from __future__ import annotations

from pathlib import Path

import pytest

from desi.context_contamination import (
    DENSITY_LEVELS,
    ScriptedChat,
    build_hygiene_state,
    load_cases,
    run_density_sweep,
)
from desi.context_contamination.prompts import hygiene_turns
from desi.context_contamination.runner import run_case

FIXTURES = Path(__file__).parent / "fixtures"
RAW = (FIXTURES / "advText_synthetic.txt").read_text(encoding="utf-8")


# --- density levels -------------------------------------------------------------

def test_density_levels_are_a_closed_ordered_set():
    assert DENSITY_LEVELS == (1, 3, 5, 8)
    with pytest.raises(ValueError, match="unknown density"):
        build_hygiene_state(RAW, density=2)


def test_density_1_is_a_bare_contamination_label():
    s = build_hygiene_state(RAW, density=1)
    assert "source_register" in s and s["source_register"]      # the label
    assert "source_claims" not in s
    assert "hard_constraints" not in s
    assert "risk_markers" not in s and "forbidden_transfers" not in s
    assert s["audit"]["density"] == 1 and s["audit"]["state_claims"] == 0


def test_density_3_adds_claims_and_constraints_only():
    s = build_hygiene_state(RAW, density=3)
    assert s["source_claims"] and len(s["source_claims"]) <= 6
    assert "Do not adopt the source ontology." in s["hard_constraints"]
    assert "risk_markers" not in s and "forbidden_transfers" not in s


def test_density_5_is_the_full_default_state():
    default = build_hygiene_state(RAW)
    explicit = build_hygiene_state(RAW, density=5)
    assert default == explicit
    for key in ("source_claims", "hard_constraints", "risk_markers",
                "forbidden_transfers", "framework_terms_present"):
        assert key in default
    assert default["audit"]["density"] == 5


def test_density_8_is_richer_but_still_capped_and_quoted():
    s5 = build_hygiene_state(RAW, density=5)
    s8 = build_hygiene_state(RAW, density=8)
    assert len(s8["source_claims"]) >= len(s5["source_claims"])
    for claim in s8["source_claims"]:
        assert claim.startswith('Quoted from uploaded_file: "')
        assert len(claim) <= 350                       # 300-char cap + quoting
    # the raw-text invariant holds at every density
    for k in DENSITY_LEVELS:
        joined = "\n".join(hygiene_turns(RAW, density=k))
        assert RAW.strip() not in joined
        assert "BEGIN UPLOADED FILE" not in joined


def test_density_threads_through_run_case():
    case = load_cases(FIXTURES, pattern="advText_*.txt")[0]
    out = run_case(ScriptedChat([], default="ok"), case, "desi_hygiene", density=3)
    assert out["density"] == 3


# --- the sweep: shared baseline, hygiene per level --------------------------------

def test_sweep_shares_one_baseline_per_repeat():
    cases = load_cases(FIXTURES, pattern="advText_*.txt")
    chat = ScriptedChat([], default="The file shows escalation in the transcript.")
    out = run_density_sweep(cases, chat, repeats=2)
    assert out["densities"] == list(DENSITY_LEVELS)
    # cost model: (1 baseline + 4 hygiene) case-runs x 4 turns x 1 case x 2 repeats
    assert len(chat.calls) == (1 + len(DENSITY_LEVELS)) * 4 * len(cases) * 2
    # every density was compared against the SAME baseline metrics
    for k in DENSITY_LEVELS:
        comp = out["sweeps"][k][0]["comparisons"][0]
        base = out["baseline_runs"][0]["advText_synthetic"]["metrics"]
        assert comp["baseline"]["framing_leakage"] == base["framing_leakage"]


def test_sweep_rejects_unknown_density():
    cases = load_cases(FIXTURES, pattern="advText_*.txt")
    with pytest.raises(ValueError, match="unknown density"):
        run_density_sweep(cases, ScriptedChat([], default="x"), densities=(1, 4))


def test_sweep_profile_has_variance_per_density():
    cases = load_cases(FIXTURES, pattern="advText_*.txt")
    chat = ScriptedChat([], default="neutral reply about the file")
    out = run_density_sweep(cases, chat, densities=(1, 5), repeats=2)
    cell = out["by_density"][5]["advText_synthetic"]["register_drift"]
    assert set(cell) == {"mean", "stdev", "min", "max", "values"}
    assert len(cell["values"]) == 2


# --- ledger recording (local Layer 9 / Reviewer Port visibility) -------------------

class _FakeLedger:
    def __init__(self):
        self.events = []

    def record(self, kind, payload, **kw):
        self.events.append((kind, payload))
        return {"seq": len(self.events)}


def test_run_case_records_one_slim_ledger_event():
    case = load_cases(FIXTURES, pattern="advText_*.txt")[0]
    led = _FakeLedger()
    out = run_case(ScriptedChat([], default="ok"), case, "desi_hygiene",
                   persona="neutral", ledger=led)
    assert len(led.events) == 1
    kind, payload = led.events[0]
    assert kind == "context_contamination"
    assert payload["arm"] == "desi_hygiene" and payload["case_id"] == "advText_synthetic"
    assert payload["density"] == 5 and payload["persona"] == "neutral"
    # slim: metrics + transcript hash, never the transcripts themselves
    assert "responses" not in payload and len(payload["responses_sha256"]) == 64
    assert payload["framing_leakage"] == out["metrics"]["framing_leakage"]


def test_real_layer9_ledger_accepts_benchmark_events(tmp_path):
    # integration with the actual desi_router ledger: append, chain intact
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from desi_router.ledger import Ledger

    cases = load_cases(FIXTURES, pattern="advText_*.txt")
    led = Ledger(tmp_path / "l9.db", instance_id="cc-test")
    run_density_sweep(cases, ScriptedChat([], default="ok"),
                      densities=(1, 5), ledger=led)
    events = led.all(kind="context_contamination")
    assert len(events) == 3                       # 1 baseline + 2 hygiene runs
    assert {e["payload"]["arm"] for e in events} == {"baseline", "desi_hygiene"}
    assert {e["payload"]["density"] for e in events if
            e["payload"]["arm"] == "desi_hygiene"} == {1, 5}
    assert led.verify_chain() is True
    led.close()
