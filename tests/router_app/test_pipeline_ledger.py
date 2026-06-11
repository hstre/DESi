"""Pipeline ↔ local Layer 9: escalation attempts become queryable evidence.

Drives the escalation loop fully offline (injected classifier + answerer), then
checks that every attempt is appended to the shared ledger and that
``escalation_evidence`` re-derives the confidence discrimination from those
logged runs — the read side of "the ledger is the calibration source".
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from desi_router.answerer import Answer  # noqa: E402
from desi_router.classifier import ClassificationResult  # noqa: E402
from desi_router.ledger import Ledger  # noqa: E402
from desi_router.pipeline import DESiPipeline, escalation_evidence  # noqa: E402
from desi_router.router import EpistemicRouter  # noqa: E402


class _FixedClassifier:
    def __init__(self, task_class: str, confidence: str = "high"):
        self.task_class, self.confidence = task_class, confidence

    def classify(self, query: str, context_hint=None) -> ClassificationResult:
        return ClassificationResult(
            task_class=self.task_class, confidence=self.confidence,
            raw_response="", classifier_model="fake", latency_ms=1, cost_usd=0.0,
        )


def _answer(text: str, confidence: str) -> Answer:
    return Answer(text=text, confidence=confidence, confidence_raw="(test)",
                  model="fake", input_tokens=1, output_tokens=1,
                  latency_ms=1, cost_usd=0.001)


def _router(task_class: str) -> EpistemicRouter:
    return EpistemicRouter(classifier=_FixedClassifier(task_class))


def test_attempts_are_logged_and_escalation_is_recorded(tmp_path):
    # memory_recall has escalate_on_low_conf=true in the table
    confidences = iter(["low", "high"])

    def answerer(model, context, query):
        return _answer("ans", next(confidences))

    pipe = DESiPipeline(router=_router("memory_recall"), answerer=answerer)
    led = Ledger(tmp_path / "l9.db", instance_id="pipe")
    res = pipe.run("how long did I wait?", haystack_builder=lambda s, k: "ctx",
                   ledger=led)

    assert res.escalated is True
    events = led.all(kind="pipeline_attempt")
    assert len(events) == 2                               # one row per attempt
    assert [e["payload"]["attempt_idx"] for e in events] == [0, 1]
    assert events[0]["payload"]["confidence"] == "low"
    assert events[0]["payload"]["escalate_bucket"] is True
    assert events[1]["payload"]["escalate_bucket"] is False
    assert led.verify_chain() is True                    # ledger stays intact
    led.close()


def test_no_ledger_means_no_events_but_run_still_works(tmp_path):
    def answerer(model, context, query):
        return _answer("ans", "high")

    pipe = DESiPipeline(router=_router("memory_recall"), answerer=answerer)
    res = pipe.run("q", haystack_builder=lambda s, k: "ctx")   # ledger=None
    assert res.final_answer is not None and res.escalated is False


def test_escalation_evidence_recovers_discrimination_from_ledger(tmp_path):
    # Scorer (eval-time gold proxy): low-confidence answers are wrong, high right.
    pairs = iter([("low", 0.0), ("high", 1.0),     # query 1: escalates, then fixed
                  ("high", 1.0),                     # query 2: confident & right
                  ("low", 0.0), ("high", 1.0)])      # query 3: escalates, then fixed
    state = {"score": None}

    def answerer(model, context, query):
        conf, score = next(pairs)
        state["score"] = score
        return _answer("ans", conf)

    def scorer(ans: Answer) -> float:
        return state["score"]

    pipe = DESiPipeline(router=_router("memory_recall"), answerer=answerer)
    led = Ledger(tmp_path / "l9.db", instance_id="pipe")
    for q in ("q1", "q2", "q3"):
        pipe.run(q, haystack_builder=lambda s, k: "ctx", ledger=led, scorer=scorer)

    ev = escalation_evidence(led)["memory_recall"]
    # 5 attempts total: 2 escalate-bucket (the two 'low'), 3 keep-bucket
    assert ev["n_total"] == 5 and ev["n_scored"] == 5
    assert ev["trigger_rate"] == round(2 / 5, 4)
    assert ev["p_correct_keep"] == 1.0          # every 'high' was correct
    assert ev["p_correct_escalate"] == 0.0      # every 'low' was wrong
    assert ev["separation"] == 1.0              # heuristic perfectly discriminates
    led.close()


def test_escalation_evidence_separation_none_without_scores(tmp_path):
    def answerer(model, context, query):
        return _answer("ans", "high")

    pipe = DESiPipeline(router=_router("memory_recall"), answerer=answerer)
    led = Ledger(tmp_path / "l9.db", instance_id="pipe")
    pipe.run("q", haystack_builder=lambda s, k: "ctx", ledger=led)   # no scorer
    ev = escalation_evidence(led)["memory_recall"]
    assert ev["n_total"] >= 1 and ev["n_scored"] == 0
    assert ev["separation"] is None             # trigger rate known, accuracy not
    led.close()
