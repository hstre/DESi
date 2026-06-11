"""DESi end-to-end pipeline: classify -> route -> answer -> (escalate).

This is v0.3 — adds confidence-based escalation. If the answerer derives
'low' confidence (heuristic hedging/refusal markers; see desi_router.answerer),
the pipeline retries with the next Pareto point.
Each attempt is logged for audit.

Closing the loop (local Layer 9): when a ``ledger`` is supplied, every attempt
is appended as a ``pipeline_attempt`` event — task, model, heuristic confidence,
whether it escalated, and (when the caller supplies an eval-time ``scorer``) the
realized score. ``escalation_evidence`` reads those events back and computes the
confidence discrimination directly from logged runs, so the escalation_rules in
routing_table.json can be re-fitted from accumulated evidence instead of a
one-off calibration. Without a scorer the ledger still records the decision
trail; realized accuracy simply needs a downstream correctness signal to attach.

Usage:
    from desi_router.pipeline import DESiPipeline

    p = DESiPipeline()
    result = p.run(
        query="How long did I wait for the asylum decision?",
        haystack_builder=lambda strategy, k: build_context(items, strategy, k),
    )
    # result.final_answer.text, result.attempts, result.total_cost_usd

The haystack_builder is supplied by the caller because the retrieval logic
depends on the task (sessions for memory_recall, abstracts for scientific_claim,
files for code_audit).
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable

from desi_router.router import EpistemicRouter, Decision
from desi_router.answerer import Answer, answer as call_answerer

# Confidence buckets that trigger escalation — kept identical to the default
# escalate_on so logged evidence is read back with the same split.
ESCALATE_BUCKETS = ("low", "unknown")

Answerer = Callable[[str, str, str], Answer]
Scorer = Callable[[Answer], float]


@dataclass
class Attempt:
    decision: Decision
    answer: Answer


@dataclass
class PipelineResult:
    query: str
    task_class: str
    classifier_confidence: str
    attempts: list[Attempt] = field(default_factory=list)
    final_answer: Answer | None = None
    total_cost_usd: float = 0.0
    total_latency_ms: int = 0
    escalated: bool = False
    escalation_reason: str = ""
    refused: bool = False


HaystackBuilder = Callable[[str, int | None], str]


class DESiPipeline:
    def __init__(self, router: EpistemicRouter | None = None,
                 escalate_on: tuple[str, ...] = ESCALATE_BUCKETS,
                 max_attempts: int = 2,
                 answerer: Answerer = call_answerer):
        self.router = router or EpistemicRouter()
        self.escalate_on = escalate_on
        self.max_attempts = max_attempts
        # Injectable so the escalation loop is exercisable offline (tests pass a
        # deterministic fake); defaults to the live OpenRouter answerer.
        self.answerer = answerer

    def run(self, query: str, haystack_builder: HaystackBuilder,
            cost_budget_usd: float = float("inf"),
            accuracy_target: float = 0.5,
            latency_budget_ms: int = 60_000,
            ledger=None,
            scorer: Scorer | None = None) -> PipelineResult:
        # 1. Classify
        classifier = self.router._get_classifier()
        cls = classifier.classify(query)
        result = PipelineResult(query=query, task_class=cls.task_class,
                                classifier_confidence=cls.confidence)
        result.total_cost_usd += cls.cost_usd
        result.total_latency_ms += cls.latency_ms

        if cls.task_class == "other":
            result.refused = True
            result.escalation_reason = (
                f"Classified as 'other' ({cls.confidence}). No route available."
            )
            return result

        # 2. Initial route
        from desi_router.router import RouteRequest
        avoid_models: list[str] = []
        for attempt_idx in range(self.max_attempts):
            req = RouteRequest(
                task_class=cls.task_class,
                cost_budget_usd=cost_budget_usd,
                accuracy_target=accuracy_target,
                latency_budget_ms=latency_budget_ms,
                avoid_models=list(avoid_models),
            )
            decision = self.router.route(req)
            if decision.model.startswith("("):
                # no candidate fits
                result.refused = True
                result.escalation_reason = decision.reason
                break

            # 3. Build context for this decision
            context_block = haystack_builder(decision.retrieval_strategy, decision.k)

            # 4. Call answerer
            ans = self.answerer(decision.model, context_block, query)
            result.attempts.append(Attempt(decision=decision, answer=ans))
            result.total_cost_usd += ans.cost_usd
            result.total_latency_ms += ans.latency_ms
            result.final_answer = ans

            # 4b. Record this attempt to the shared ledger (local Layer 9), so
            #     escalation behaviour becomes queryable evidence, not just a
            #     one-off calibration. The score is attached only when the
            #     caller has a correctness signal (eval-time); None in production.
            if ledger is not None:
                score = scorer(ans) if scorer is not None else None
                ledger.record(
                    "pipeline_attempt",
                    {
                        "query": query,
                        "task_class": cls.task_class,
                        "attempt_idx": attempt_idx,
                        "model": decision.model,
                        "confidence": ans.confidence,
                        "escalate_bucket": ans.confidence in self.escalate_on,
                        "answer": ans.text,
                        "error": ans.error,
                        "cost_usd": ans.cost_usd,
                        "score": score,
                    },
                )

            # 5. Escalation gate — now task-aware (v0.6)
            #
            # The decision to escalate is no longer "always on low confidence".
            # The routing_table.json escalation_rules section encodes per-task
            # whether escalation has positive expected value. For code_audit
            # and scientific_claim, the confidence heuristic mis-signals on the
            # current defaults, and naive escalation makes things worse.
            if ans.error:
                result.escalation_reason = f"Answerer error: {ans.error}"
                avoid_models.append(decision.model)
                continue
            esc_rules = self.router.table.get("escalation_rules", {}).get(cls.task_class, {})
            should_escalate = (
                ans.confidence in self.escalate_on
                and attempt_idx < self.max_attempts - 1
                and esc_rules.get("escalate_on_low_conf", False)
            )
            if should_escalate:
                result.escalated = True
                tgt = esc_rules.get("escalation_target_model", "(score-led)")
                result.escalation_reason = (
                    f"Confidence={ans.confidence} on {decision.model}; "
                    f"task={cls.task_class} has positive escalation EV "
                    f"(+{esc_rules.get('expected_gain', '?')}); escalating to {tgt}."
                )
                avoid_models.append(decision.model)
                # If table specifies an explicit escalation target, prefer it
                if "escalation_target_model" in esc_rules:
                    # Push the previous model into avoid so it's not picked again,
                    # but also bias toward the named target by raising accuracy.
                    accuracy_target = max(accuracy_target, decision.expected_score + 0.05)
                else:
                    accuracy_target = max(accuracy_target, decision.expected_score + 0.01)
                continue
            # confidence is acceptable OR escalation has non-positive EV for this task
            break

        return result


def escalation_evidence(ledger) -> dict:
    """Re-derive confidence calibration from logged pipeline attempts.

    Reads ``pipeline_attempt`` events out of the shared ledger and, per task,
    computes the same discrimination the one-off calibration does — but from
    accumulated production/eval evidence:

      * ``trigger_rate``       — share of attempts in the escalate buckets
      * ``p_correct_keep``     — realized P(correct | kept), scored attempts only
      * ``p_correct_escalate`` — realized P(correct | escalated)
      * ``separation``         — keep − escalate; the signal the escalation gate
        relies on. ``None`` until enough *scored* attempts exist.

    Attempts logged without a score (production, no gold) still count toward the
    trigger rate but not the accuracy split — so the loop tightens as eval-time
    scored runs accumulate. This is the read side of "the ledger is the
    calibration source"; the rules in routing_table.json can be re-fitted from it.
    """
    per_task_scores: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    per_task_counts: dict[str, dict[str, int]] = defaultdict(
        lambda: {"escalate": 0, "keep": 0}
    )
    for event in ledger.all(kind="pipeline_attempt"):
        p = event["payload"]
        task = p.get("task_class", "unknown")
        group = "escalate" if p.get("escalate_bucket") else "keep"
        per_task_counts[task][group] += 1
        score = p.get("score")
        if score is not None:
            per_task_scores[task][group].append(float(score))

    out: dict[str, dict] = {}
    for task, counts in sorted(per_task_counts.items()):
        keep, esc = per_task_scores[task]["keep"], per_task_scores[task]["escalate"]
        n_esc, n_keep = counts["escalate"], counts["keep"]
        n_total = n_esc + n_keep
        p_keep = (sum(keep) / len(keep)) if keep else None
        p_esc = (sum(esc) / len(esc)) if esc else None
        sep = (p_keep - p_esc) if (p_keep is not None and p_esc is not None) else None
        out[task] = {
            "n_total": n_total,
            "n_scored": len(keep) + len(esc),
            "trigger_rate": round(n_esc / n_total, 4) if n_total else 0.0,
            "p_correct_keep": round(p_keep, 4) if p_keep is not None else None,
            "p_correct_escalate": round(p_esc, 4) if p_esc is not None else None,
            "separation": round(sep, 4) if sep is not None else None,
        }
    return out


if __name__ == "__main__":
    # Smoke test: classify only (no haystack-builder available here)
    p = DESiPipeline()
    print("DESi Pipeline v0.6 (task-aware confidence escalation) loaded.")
    print("Use p.run(query, haystack_builder) for end-to-end.")
