"""Calibrated dissent-auditor tests (PERIPHERAL, offline, targeted)."""
from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))
_ANS = _REPO / "benchmarks" / "hf_answering"
sys.path.insert(0, str(_ANS))

import auditor_ports as ap  # noqa: E402
import solver_ports as sp  # noqa: E402


def test_parse_audit_strength_line() -> None:
    assert ap._parse_audit("gap noted.\nDISSENT_STRENGTH: STRONG").strength == "STRONG"
    assert ap._parse_audit("...\nDISSENT_STRENGTH: none").strength == "NONE"
    assert ap._parse_audit("DISSENT_STRENGTH: Medium").strength == "MEDIUM"


def test_parse_audit_unparseable_is_none_safe() -> None:
    # empty / runaway-reasoning output -> NONE (safe; never invents a strength)
    bad = ap._parse_audit("")
    assert bad.strength == "NONE" and bad.parse_ok is False
    bad2 = ap._parse_audit("long reasoning with no final line")
    assert bad2.strength == "NONE" and bad2.parse_ok is False


def test_audit_to_compact_carries_strength() -> None:
    a = ap.Audit(strength="MEDIUM", raw="evidence lacks an upper bound")
    s = a.to_compact()
    assert "strength=MEDIUM" in s and "upper bound" in s


def test_null_auditor_offline() -> None:
    a, pt, ct = ap.NullAuditor().audit("c", "e", "{}")
    assert a.strength == "NONE" and (pt, ct) == (0, 0)


def test_recheck_prompt_has_anti_collapse_rule() -> None:
    p = sp.build_recheck_prompt("claim", "evidence", "SUPPORTS", "WEAK", "strength=WEAK; gaps=...", task="verify")
    # NEI must NOT be automatic: the rule and the first verdict must be present
    assert "ONLY IF" in p and "KEEP your first verdict" in p and "SUPPORTS" in p


def test_constant_solver_recheck() -> None:
    s = sp.ConstantSolver("REFUTES")
    assert s.solve_recheck("c", "e", "REFUTES", "STRONG", "x", task="verify")[0] == "FINAL: REFUTES"
