"""SciFact/FEVER-style evaluator tests (PERIPHERAL, offline, targeted)."""
from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))
_ANS = _REPO / "benchmarks" / "hf_answering"
sys.path.insert(0, str(_ANS))

import scifact_evaluator as se  # noqa: E402
import scifact_runner as sr  # noqa: E402

VE = se.VerifyExample
VA = se.VerifyAnswer


def test_parse_label() -> None:
    assert se.parse_label("SUPPORTS") == "SUPPORTS"
    assert se.parse_label("The evidence refutes the claim.") == "REFUTES"
    assert se.parse_label("not enough info") == "NOT_ENOUGH_INFO"
    assert se.parse_label("NEUTRAL") == "NOT_ENOUGH_INFO"
    assert se.parse_label("banana") is None
    assert se.parse_label("") is None


def test_normalize_gold() -> None:
    assert se.normalize_gold("SUPPORTS") == "SUPPORTS"
    assert se.normalize_gold("NOT ENOUGH INFO") == "NOT_ENOUGH_INFO"
    assert se.normalize_gold("contradiction") == "REFUTES"
    assert se.normalize_gold("???") is None


def test_evaluate_3class_confusion() -> None:
    ex = [
        VE("a", "c1", "e1", "SUPPORTS"),
        VE("b", "c2", "e2", "REFUTES"),
        VE("c", "c3", "e3", "NOT_ENOUGH_INFO"),
        VE("d", "c4", "e4", "SUPPORTS"),
    ]
    ans = [
        VA("a", "SUPPORTS", "SUPPORTS"),         # correct
        VA("b", "REFUTES", "REFUTES"),           # correct
        VA("c", "SUPPORTS", "SUPPORTS"),         # wrong (gold NEI)
        VA("d", "huh", None),                    # parse failure
    ]
    r = se.evaluate(ex, ans)
    assert r["n"] == 4 and r["answered"] == 3 and r["parse_failures"] == 1
    assert abs(r["accuracy"] - 2 / 3) < 1e-9
    assert r["confusion"]["NOT_ENOUGH_INFO"]["SUPPORTS"] == 1
    assert r["gold_distribution"]["SUPPORTS"] == 2
    assert r["pred_distribution"]["SUPPORTS"] == 2


def test_desi_core_metrics_alongside() -> None:
    ex = [VE(f"x{i}", f"claim {i}", "evidence", "SUPPORTS") for i in range(6)]
    dc = sr.desi_core_metrics(ex)
    assert dc["replay_stable"] is True
    assert dc["gov_independent"] is True
    assert dc["critical_branch_preservation"] == 1.0
    assert dc["hard_pruning"] == 0
    assert dc["mutation_rejected"] == dc["mutation_attempts"] == 5
    assert dc["core_identity_ok"] in (True, None)
