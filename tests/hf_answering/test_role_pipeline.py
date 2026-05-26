"""Role-pipeline tests (PERIPHERAL, offline, targeted)."""
from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))
_ANS = _REPO / "benchmarks" / "hf_answering"
sys.path.insert(0, str(_ANS))

import extractor_ports as ep  # noqa: E402
import solver_ports as sp  # noqa: E402
import role_pipeline as rp  # noqa: E402


def test_parse_verdict_final_line() -> None:
    assert sp.parse_verdict("reasoning... FINAL: YES", sp.BOOL_SYNS) == "YES"
    assert sp.parse_verdict("I think... FINAL: NO", sp.BOOL_SYNS) == "NO"
    assert sp.parse_verdict("...\nFINAL: NOT_ENOUGH_INFO", sp.VERIFY_SYNS) == "NOT_ENOUGH_INFO"
    assert sp.parse_verdict("the evidence refutes it", sp.VERIFY_SYNS) == "REFUTES"
    assert sp.parse_verdict("banana", sp.VERIFY_SYNS) is None


def test_parse_verdict_prefers_final_over_earlier_mentions() -> None:
    # reasoning mentions 'support' then concludes 'REFUTES' on the FINAL line
    txt = "At first this seems to support the claim, but actually FINAL: REFUTES"
    assert sp.parse_verdict(txt, sp.VERIFY_SYNS) == "REFUTES"


def test_projection_parse() -> None:
    ok = ep._parse_projection('{"claims":["a"],"evidence":["e"],"polarity":"support","uncertainty":"low"}')
    assert ok.parse_ok is True and ok.claims == ["a"] and ok.polarity == "support"
    bad = ep._parse_projection("not json at all")
    assert bad.parse_ok is False and bad.raw == "not json at all"


def test_score_uniform() -> None:
    items = [
        {"id": "a", "gold": "YES"}, {"id": "b", "gold": "NO"},
        {"id": "c", "gold": "YES"}, {"id": "d", "gold": "NO"},
    ]
    parsed = {"a": "YES", "b": "NO", "c": "NO", "d": None}  # a,b correct; c wrong; d parsefail
    ev = rp._score(items, parsed, ("YES", "NO"), ex_tokens=(0, 0), ex_price=(0, 0),
                   sv_tokens=(0, 0), sv_price=(0, 0))
    assert ev["n"] == 4 and ev["answered"] == 3 and ev["parse_failures"] == 1
    assert abs(ev["accuracy"] - 2 / 3) < 1e-9
    assert ev["confusion"]["YES"]["NO"] == 1


def test_desi_core_metrics_alongside() -> None:
    items = [{"id": f"i{i}", "primary": f"text {i}"} for i in range(6)]
    dc = rp.desi_core_metrics(items)
    assert dc["replay_stable"] is True and dc["gov_independent"] is True
    assert dc["critical_branch_preservation"] == 1.0 and dc["hard_pruning"] == 0
    assert dc["mutation_rejected"] == dc["mutation_attempts"] == 5
    assert dc["core_identity_ok"] in (True, None)


def test_constant_solver_and_null_extractor_offline() -> None:
    proj, pt, ct = ep.NullExtractor().extract("hello")
    assert proj.raw == "hello" and (pt, ct) == (0, 0)
    s = sp.ConstantSolver("NO")
    assert s.solve_direct("q", "ctx", task="boolq")[0] == "FINAL: NO"
