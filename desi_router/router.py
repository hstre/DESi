"""DESi epistemic router — empirically grounded dispatch.

Given a task class + budget/accuracy constraints, return (model, k, strategy).
The routing table is grounded in the minimaltest series (LongMemEval-S, SciFact,
planted-bug code review). See routing_table.json for sources and caveats.

Usage:
    from desi_router.router import EpistemicRouter, RouteRequest

    router = EpistemicRouter()
    decision = router.route(RouteRequest(
        task_class="memory_recall",
        cost_budget_usd=0.0005,
        accuracy_target=0.50,
        latency_budget_ms=5000,
    ))
    # decision is a Decision with model, k, retrieval_strategy, expected_score, ...

For AUTONOMOUS routing (router classifies the input itself):
    router.route_from_query("How long did I wait for my visa?")
    # -> Decision; classification step adds ~$0.0001 and ~0.7s

This is a v0.2 router — picks from the measured Pareto-front and now includes
optional task-classification. It does NOT yet:
  - read self-confidence signals (logprobs / verdict uncertainty)
  - escalate dynamically after a low-confidence first answer
  - generalize to unseen task classes
Those are TODOs explicitly listed in routing_table.json#open_questions.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

_TABLE_PATH = Path(__file__).resolve().parent / "routing_table.json"


TaskClass = Literal["memory_recall", "code_audit", "scientific_claim"]
RetrievalStrategy = Literal["embedding_top_k", "raw_full", "none"]


@dataclass
class RouteRequest:
    task_class: TaskClass
    cost_budget_usd: float = float("inf")
    accuracy_target: float = 0.0
    latency_budget_ms: int = 1_000_000
    avoid_models: list[str] = field(default_factory=list)


@dataclass
class Decision:
    task_class: str
    model: str
    k: int | None
    retrieval_strategy: RetrievalStrategy
    expected_score: float
    expected_cost_usd: float
    expected_latency_ms: int | None
    reason: str
    fallbacks: list[str] = field(default_factory=list)


class EpistemicRouter:
    def __init__(self, table_path: Path = _TABLE_PATH, classifier=None):
        self.table = json.loads(table_path.read_text())
        self._classifier = classifier  # lazy-init on first route_from_query

    def _get_classifier(self):
        if self._classifier is None:
            from desi_router.classifier import TaskClassifier
            self._classifier = TaskClassifier()
        return self._classifier

    def route_from_query(self, query: str, context_hint: str | None = None,
                         cost_budget_usd: float = float("inf"),
                         accuracy_target: float = 0.0,
                         latency_budget_ms: int = 1_000_000,
                         avoid_models: list[str] | None = None) -> Decision:
        """Autonomous routing: classifies the query, then dispatches.

        Returns a Decision whose .reason includes the classification
        confidence and the classifier model used (so callers can audit).
        """
        c = self._get_classifier()
        cls = c.classify(query, context_hint=context_hint)
        if cls.task_class == "other":
            return Decision(
                task_class="other",
                model="(no route — task class outside empirical table)",
                k=None,
                retrieval_strategy="none",
                expected_score=0.0,
                expected_cost_usd=cls.cost_usd,
                expected_latency_ms=cls.latency_ms,
                reason=f"Task classified as 'other' ({cls.confidence} confidence). "
                       f"Untested classes: {self.table.get('untested_tasks', [])}. "
                       f"Recommend manual route or fallback to granite-4.1-8b.",
            )
        req = RouteRequest(
            task_class=cls.task_class,
            cost_budget_usd=cost_budget_usd,
            accuracy_target=accuracy_target,
            latency_budget_ms=latency_budget_ms,
            avoid_models=avoid_models or [],
        )
        d = self.route(req)
        d.reason = (f"[classified as {cls.task_class}, {cls.confidence} confidence, "
                    f"+${cls.cost_usd:.6f} +{cls.latency_ms}ms] " + d.reason)
        d.expected_cost_usd += cls.cost_usd
        if d.expected_latency_ms is not None:
            d.expected_latency_ms += cls.latency_ms
        return d

    def _cells(self, task_class: str) -> list[dict]:
        return self.table["tasks"][task_class]["cells"]

    def _retrieval_strategy(self, task_class: str) -> RetrievalStrategy:
        return self.table["tasks"][task_class].get("winning_strategy", "none")

    def route(self, req: RouteRequest) -> Decision:
        if req.task_class not in self.table["tasks"]:
            raise ValueError(f"Unknown task class: {req.task_class}. "
                             f"Known: {list(self.table['tasks'])}. "
                             "Untested fallback: route conservative to granite-4.1-8b.")

        candidates = [
            c for c in self._cells(req.task_class)
            if c["model"] not in req.avoid_models
        ]

        # Honor explicit avoid-list from the table (e.g. Qwen on code_audit)
        rules = self.table.get("router_rules", {}).get(req.task_class, {})
        explicit_avoid = rules.get("avoid", [])
        candidates = [c for c in candidates if c["model"] not in explicit_avoid]

        # Filter by hard constraints
        candidates = [
            c for c in candidates
            if c["cost_per_item_usd"] <= req.cost_budget_usd
            and c["score"] >= req.accuracy_target
            and (c.get("mean_latency_ms") is None
                 or c["mean_latency_ms"] <= req.latency_budget_ms)
        ]

        if not candidates:
            return Decision(
                task_class=req.task_class,
                model="(no candidate fits constraints)",
                k=None,
                retrieval_strategy="none",
                expected_score=0.0,
                expected_cost_usd=0.0,
                expected_latency_ms=None,
                reason="No model meets the (cost, accuracy, latency) constraints. "
                       "Relax budgets or accuracy_target.",
            )

        # Selection strategy:
        # 1. If a hand-curated 'default' rule exists for this task and the requested
        #    model is among candidates, honor it (table authors knew best).
        # 2. If cost_budget is tight (caller explicitly limited it), pick Pareto-cheapest.
        # 3. Otherwise: Score-led Pareto — prefer highest score, break ties by cost.
        default_rule = rules.get("default", {})
        default_model = default_rule.get("model")
        if default_model and any(c["model"] == default_model for c in candidates):
            # Score-driven path: explicit default beats lone cost optimization.
            cost_tight = req.cost_budget_usd < float("inf")
            if not cost_tight:
                best = next(c for c in candidates if c["model"] == default_model)
                best["_reason_hint"] = (f"Hand-curated default for {req.task_class}: "
                                       f"{default_rule.get('reason', '(no reason)')}")
            else:
                # Cost is constrained — fall back to Pareto-cheapest.
                best = min(candidates, key=lambda c: (c["cost_per_item_usd"], -c["score"]))
        else:
            # No applicable default — use score-led Pareto (max score, ties by cost).
            best = min(candidates, key=lambda c: (-c["score"], c["cost_per_item_usd"]))

        # Fallbacks = next 2 cheapest above accuracy_target
        sorted_alts = sorted(
            [c for c in candidates if c["model"] != best["model"]],
            key=lambda c: (c["cost_per_item_usd"], -c["score"]),
        )
        fallback_models = [c["model"] for c in sorted_alts[:2]]

        reason = (best.get("_reason_hint") or best.get("note") or
                  f"Score-led pick at score >= {req.accuracy_target:.2f} "
                  f"within cost budget ${req.cost_budget_usd:.5f}")
        return Decision(
            task_class=req.task_class,
            model=best["model"],
            k=best.get("k"),
            retrieval_strategy=self._retrieval_strategy(req.task_class),
            expected_score=best["score"],
            expected_cost_usd=best["cost_per_item_usd"],
            expected_latency_ms=best.get("mean_latency_ms"),
            reason=reason,
            fallbacks=fallback_models,
        )

    def provisional_models(self) -> dict:
        """Return the provisional_models block from the routing table.

        Provisional models have known pricing and tier but no measured task
        scores. The router REFUSES to route to them by default — they must be
        calibrated via the standard k-curve + cross-task sweep first.

        Returns the full block so callers can inspect tiers, pricing, and the
        calibration plan documented in routing_table.json.
        """
        return self.table.get("provisional_models", {})

    def pareto_front(self, task_class: str) -> list[Decision]:
        """Return the Pareto front (score, cost) for a task class — useful for
        plotting and debugging."""
        cells = self._cells(task_class)
        rules = self.table.get("router_rules", {}).get(task_class, {})
        avoid = set(rules.get("avoid", []))
        cells = [c for c in cells if c["model"] not in avoid]
        sorted_by_cost = sorted(cells, key=lambda c: c["cost_per_item_usd"])
        front = []
        best_score = -1
        strategy = self._retrieval_strategy(task_class)
        for c in sorted_by_cost:
            if c["score"] > best_score:
                best_score = c["score"]
                front.append(Decision(
                    task_class=task_class,
                    model=c["model"],
                    k=c.get("k"),
                    retrieval_strategy=strategy,
                    expected_score=c["score"],
                    expected_cost_usd=c["cost_per_item_usd"],
                    expected_latency_ms=c.get("mean_latency_ms"),
                    reason=f"Pareto point — cheapest at score {c['score']:.3f}",
                ))
        return front


def demo():
    """Show the router in action across all three task classes."""
    r = EpistemicRouter()

    print("=" * 78)
    print("DESi Epistemic Router — empirically grounded dispatch")
    print("=" * 78)
    print()

    scenarios = [
        ("Memory recall, no budget limit, want score >= 0.5",
         RouteRequest(task_class="memory_recall", accuracy_target=0.5)),
        ("Memory recall, ultra cheap (<$0.0005), score >= 0.5",
         RouteRequest(task_class="memory_recall", cost_budget_usd=0.0005,
                      accuracy_target=0.5)),
        ("Memory recall, want max accuracy (>= 0.59)",
         RouteRequest(task_class="memory_recall", accuracy_target=0.59)),
        ("Code audit, default",
         RouteRequest(task_class="code_audit", accuracy_target=0.5)),
        ("Code audit, cost-critical (<$0.00005)",
         RouteRequest(task_class="code_audit", cost_budget_usd=0.00005,
                      accuracy_target=0.5)),
        ("Scientific claim, want >= 0.85",
         RouteRequest(task_class="scientific_claim", accuracy_target=0.85)),
        ("Scientific claim, cost-critical",
         RouteRequest(task_class="scientific_claim", cost_budget_usd=0.00005,
                      accuracy_target=0.5)),
    ]

    for scenario, req in scenarios:
        print(f"-- {scenario}")
        d = r.route(req)
        print(f"   -> {d.model}")
        kstr = f"k={d.k}" if d.k is not None else "k=n/a (raw)"
        print(f"      {kstr}, strategy={d.retrieval_strategy}")
        print(f"      expected score={d.expected_score:.3f}, cost=${d.expected_cost_usd:.5f}")
        print(f"      reason: {d.reason}")
        if d.fallbacks:
            print(f"      fallbacks: {', '.join(d.fallbacks)}")
        print()

    print("=" * 78)
    print("Pareto fronts per task class (cheapest first):")
    print("=" * 78)
    for tc in ("memory_recall", "code_audit", "scientific_claim"):
        print(f"\n  [{tc}]")
        for d in r.pareto_front(tc):
            print(f"    score={d.expected_score:.3f}  ${d.expected_cost_usd:.5f}  "
                  f"{d.model.split('/')[-1]}"
                  + (f" @k={d.k}" if d.k is not None else ""))


if __name__ == "__main__":
    demo()
