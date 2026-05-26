"""HF answering layer tests (PERIPHERAL, offline, targeted).

Verify the evaluator, the model-port contract, and the DESi-core-alongside
wiring — all offline (no network, no token, no core mutation). Real model
answering is exercised by the runner with a token, not here.
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))
_ANS = _REPO / "benchmarks" / "hf_answering"
sys.path.insert(0, str(_ANS))

import schemas  # noqa: E402
import evaluator  # noqa: E402
import models  # noqa: E402
import answer_runner  # noqa: E402

ModelPort = models.ModelPort

QA = schemas.QAExample


def _examples():
    return [
        QA("e0", "is the sky blue?", "The sky appears blue.", True),
        QA("e1", "do pigs fly?", "Pigs cannot fly.", False),
        QA("e2", "is water wet?", "Water is wet.", True),
        QA("e3", "is fire cold?", "Fire is hot.", False),
    ]


def test_parse_bool() -> None:
    assert evaluator.parse_bool("yes") is True
    assert evaluator.parse_bool("No.") is False
    assert evaluator.parse_bool("  True ") is True
    assert evaluator.parse_bool("maybe") is None
    assert evaluator.parse_bool("") is None


def test_evaluate_confusion_and_accuracy() -> None:
    ex = _examples()
    # answers: e0 correct(True), e1 correct(False), e2 wrong(False -> FN), e3 unparsed
    answers = [
        schemas.ModelAnswer("e0", "yes", True),
        schemas.ModelAnswer("e1", "no", False),
        schemas.ModelAnswer("e2", "no", False),
        schemas.ModelAnswer("e3", "hmm", None),
    ]
    res = evaluator.evaluate(ex, answers, model="t", elapsed_s=0.0)
    assert res.n == 4 and res.answered == 3 and res.unparsed == 1
    c = res.confusion
    assert (c.tp, c.tn, c.fp, c.fn) == (1, 1, 0, 1)
    assert abs(res.accuracy - 2 / 3) < 1e-9


def test_constant_baseline_is_a_port_and_deterministic() -> None:
    p = models.ConstantBaselinePort(value=False)
    assert isinstance(p, ModelPort)
    assert p.answer("anything") == ("no", 0, 0)
    assert p.answer("other") == ("no", 0, 0)


def test_openrouter_port_raises_without_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    import pytest
    with pytest.raises(RuntimeError):
        models.OpenRouterPort(models.GRANITE)


def test_answer_all_one_pass_no_repair() -> None:
    ex = _examples()
    answers, elapsed = evaluator.answer_all(ex, models.ConstantBaselinePort(False))
    assert len(answers) == len(ex)
    assert all(a.parsed is False for a in answers)  # constant 'no'
    assert elapsed >= 0.0


def test_desi_core_metrics_alongside_holds_invariants() -> None:
    dc = answer_runner.desi_core_metrics(_examples())
    assert dc["replay_stable"] is True
    assert dc["gov_independent"] is True
    assert dc["critical_branch_preservation"] == 1.0
    assert dc["mutation_rejected"] == dc["mutation_attempts"] == 4  # 4 examples -> 4 (capped at 5)
    assert dc["core_identity_ok"] in (True, None)
