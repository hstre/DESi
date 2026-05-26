"""Dissent ('wild brother') layer tests (PERIPHERAL, offline, targeted)."""
from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))
_ANS = _REPO / "benchmarks" / "hf_answering"
sys.path.insert(0, str(_ANS))

import challenger_ports as cp  # noqa: E402
import solver_ports as sp  # noqa: E402


def test_parse_dissent_final_line() -> None:
    ok = cp._parse_dissent("Counter-hypotheses: ...\nNEI_PLAUSIBLE: YES")
    assert ok.parse_ok is True and ok.nei_plausible is True
    no = cp._parse_dissent("reasoning...\nNEI_PLAUSIBLE: NO")
    assert no.parse_ok is True and no.nei_plausible is False
    bad = cp._parse_dissent("no final line here")
    assert bad.parse_ok is False and bad.nei_plausible is False  # never invented True


def test_dissent_to_compact_carries_flag_and_text() -> None:
    d = cp.Dissent(nei_plausible=True, raw="missing evidence about counts")
    s = d.to_compact()
    assert "nei_plausible=True" in s and "missing evidence" in s


def test_null_challenger_offline() -> None:
    diss, pt, ct = cp.NullChallenger().challenge("claim", "evidence", "{}")
    assert diss.nei_plausible is False and (pt, ct) == (0, 0)


def test_dissent_prompt_includes_dissent_block() -> None:
    p = sp.build_dissent_prompt("{struct}", "{dissent}", "the claim", task="verify")
    assert "DISSENT:" in p and "STRUCTURE:" in p and "NOT_ENOUGH_INFO" in p


def test_constant_solver_solve_with_dissent() -> None:
    import dissent_governance as dg
    s = sp.ConstantSolver("NOT_ENOUGH_INFO")
    payload = dg.GOVERNED_SENTINEL + " weight=WEAK; governed dissent"
    assert s.solve_with_dissent("{}", payload, "c", task="verify")[0] == "FINAL: NOT_ENOUGH_INFO"
