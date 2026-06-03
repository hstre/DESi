"""DESi end-to-end pipeline: classify -> route -> answer -> (escalate).

This is v0.3 — adds confidence-based escalation. If the routed model returns
[CONFIDENCE: low], the pipeline retries with the next Pareto point.
Each attempt is logged for audit.

Usage:
    from desi.pipeline import DESiPipeline

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

from dataclasses import dataclass, field
from typing import Callable

from desi.router import EpistemicRouter, Decision
from desi.answerer import Answer, answer as call_answerer


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
                 escalate_on: tuple[str, ...] = ("low", "unknown"),
                 max_attempts: int = 2):
        self.router = router or EpistemicRouter()
        self.escalate_on = escalate_on
        self.max_attempts = max_attempts

    def run(self, query: str, haystack_builder: HaystackBuilder,
            cost_budget_usd: float = float("inf"),
            accuracy_target: float = 0.5,
            latency_budget_ms: int = 60_000) -> PipelineResult:
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
        from desi.router import RouteRequest
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
            ans = call_answerer(decision.model, context_block, query)
            result.attempts.append(Attempt(decision=decision, answer=ans))
            result.total_cost_usd += ans.cost_usd
            result.total_latency_ms += ans.latency_ms
            result.final_answer = ans

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


if __name__ == "__main__":
    # Smoke test: classify only (no haystack-builder available here)
    p = DESiPipeline()
    print("DESi Pipeline v0.6 (task-aware confidence escalation) loaded.")
    print("Use p.run(query, haystack_builder) for end-to-end.")
